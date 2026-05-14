"""
Submissions router.

Evaluation goes through the LLM (`app.llm.submission_evaluator`), which reasons
about the user's code against the problem statement + visible test cases.
A strict heuristic fallback runs when the LLM is unavailable - the fallback
does NOT fake a high score; it returns an honest "couldn't grade" result so
the user knows the AI is offline.
"""

from datetime import date, datetime, timedelta, timezone

# Spaced repetition (FR-User 11.3): problems solved more than this many days ago
# become eligible to be recommended again as refreshers. Below the threshold
# they are filtered out so the student isn't asked to re-solve recent work.
SPACED_REPETITION_COOLDOWN_DAYS = 14

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from .. import audit
from ..database import get_db
from ..deps import get_current_user, require_diagnostic_complete
from ..llm import recommender, submission_evaluator
from ..models import (
    Feedback,
    HintRequest,
    Metric,
    Problem,
    ProblemStatus,
    ProblemSkill,
    Recommendation,
    Skill,
    Submission,
    TestCase,
    User,
    UserSkill,
    UserSkillHistory,
)
# Mirror of problems.HINT_COST_BY_INDEX / HINT_TOTAL_CAP. Kept in sync deliberately —
# the live tally shown in the editor must match what's deducted at Submit time.
_HINT_COST_BY_INDEX: tuple[int, ...] = (3, 5, 8, 8, 8)
_HINT_TOTAL_CAP = 25


def _hint_cost_for(index_1based: int) -> int:
    return _HINT_COST_BY_INDEX[min(index_1based, len(_HINT_COST_BY_INDEX)) - 1]


def _compute_hint_penalty(db: Session, user_id: int, problem_id: int) -> tuple[int, int]:
    """Return (hint_count, hint_penalty_points) for this user+problem."""
    count = db.scalar(
        select(func.count())
        .select_from(HintRequest)
        .where(HintRequest.user_id == user_id, HintRequest.problem_id == problem_id)
    ) or 0
    raw_cost = sum(_hint_cost_for(i + 1) for i in range(count))
    return count, min(_HINT_TOTAL_CAP, raw_cost)
from ..schemas import (
    FeedbackBullet,
    MetricsOut,
    NextProblemSuggestion,
    RunRequest,
    RunResult,
    ScoreAdjustment,
    SkillDelta,
    SubmissionCreate,
    SubmissionDetail,
    TestCaseResultOut,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


# --------------------------- evaluation -------------------------------------

def _build_eval_input(
    db: Session,
    problem: Problem,
    code: str,
    language: str,
    *,
    include_hidden: bool,
) -> submission_evaluator.EvaluationInput:
    """Pull test cases from the DB and shape them for the evaluator."""
    visibility_filter = ["sample", "public"]
    if include_hidden:
        visibility_filter.append("hidden")

    rows = db.scalars(
        select(TestCase)
        .where(
            TestCase.problem_id == problem.problem_id,
            TestCase.visibility.in_(visibility_filter),
        )
        .order_by(TestCase.test_case_id)
    ).all()

    snapshots = [
        submission_evaluator.TestCaseSnapshot(
            case_index=i + 1,
            name=tc.name,
            visibility=tc.visibility,
            input_blob=tc.input_blob,
            expected_blob=tc.expected_blob,
        )
        for i, tc in enumerate(rows)
    ]

    return submission_evaluator.EvaluationInput(
        problem_slug=problem.slug,
        problem_title=problem.title,
        difficulty=problem.difficulty,
        statement_md=problem.statement_md,
        constraints_md=problem.constraints_md,
        cases=snapshots,
        language=language,
        code=code,
    )


def _evaluate_submission(
    db: Session, problem: Problem, code: str, language: str
) -> submission_evaluator.EvaluationResult:
    """Full evaluation (visible + hidden cases) - used by Submit."""
    eval_input = _build_eval_input(db, problem, code, language, include_hidden=True)
    return submission_evaluator.evaluate_submission(eval_input)


def _run_submission(
    db: Session, problem: Problem, code: str, language: str
) -> submission_evaluator.EvaluationResult:
    """Quick evaluation (visible cases only) - used by Run."""
    eval_input = _build_eval_input(db, problem, code, language, include_hidden=False)
    return submission_evaluator.run_submission(eval_input)


# --------------------------- failed-attempts penalty ---------------------

# Points deducted from the raw LLM score per severity point accumulated across
# the user's prior FAILED attempts on this problem. Each failed test case in a
# prior attempt contributes severity (minor=1, moderate=2, severe=3), times a
# per-kind weight (run is exploratory, submit is committed).
_PENALTY_MULTIPLIER = 2
_KIND_WEIGHT: dict[str, float] = {"run": 0.5, "submit": 1.0}
# Floor so a finally-correct solution never drops below 50 — passing matters.
_MIN_SCORE_AFTER_PENALTY = 50


def _compute_failed_attempts_penalty(
    db: Session, user_id: int, problem_id: int
) -> dict:
    """
    Sum (severity * kind_weight) across the user's previous FAILED attempts on
    this problem. Returns a dict so callers can synthesize a clear explanation:

      {
        "points": float,             # sum of weighted severity (pre-multiplier)
        "prior_failed_attempts": int,
        "prior_failed_runs": int,
        "prior_failed_submits": int,
        "severity_counts": {"minor": int, "moderate": int, "severe": int},
      }
    """
    prior = db.scalars(
        select(Submission)
        .where(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
            Submission.status != "accepted",
        )
        .order_by(Submission.submission_id)
    ).all()

    points = 0.0
    severity_counts = {"minor": 0, "moderate": 0, "severe": 0}
    prior_runs = 0
    prior_submits = 0
    for sub in prior:
        weight = _KIND_WEIGHT.get(sub.kind, 1.0)
        if sub.kind == "run":
            prior_runs += 1
        else:
            prior_submits += 1
        rows = sub.case_results_json or []
        if not isinstance(rows, list):
            continue
        for entry in rows:
            if not isinstance(entry, dict) or entry.get("passed"):
                continue
            sev = entry.get("severity") or "moderate"
            if sev not in severity_counts:
                sev = "moderate"
            severity_counts[sev] += 1
            points += submission_evaluator.SEVERITY_POINTS[sev] * weight

    return {
        "points": points,
        "prior_failed_attempts": len(prior),
        "prior_failed_runs": prior_runs,
        "prior_failed_submits": prior_submits,
        "severity_counts": severity_counts,
    }


def _apply_penalty(raw_score: int, penalty_points: float) -> int:
    """Subtract scaled penalty from raw score, clamped to [_MIN, 100]."""
    adjusted = round(raw_score - _PENALTY_MULTIPLIER * penalty_points)
    return max(_MIN_SCORE_AFTER_PENALTY, min(100, adjusted))


def _build_penalty_bullet(
    raw_score: int, final_score: int, breakdown: dict
) -> FeedbackBullet | None:
    """Synthesize a feedback bullet explaining the score deduction."""
    deducted = raw_score - final_score
    hint_count = breakdown.get("hint_count", 0)
    hint_penalty = breakdown.get("hint_penalty", 0)
    if deducted <= 0 or (breakdown["prior_failed_attempts"] == 0 and hint_count == 0):
        return None

    parts: list[str] = []
    if breakdown["prior_failed_submits"] > 0:
        parts.append(
            f"{breakdown['prior_failed_submits']} failed "
            f"{'submit' if breakdown['prior_failed_submits'] == 1 else 'submits'}"
        )
    if breakdown["prior_failed_runs"] > 0:
        parts.append(
            f"{breakdown['prior_failed_runs']} failed "
            f"{'run' if breakdown['prior_failed_runs'] == 1 else 'runs'} (each weighted 0.5x)"
        )
    if hint_count > 0:
        parts.append(
            f"{hint_count} hint{'s' if hint_count != 1 else ''} requested (-{hint_penalty} pts)"
        )

    sev = breakdown["severity_counts"]
    sev_parts = [f"{n} {label}" for label, n in (
        ("severe", sev["severe"]), ("moderate", sev["moderate"]), ("minor", sev["minor"])
    ) if n > 0]
    sev_tail = (
        f" ({', '.join(sev_parts)} failed cases). Severe failures cost the most; "
        "runs cost half of submits."
        if sev_parts
        else ". Each hint costs more than the previous one (3, 5, 8, ... pts)."
    )
    return FeedbackBullet(
        kind="warn",
        text=(
            f"Final score reduced by {deducted} points "
            f"(raw {raw_score} -> {final_score}) due to "
            f"{' and '.join(parts)} on this problem"
            f"{sev_tail}"
        ),
    )


# --------------------------- skill update + status --------------------------

# Easier problems contribute less to skill growth — a beginner solving Two Sum
# shouldn't jump skills the same way a mid-track student solving Word Ladder does.
_DIFFICULTY_FACTOR: dict[str, float] = {"easy": 0.5, "medium": 1.0, "hard": 1.5}
# Hard cap on a single-submission bump, by difficulty. Steady journey, not a sprint.
_MAX_BUMP_BY_DIFFICULTY: dict[str, int] = {"easy": 1, "medium": 2, "hard": 3}

# Which LLM-graded axis drives each tagged skill's per-submission target.
_SKILL_METRIC_MAP: dict[str, str] = {
    "Algorithms":       "score_correctness",
    "Data Structures":  "score_correctness",
    "Edge Cases":       "score_edge_cases",
    "Code Quality":     "score_code_quality",
    "Time Complexity":  "score_time_complexity",
}


def _apply_skill_updates(
    db: Session,
    user_id: int,
    problem: Problem,
    evaluation: "submission_evaluator.EvaluationResult",
    final_score: int,
) -> list[SkillDelta]:
    """
    Update ONLY the skills the problem targets (problem_skills).

    Two Sum -> Algorithms + Data Structures bump. No other skill moves on
    that submission. The journey balance comes from problem variety: as
    different problems target different skills, all six grow over time.

    Bump formula:
        raw_delta = (target - before) * weight * difficulty_factor
                    * 0.08 * (final_score / 100)

      - `target` is the most-relevant LLM-graded axis for the skill
        (Edge Cases listens to score_edge_cases, etc.).
      - `weight` is problem_skills.weight (1.0 / 0.8 / 0.6 depending on
        how central the skill is to this problem).
      - `difficulty_factor` is 0.5 / 1.0 / 1.5 for easy / medium / hard.
      - `final_score / 100` is the EFFICIENCY MULTIPLIER. A user who
        scored 100/100 (clean first try) earns the full bump; a user
        whose final_score is 50/100 (lots of prior failed attempts, or
        weak submission) earns half. So passing on the 6th try is worth
        meaningfully less than passing first try.

    Caps: easy +1, medium +2, hard +3 per submission.
    Floor: 0 — bad submissions never decrease skills.
    """
    weight_rows = db.execute(
        select(ProblemSkill.skill_id, ProblemSkill.weight, Skill.name)
        .join(Skill, Skill.skill_id == ProblemSkill.skill_id)
        .where(ProblemSkill.problem_id == problem.problem_id)
        .order_by(Skill.display_order)
    ).all()

    metric_values = {
        "score_correctness":     evaluation.score_correctness,
        "score_edge_cases":      evaluation.score_edge_cases,
        "score_code_quality":    evaluation.score_code_quality,
        "score_time_complexity": evaluation.score_time_complexity,
    }
    difficulty_factor = _DIFFICULTY_FACTOR.get(problem.difficulty, 1.0)
    max_bump = _MAX_BUMP_BY_DIFFICULTY.get(problem.difficulty, 2)
    efficiency = max(0.0, min(1.0, final_score / 100.0))

    today = date.today()
    deltas: list[SkillDelta] = []
    for skill_id, weight, name in weight_rows:
        us = db.scalar(
            select(UserSkill).where(
                UserSkill.user_id == user_id, UserSkill.skill_id == skill_id
            )
        )
        before = us.score if us else 0

        metric_key = _SKILL_METRIC_MAP.get(name, "score_correctness")
        target = metric_values.get(metric_key, 0)

        raw_delta = (target - before) * float(weight) * difficulty_factor * 0.08 * efficiency
        # Floor at 0 — never lose skill points from a bad submission.
        bump = max(0, min(max_bump, round(raw_delta)))
        new_score = max(0, min(100, before + bump))

        if us is None:
            db.add(UserSkill(user_id=user_id, skill_id=skill_id, score=new_score))
        else:
            us.score = new_score

        # Daily snapshot for changed skills only. UNIQUE(user_id, skill_id, day)
        # means multiple submissions same day overwrite with the latest score.
        hist = db.scalar(
            select(UserSkillHistory).where(
                UserSkillHistory.user_id == user_id,
                UserSkillHistory.skill_id == skill_id,
                UserSkillHistory.day == today,
            )
        )
        if hist is None:
            db.add(UserSkillHistory(
                user_id=user_id, skill_id=skill_id, day=today, score=new_score,
            ))
        else:
            hist.score = new_score

        deltas.append(SkillDelta(skill=name, before=before, after=new_score))
    return deltas


def _upsert_problem_status(db: Session, user_id: int, problem_id: int, accepted: bool, score: int) -> None:
    ps = db.scalar(
        select(ProblemStatus).where(ProblemStatus.user_id == user_id, ProblemStatus.problem_id == problem_id)
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if ps is None:
        ps = ProblemStatus(user_id=user_id, problem_id=problem_id)
        db.add(ps)
    ps.attempts_count = (ps.attempts_count or 0) + 1
    ps.last_attempted_at = now
    ps.best_score = max(ps.best_score or 0, score)
    if accepted:
        ps.status = "solved"
        if ps.solved_at is None:
            ps.solved_at = now
    elif ps.status != "solved":
        ps.status = "attempted"


# --------------------------- recommendation -------------------------------

def _make_recommendation(db: Session, user_id: int) -> list[Recommendation]:
    """
    Ask the LLM (with heuristic fallback) for the user's next 3 problems,
    tailored to their CURRENT skill profile, and persist them.

    Called AFTER `_apply_skill_updates` so the freshly-updated skill scores
    are what the recommender sees — the next problems reflect the latest
    state of the journey, not the state before the submission.
    """
    db.flush()  # ensure prior writes (skill updates, problem_status) are visible

    # Fresh skill snapshot (after this submission's bump)
    skill_rows = db.execute(
        select(Skill.name, UserSkill.score)
        .outerjoin(
            UserSkill,
            (UserSkill.skill_id == Skill.skill_id) & (UserSkill.user_id == user_id),
        )
        .order_by(Skill.display_order)
    ).all()
    skills_payload = [
        recommender.SkillScore(name=name, score=int(score) if score is not None else 0)
        for name, score in skill_rows
    ]

    # Catalogue with the latest solved flag. Problems solved within the
    # spaced-repetition cooldown are treated as is_solved=True (filtered out
    # by the recommender). Older solves become eligible again -- the system
    # may occasionally re-suggest them as refreshers.
    cooldown_threshold = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        - timedelta(days=SPACED_REPETITION_COOLDOWN_DAYS)
    )
    solved_ids = {
        pid
        for (pid,) in db.execute(
            select(ProblemStatus.problem_id).where(
                ProblemStatus.user_id == user_id,
                ProblemStatus.status == "solved",
                ProblemStatus.solved_at >= cooldown_threshold,
            )
        ).all()
    }
    problem_rows = db.scalars(
        select(Problem).where(Problem.is_active.is_(True)).order_by(Problem.problem_id)
    ).all()
    skills_by_pid: dict[int, list[str]] = {}
    for pid, name in db.execute(
        select(ProblemSkill.problem_id, Skill.name)
        .join(Skill, Skill.skill_id == ProblemSkill.skill_id)
        .order_by(Skill.display_order)
    ).all():
        skills_by_pid.setdefault(pid, []).append(name)

    catalogue = [
        recommender.CatalogueProblem(
            problem_id=p.problem_id,
            title=p.title,
            difficulty=p.difficulty,
            skills=skills_by_pid.get(p.problem_id, []),
            is_solved=p.problem_id in solved_ids,
        )
        for p in problem_rows
    ]

    rec_set = recommender.recommend_problem(skills=skills_payload, catalogue=catalogue)
    if rec_set is None:
        return []

    rows: list[Recommendation] = []
    for p in rec_set.picks:
        row = Recommendation(
            user_id=user_id,
            problem_id=p.problem_id,
            reason_md=p.reason_md,
            algo_version=f"llm-recommender-{rec_set.source}-3picks",
        )
        db.add(row)
        rows.append(row)
    return rows


# --------------------------- endpoints ------------------------------------

@router.post("", response_model=SubmissionDetail, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    request: Request,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    problem = db.get(Problem, payload.problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # Once a student has solved a problem, the only thing they can do with it is
    # review the existing submission. No re-attempts; no new hints; no new runs.
    if user.role != "admin":
        existing = db.scalar(
            select(ProblemStatus.status).where(
                ProblemStatus.user_id == user.user_id,
                ProblemStatus.problem_id == payload.problem_id,
            )
        )
        if existing == "solved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "You've already solved this problem. Open it in review mode to see "
                    "your accepted code, feedback, and hints."
                ),
            )

    evaluation = _evaluate_submission(db, problem, payload.code, payload.language)

    raw_score = evaluation.score
    breakdown = _compute_failed_attempts_penalty(db, user.user_id, payload.problem_id)
    hint_count, hint_penalty = _compute_hint_penalty(db, user.user_id, payload.problem_id)
    breakdown["hint_count"] = hint_count
    breakdown["hint_penalty"] = hint_penalty
    # Total deduction = scaled failed-attempt severity + flat hint points.
    # Floor at 50 for accepted; floor at 50 for wrong_answer too (legacy behavior).
    raw_deduction = _PENALTY_MULTIPLIER * breakdown["points"] + hint_penalty
    final_score = max(_MIN_SCORE_AFTER_PENALTY, min(100, round(raw_score - raw_deduction)))
    adjustment = ScoreAdjustment(
        raw_score=raw_score,
        penalty_points=round(breakdown["points"]) + hint_penalty,
        prior_failed_attempts=breakdown["prior_failed_attempts"],
        final_score=final_score,
    )

    cases_payload = [c.model_dump() for c in evaluation.cases]
    submission = Submission(
        user_id=user.user_id,
        problem_id=payload.problem_id,
        language=payload.language,
        kind="submit",
        code=payload.code,
        status=evaluation.status,
        score=final_score,
        total_runtime_ms=evaluation.runtime_ms,
        total_memory_kb=evaluation.memory_kb,
        case_results_json=cases_payload,
    )
    db.add(submission)
    db.flush()

    db.add(
        Metric(
            submission_id=submission.submission_id,
            score_correctness=evaluation.score_correctness,
            score_edge_cases=evaluation.score_edge_cases,
            score_code_quality=evaluation.score_code_quality,
            score_time_complexity=evaluation.score_time_complexity,
            inferred_big_o=evaluation.inferred_big_o,
            passed_count=evaluation.passed_count,
            total_count=evaluation.total_count,
        )
    )

    accepted = evaluation.status == "accepted"
    bullets = [FeedbackBullet(kind=b.kind, text=b.text) for b in evaluation.bullets]
    penalty_bullet = _build_penalty_bullet(raw_score, final_score, breakdown)
    if penalty_bullet is not None:
        bullets.insert(0, penalty_bullet)
    db.add(
        Feedback(
            submission_id=submission.submission_id,
            source="llm" if evaluation.source == "llm" else "rule",
            summary_md=evaluation.summary_md,
            bullets_json=[b.model_dump() for b in bullets],
        )
    )

    deltas = _apply_skill_updates(db, user.user_id, problem, evaluation, final_score)
    _upsert_problem_status(db, user.user_id, payload.problem_id, accepted, final_score)

    next_recs = _make_recommendation(db, user.user_id) if accepted else []
    next_suggestions: list[NextProblemSuggestion] = []
    for rec in next_recs:
        next_p = db.get(Problem, rec.problem_id)
        if next_p:
            next_suggestions.append(NextProblemSuggestion(
                problem_id=next_p.problem_id,
                title=next_p.title,
                difficulty=next_p.difficulty,
                reason_md=rec.reason_md,
                estimated_minutes=next_p.estimated_minutes,
            ))

    # Audit log: record submit attempts. Useful for instructor review of
    # who attempted what + their final scores.
    audit.record(
        db,
        user_id=user.user_id,
        event_type=f"submission.{evaluation.status}",
        target_kind="problem",
        target_id=str(payload.problem_id),
        detail=f"score={final_score}, raw={raw_score}, cases={evaluation.passed_count}/{evaluation.total_count}",
        request=request,
    )

    db.commit()
    db.refresh(submission)

    return _build_submission_detail(
        db, submission, deltas, next_suggestions, bullets,
        grader_source=evaluation.source, score_adjustment=adjustment,
    )


@router.get("/{submission_id}", response_model=SubmissionDetail)
def get_submission(
    submission_id: int,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    submission = db.get(Submission, submission_id)
    if submission is None or (submission.user_id != user.user_id and user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return _build_submission_detail(db, submission, skills_updated=[], next_suggestions=[])


def _build_submission_detail(
    db: Session,
    submission: Submission,
    skills_updated: list[SkillDelta],
    next_suggestions: list[NextProblemSuggestion],
    bullets_override: list[FeedbackBullet] | None = None,
    grader_source: str | None = None,
    score_adjustment: ScoreAdjustment | None = None,
) -> SubmissionDetail:
    problem = db.get(Problem, submission.problem_id)
    metric = db.scalar(select(Metric).where(Metric.submission_id == submission.submission_id))
    feedback = db.scalar(
        select(Feedback).where(Feedback.submission_id == submission.submission_id).order_by(Feedback.created_at.desc())
    )

    bullets: list[FeedbackBullet] = bullets_override or []
    if not bullets and feedback and feedback.bullets_json:
        bullets = [FeedbackBullet(**b) for b in feedback.bullets_json]

    cases: list[TestCaseResultOut] = []
    if submission.case_results_json:
        for entry in submission.case_results_json:
            if not isinstance(entry, dict):
                continue
            try:
                cases.append(TestCaseResultOut(**entry))
            except Exception:  # noqa: BLE001
                continue

    return SubmissionDetail(
        submission_id=submission.submission_id,
        problem_id=submission.problem_id,
        problem_title=problem.title if problem else "(deleted)",
        language=submission.language,
        status=submission.status,
        score=submission.score,
        submitted_at=submission.submitted_at,
        total_runtime_ms=submission.total_runtime_ms,
        total_memory_kb=submission.total_memory_kb,
        metrics=MetricsOut(
            score_correctness=metric.score_correctness,
            score_edge_cases=metric.score_edge_cases,
            score_code_quality=metric.score_code_quality,
            score_time_complexity=metric.score_time_complexity,
            passed_count=metric.passed_count,
            total_count=metric.total_count,
            inferred_big_o=metric.inferred_big_o,
        ) if metric else None,
        feedback_summary_md=feedback.summary_md if feedback else None,
        feedback_bullets=bullets,
        cases=cases,
        skills_updated=skills_updated,
        next_problem=next_suggestions[0] if next_suggestions else None,
        next_problems=next_suggestions,
        grader_source=grader_source if grader_source in ("llm", "heuristic") else None,
        score_adjustment=score_adjustment,
    )
