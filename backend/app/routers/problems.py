import json as _json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_diagnostic_complete
from ..llm import (
    hint_generator,
    interactive_tutor,
    solution_generator,
    submission_evaluator,
)
from ..models import (
    AiSolution,
    Feedback,
    HintRequest,
    HintTemplate,
    Metric,
    Problem,
    ProblemSkill,
    ProblemStatus,
    Recommendation,
    Skill,
    Submission,
    TestCase,
    User,
)
from ..schemas import (
    AiSolutionOut,
    FeedbackBullet,
    HintOut,
    HintRecord,
    HintRequestPayload,
    MetricsOut,
    MyAttemptOut,
    MySubmissionListItem,
    ProblemDetail,
    ProblemSummary,
    RunRequest,
    RunResult,
    SubmissionDetail,
    TestCaseOut,
    TestCaseResultOut,
    TutorTurnRequest,
    TutorTurnResponse,
)

router = APIRouter(prefix="/problems", tags=["problems"])


def _is_solved(db: Session, user_id: int, problem_id: int) -> bool:
    """True if the user has an accepted submission on this problem (problem_status='solved')."""
    s = db.scalar(
        select(ProblemStatus.status).where(
            ProblemStatus.user_id == user_id,
            ProblemStatus.problem_id == problem_id,
        )
    )
    return s == "solved"


def _block_if_solved(db: Session, user: User, problem_id: int) -> None:
    """Reject mutating actions on a problem the user has already solved."""
    if user.role != "admin" and _is_solved(db, user.user_id, problem_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "You've already solved this problem. Open your submission in review "
                "mode to see your code, feedback, and hints — re-attempts aren't allowed."
            ),
        )


def _skill_names_for_problem(db: Session, problem_id: int) -> list[str]:
    return [
        n
        for (n,) in db.execute(
            select(Skill.name)
            .join(ProblemSkill, ProblemSkill.skill_id == Skill.skill_id)
            .where(ProblemSkill.problem_id == problem_id)
            .order_by(Skill.display_order)
        ).all()
    ]


@router.get("", response_model=list[ProblemSummary])
def list_problems(
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> list[ProblemSummary]:
    """
    Problems visible to the current user.

    - Admins see the entire catalogue.
    - Students see only the problems they've already touched (attempted or
      solved) PLUS any problem that has been recommended to them at some
      point. The journey expands as the LLM recommends new problems after
      each accepted submission — students don't get a browseable catalog.
    """
    status_rows = db.execute(
        select(
            ProblemStatus.problem_id, ProblemStatus.status, ProblemStatus.best_score
        ).where(ProblemStatus.user_id == user.user_id)
    ).all()
    status_by_pid = {pid: (s, score) for pid, s, score in status_rows}

    base = select(Problem).where(Problem.is_active.is_(True))
    if user.role == "admin":
        problems = db.scalars(base.order_by(Problem.problem_id)).all()
    else:
        recommended_ids = {
            pid
            for (pid,) in db.execute(
                select(Recommendation.problem_id).where(
                    Recommendation.user_id == user.user_id
                )
            ).all()
        }
        touched_ids = set(status_by_pid.keys())
        visible_ids = recommended_ids | touched_ids
        if not visible_ids:
            return []
        problems = db.scalars(
            base.where(Problem.problem_id.in_(visible_ids)).order_by(Problem.problem_id)
        ).all()

    # Pre-fetch skills for all problems (one query)
    skills_rows = db.execute(
        select(ProblemSkill.problem_id, Skill.name)
        .join(Skill, Skill.skill_id == ProblemSkill.skill_id)
        .order_by(Skill.display_order)
    ).all()
    skills_by_pid: dict[int, list[str]] = {}
    for pid, name in skills_rows:
        skills_by_pid.setdefault(pid, []).append(name)

    out = []
    for p in problems:
        s, score = status_by_pid.get(p.problem_id, ("not_started", 0))
        out.append(
            ProblemSummary(
                problem_id=p.problem_id,
                slug=p.slug,
                title=p.title,
                difficulty=p.difficulty,
                source=p.source,
                estimated_minutes=p.estimated_minutes,
                skills=skills_by_pid.get(p.problem_id, []),
                is_active=p.is_active,
                user_status=s,
                best_score=score,
            )
        )
    return out


@router.get("/{problem_id}", response_model=ProblemDetail)
def problem_detail(
    problem_id: int,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> ProblemDetail:
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    # Students can only open problems that have been recommended OR they've
    # already attempted — same gate as the list endpoint, applied per-problem
    # so the route can't be bypassed by typing /problems/<id> directly.
    if user.role != "admin":
        touched = db.scalar(
            select(ProblemStatus.problem_id).where(
                ProblemStatus.user_id == user.user_id,
                ProblemStatus.problem_id == problem_id,
            )
        )
        recommended = db.scalar(
            select(Recommendation.problem_id).where(
                Recommendation.user_id == user.user_id,
                Recommendation.problem_id == problem_id,
            )
        )
        if touched is None and recommended is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem not found",
            )

    visible_cases = db.scalars(
        select(TestCase)
        .where(
            TestCase.problem_id == problem_id,
            TestCase.visibility.in_(["sample", "public"]),
        )
        .order_by(TestCase.test_case_id)
    ).all()
    hidden_count = (
        db.scalar(
            select(func.count())
            .select_from(TestCase)
            .where(TestCase.problem_id == problem_id, TestCase.visibility == "hidden")
        )
        or 0
    )

    return ProblemDetail(
        problem_id=problem.problem_id,
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        source=problem.source,
        estimated_minutes=problem.estimated_minutes,
        statement_md=problem.statement_md,
        constraints_md=problem.constraints_md,
        starter_code_md=problem.starter_code_md,
        cheatsheet_md=problem.cheatsheet_md,
        skills=_skill_names_for_problem(db, problem_id),
        test_cases=[
            TestCaseOut(
                name=tc.name,
                visibility=tc.visibility,
                input_blob=tc.input_blob,
                expected_blob=tc.expected_blob,
            )
            for tc in visible_cases
        ],
        has_hidden_tests=hidden_count > 0,
    )


# Escalating hint cost: each subsequent hint costs more, capped per problem.
# Mirrored by submissions.HINT_COST_BY_INDEX so the running tally matches what's
# actually deducted on Submit.
HINT_COST_BY_INDEX: tuple[int, ...] = (3, 5, 8, 8, 8)  # hint #1..#5 (and beyond)
HINT_TOTAL_CAP = 25  # max points a single problem's hints can ever deduct


def _hint_cost_for(index_1based: int) -> int:
    return HINT_COST_BY_INDEX[min(index_1based, len(HINT_COST_BY_INDEX)) - 1]


def _hint_running_totals(db: Session, user_id: int, problem_id: int) -> tuple[int, int]:
    """Return (count, cost_so_far) of prior hint_requests for this user+problem."""
    prior = db.scalars(
        select(HintRequest)
        .where(HintRequest.user_id == user_id, HintRequest.problem_id == problem_id)
        .order_by(HintRequest.created_at)
    ).all()
    cost = 0
    for i in range(len(prior)):
        cost += _hint_cost_for(i + 1)
    return len(prior), min(cost, HINT_TOTAL_CAP)


@router.get("/{problem_id}/hint/preview")
def hint_preview(
    problem_id: int,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> dict:
    """Cost of the NEXT hint without actually requesting one. Used by the confirm modal."""
    prior_count, prior_capped_cost = _hint_running_totals(db, user.user_id, problem_id)
    next_index = prior_count + 1
    raw_total_after = sum(_hint_cost_for(i + 1) for i in range(next_index))
    new_capped_cost = min(HINT_TOTAL_CAP, raw_total_after)
    return {
        "next_hint_index": next_index,
        "next_cost_points": max(0, new_capped_cost - prior_capped_cost),
        "total_hints_used": prior_count,
        "total_cost_so_far": prior_capped_cost,
        "cap_reached": prior_capped_cost >= HINT_TOTAL_CAP,
        "total_cap": HINT_TOTAL_CAP,
    }


@router.post("/{problem_id}/hint", response_model=HintOut)
def problem_hint(
    problem_id: int,
    payload: HintRequestPayload,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> HintOut:
    """
    Generate a DYNAMIC hint tailored to the student's current code, log it
    in hint_requests, and return the running cost tally. The cost is applied
    to the user's final score on the next Submit (see submissions.create_submission).
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )
    _block_if_solved(db, user, problem_id)

    visible_cases = db.scalars(
        select(TestCase)
        .where(
            TestCase.problem_id == problem_id,
            TestCase.visibility.in_(["sample", "public"]),
        )
        .order_by(TestCase.test_case_id)
    ).all()
    sample_cases = [
        {"name": c.name, "input_blob": c.input_blob, "expected_blob": c.expected_blob}
        for c in visible_cases[:2]
    ]

    hint = hint_generator.generate_hint(
        hint_generator.HintInput(
            problem_title=problem.title,
            difficulty=problem.difficulty,
            statement_md=problem.statement_md,
            constraints_md=problem.constraints_md,
            sample_cases=sample_cases,
            user_code=payload.code,
            level=payload.level,
        )
    )

    # Price this hint (escalating + capped). Compute marginal cost so the per-hint
    # cost reflects what's actually deductible after the cap kicks in.
    prior_count, prior_capped_cost = _hint_running_totals(db, user.user_id, problem_id)
    this_index = prior_count + 1
    raw_total_after = sum(_hint_cost_for(i + 1) for i in range(this_index))
    new_capped_cost = min(HINT_TOTAL_CAP, raw_total_after)
    marginal_cost = max(0, new_capped_cost - prior_capped_cost)

    db.add(
        HintRequest(
            user_id=user.user_id,
            problem_id=problem_id,
            hint_level_requested=hint.hint_level,
            source="llm" if hint.source == "llm" else "template",
            hint_text_md=hint.hint_text_md,
        )
    )
    db.commit()

    return HintOut(
        hint_level=hint.hint_level,
        hint_text_md=hint.hint_text_md,
        source=hint.source,
        cost_points=marginal_cost,
        total_hints_used=this_index,
        total_cost_points=new_capped_cost,
    )


@router.post("/{problem_id}/run", response_model=RunResult)
def run_plain(
    problem_id: int,
    payload: RunRequest,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> RunResult:
    """
    PLAIN run -- the "normal compiler" button. Executes user code in the
    Python sandbox against visible test cases ONLY. No LLM is called.
    Result is pure pass/fail + actual output per case. Fast (~100-300 ms).

    NOT persisted, NOT penalized -- it's a free smoke test, like LeetCode's
    "Run Code" before "Submit".
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )
    _block_if_solved(db, user, problem_id)

    visible_cases = db.scalars(
        select(TestCase)
        .where(
            TestCase.problem_id == problem_id,
            TestCase.visibility.in_(["sample", "public"]),
        )
        .order_by(TestCase.test_case_id)
    ).all()
    if not visible_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No visible test cases."
        )

    # Execute every case through the sandbox. The sandbox is what the LLM path
    # already uses for ground-truth pass/fail, so plain run and AI run agree
    # on correctness -- the difference is just whether LLM commentary runs.
    from ..sandbox import PROBLEM_CONFIGS, run_all_cases

    if problem.slug not in PROBLEM_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This problem has no sandbox config yet -- use 'Run with AI' instead.",
        )

    cases_payload = [
        {
            "case_index": i + 1,
            "input_blob": tc.input_blob,
            "expected_blob": tc.expected_blob,
        }
        for i, tc in enumerate(visible_cases)
    ]
    sandbox_results = run_all_cases(
        slug=problem.slug, user_code=payload.code, cases=cases_payload
    )
    by_index = {r.case_index: r for r in sandbox_results}

    cases_out: list[TestCaseResultOut] = []
    any_runtime_error = False
    for i, tc in enumerate(visible_cases, start=1):
        sb = by_index.get(i)
        if sb is None:
            continue
        if sb.error and (
            "Error" in sb.error or "Exception" in sb.error or "Timed out" in sb.error
        ):
            any_runtime_error = True
        predicted = sb.actual_output or (sb.error or "(no output)")
        cases_out.append(
            TestCaseResultOut(
                case_index=i,
                name=tc.name,
                visibility=tc.visibility,
                input_blob=tc.input_blob,
                expected_blob=tc.expected_blob,
                predicted_output=predicted,
                passed=sb.passed,
                explanation_md=(
                    f"Got `{predicted}`, expected `{sb.expected_output}`."
                    if not sb.passed
                    else ""
                ),
                severity=None,
            )
        )

    passed = sum(1 for c in cases_out if c.passed)
    total = len(cases_out)
    all_passed = passed == total and total > 0
    if all_passed:
        status_str = "accepted"
    elif any_runtime_error:
        status_str = "runtime_error"
    else:
        status_str = "wrong_answer"

    return RunResult(
        cases=cases_out,
        passed_count=passed,
        total_count=total,
        all_passed=all_passed,
        status=status_str,
        source="sandbox",
    )


@router.post("/{problem_id}/run-ai", response_model=RunResult)
def run_with_ai(
    problem_id: int,
    payload: RunRequest,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> RunResult:
    """
    AI run -- sandbox + LLM commentary (severity, per-case explanations,
    code-quality scoring). Slower (~3-5 s), persists failed attempts as
    Submission(kind='run') so their severity points contribute to future
    Submit penalties. Passing runs are not persisted.
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )
    _block_if_solved(db, user, problem_id)

    visible_cases = db.scalars(
        select(TestCase)
        .where(
            TestCase.problem_id == problem_id,
            TestCase.visibility.in_(["sample", "public"]),
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
        for i, tc in enumerate(visible_cases)
    ]
    if not snapshots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No visible test cases for this problem.",
        )

    eval_input = submission_evaluator.EvaluationInput(
        problem_slug=problem.slug,
        problem_title=problem.title,
        difficulty=problem.difficulty,
        statement_md=problem.statement_md,
        constraints_md=problem.constraints_md,
        cases=snapshots,
        language=payload.language,
        code=payload.code,
    )
    result = submission_evaluator.run_submission(eval_input)

    all_passed = result.passed_count == result.total_count
    if not all_passed:
        # Persist failed runs only — their severity points accumulate against
        # the next Submit. Passing runs are not stored (no penalty contribution
        # and the user hasn't yet committed via Submit).
        cases_payload = [c.model_dump() for c in result.cases]
        db.add(
            Submission(
                user_id=user.user_id,
                problem_id=problem_id,
                language=payload.language,
                kind="run",
                code=payload.code,
                status=result.status,
                score=result.score,
                total_runtime_ms=result.runtime_ms,
                total_memory_kb=result.memory_kb,
                case_results_json=cases_payload,
            )
        )
        db.commit()

    cases_out = [
        TestCaseResultOut(
            case_index=c.case_index,
            name=c.name,
            visibility=c.visibility,
            input_blob=c.input_blob,
            expected_blob=c.expected_blob,
            predicted_output=c.predicted_output,
            passed=c.passed,
            explanation_md=c.explanation_md,
            severity=c.severity,
        )
        for c in result.cases
    ]
    return RunResult(
        cases=cases_out,
        passed_count=result.passed_count,
        total_count=result.total_count,
        all_passed=all_passed,
        status=result.status,
        source=result.source,
    )


@router.get("/{problem_id}/my-submissions", response_model=list[MySubmissionListItem])
def my_submissions(
    problem_id: int,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> list[MySubmissionListItem]:
    """
    All Submit attempts (kind='submit') for this user+problem, newest first.
    Drives the editor's 'Submissions' tab.

    Failed Run attempts are intentionally omitted from this view — they exist
    only so failed-attempt severity points feed the score penalty.
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    rows = db.scalars(
        select(Submission)
        .where(
            Submission.user_id == user.user_id,
            Submission.problem_id == problem_id,
            Submission.kind == "submit",
        )
        .order_by(Submission.submission_id.desc())
    ).all()

    # Per-submission metrics for the passed/total badge.
    metric_rows = (
        db.execute(
            select(Metric.submission_id, Metric.passed_count, Metric.total_count).where(
                Metric.submission_id.in_([s.submission_id for s in rows])
            )
        ).all()
        if rows
        else []
    )
    metrics_by_sid = {sid: (p, t) for sid, p, t in metric_rows}

    out: list[MySubmissionListItem] = []
    for s in rows:
        p_t = metrics_by_sid.get(s.submission_id, (None, None))
        out.append(
            MySubmissionListItem(
                submission_id=s.submission_id,
                kind=s.kind,
                status=s.status,
                score=s.score,
                submitted_at=s.submitted_at,
                language=s.language,
                code=s.code,
                passed_count=p_t[0],
                total_count=p_t[1],
            )
        )
    return out


@router.get("/{problem_id}/my-attempt", response_model=MyAttemptOut)
def my_attempt(
    problem_id: int,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> MyAttemptOut:
    """
    Read-only review payload for a problem the user has solved: their accepted
    submission (with code + feedback + cases) plus the full hint history.
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    accepted = db.scalar(
        select(Submission)
        .where(
            Submission.user_id == user.user_id,
            Submission.problem_id == problem_id,
            Submission.kind == "submit",
            Submission.status == "accepted",
        )
        .order_by(Submission.submission_id.desc())
    )
    if accepted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't solved this problem yet.",
        )

    metric = db.scalar(
        select(Metric).where(Metric.submission_id == accepted.submission_id)
    )
    feedback = db.scalar(
        select(Feedback)
        .where(Feedback.submission_id == accepted.submission_id)
        .order_by(Feedback.created_at.desc())
    )

    cases_out: list[TestCaseResultOut] = []
    for entry in accepted.case_results_json or []:
        if isinstance(entry, dict):
            try:
                cases_out.append(TestCaseResultOut(**entry))
            except Exception:  # noqa: BLE001
                continue

    submission_detail = SubmissionDetail(
        submission_id=accepted.submission_id,
        problem_id=accepted.problem_id,
        problem_title=problem.title,
        language=accepted.language,
        status=accepted.status,
        score=accepted.score,
        submitted_at=accepted.submitted_at,
        total_runtime_ms=accepted.total_runtime_ms,
        total_memory_kb=accepted.total_memory_kb,
        metrics=(
            MetricsOut(
                score_correctness=metric.score_correctness,
                score_edge_cases=metric.score_edge_cases,
                score_code_quality=metric.score_code_quality,
                score_time_complexity=metric.score_time_complexity,
                passed_count=metric.passed_count,
                total_count=metric.total_count,
                inferred_big_o=metric.inferred_big_o,
            )
            if metric
            else None
        ),
        feedback_summary_md=feedback.summary_md if feedback else None,
        feedback_bullets=(
            [
                FeedbackBullet(**b)
                for b in (feedback.bullets_json or [])
                if isinstance(b, dict)
            ]
            if feedback
            else []
        ),
        cases=cases_out,
        skills_updated=[],
        next_problem=None,
        grader_source=None,
        code=accepted.code,
    )

    hints = db.scalars(
        select(HintRequest)
        .where(
            HintRequest.user_id == user.user_id, HintRequest.problem_id == problem_id
        )
        .order_by(HintRequest.created_at)
    ).all()
    hint_records = [
        HintRecord(
            hint_level=h.hint_level_requested,
            hint_text_md=h.hint_text_md,
            source=h.source,
            created_at=h.created_at,
        )
        for h in hints
    ]
    # Match the escalating cost schedule from this router so the review screen
    # tells the student exactly how many points the hints cost them.
    hint_total_cost = min(
        HINT_TOTAL_CAP,
        sum(_hint_cost_for(i + 1) for i in range(len(hint_records))),
    )

    return MyAttemptOut(
        submission=submission_detail,
        hints=hint_records,
        hint_total_cost=hint_total_cost,
    )


@router.post("/{problem_id}/ai-solve/stream")
def ai_solve_stream(
    problem_id: int,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Stream the LLM solving the problem LIVE, chunk by chunk, as Server-Sent
    Events. The student watches the AI think through the problem in real time.

    Same gate as /ai-solution: only allowed once the student has solved.

    Wire format (SSE):
      data: {"text": "...chunk..."}\\n\\n
      ...
      data: [DONE]\\n\\n
    or on error:
      data: {"error": "..."}\\n\\n
      data: [DONE]\\n\\n
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    # The live AI walkthrough is always accessible — no solved-gate. Students
    # can watch the tutor solve a problem at any time, including before they
    # attempt it themselves.

    visible_cases = db.scalars(
        select(TestCase)
        .where(
            TestCase.problem_id == problem_id,
            TestCase.visibility.in_(["sample", "public"]),
        )
        .order_by(TestCase.test_case_id)
    ).all()
    sample_cases = [
        {"name": c.name, "input_blob": c.input_blob, "expected_blob": c.expected_blob}
        for c in visible_cases[:3]
    ]

    inp = solution_generator.SolutionInput(
        problem_title=problem.title,
        difficulty=problem.difficulty,
        statement_md=problem.statement_md,
        constraints_md=problem.constraints_md,
        sample_cases=sample_cases,
        starter_code_md=problem.starter_code_md,
    )

    def event_stream():
        try:
            for chunk in solution_generator.stream_live_solve(inp):
                yield f"data: {_json.dumps({'text': chunk})}\n\n"
        except Exception as exc:  # noqa: BLE001
            yield f"data: {_json.dumps({'error': str(exc)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx)
            "Connection": "keep-alive",
        },
    )


@router.post("/{problem_id}/ai-tutor/turn", response_model=TutorTurnResponse)
def ai_tutor_turn(
    problem_id: int,
    payload: TutorTurnRequest,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> TutorTurnResponse:
    """
    Interactive step-by-step tutor turn.

    The frontend keeps the conversation history and replays it on every call.
    The LLM produces the next tutor message (explanation + check question)
    and decides whether to advance step_index. When the conversation reaches
    step 6 the LLM sets is_complete=true and the frontend stops sending turns.
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    # Pick the first sample case so the tutor can reference it during the trace step.
    sample = db.scalar(
        select(TestCase)
        .where(TestCase.problem_id == problem_id, TestCase.visibility == "sample")
        .order_by(TestCase.test_case_id)
    )

    history = [
        interactive_tutor.TutorMessage(
            role=m.role, content=m.content, step_index=m.step_index
        )
        for m in payload.history
    ]
    inp = interactive_tutor.TutorInput(
        problem_title=problem.title,
        difficulty=problem.difficulty,
        statement_md=problem.statement_md,
        constraints_md=problem.constraints_md,
        sample_input=sample.input_blob if sample else None,
        sample_output=sample.expected_blob if sample else None,
        history=history,
        student_message=payload.student_message,
    )
    turn = interactive_tutor.teach(inp)
    return TutorTurnResponse(
        tutor_response=turn.tutor_response,
        step_index=turn.step_index,
        total_steps=turn.total_steps,
        is_complete=turn.is_complete,
        source=turn.source,
    )


@router.get("/{problem_id}/ai-solution", response_model=AiSolutionOut)
def ai_solution(
    problem_id: int,
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> AiSolutionOut:
    """
    Canonical AI solution + explanation for a problem. Always accessible —
    students can view it any time, including before attempting. If no seeded
    `ai_solution` row exists, generate one on-demand via the LLM and cache it.
    """
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    sol = db.scalar(
        select(AiSolution)
        .where(AiSolution.problem_id == problem_id)
        .order_by(AiSolution.created_at.desc())
    )
    if sol is None:
        # Generate on-demand, then cache so we only pay once per problem.
        visible_cases = db.scalars(
            select(TestCase)
            .where(
                TestCase.problem_id == problem_id,
                TestCase.visibility.in_(["sample", "public"]),
            )
            .order_by(TestCase.test_case_id)
        ).all()
        sample_cases = [
            {
                "name": c.name,
                "input_blob": c.input_blob,
                "expected_blob": c.expected_blob,
            }
            for c in visible_cases[:3]
        ]
        generated = solution_generator.generate_solution(
            solution_generator.SolutionInput(
                problem_title=problem.title,
                difficulty=problem.difficulty,
                statement_md=problem.statement_md,
                constraints_md=problem.constraints_md,
                sample_cases=sample_cases,
                starter_code_md=problem.starter_code_md,
            )
        )
        sol = AiSolution(
            problem_id=problem_id,
            explanation_md=generated.explanation_md,
            solution_code=generated.solution_code,
            time_complexity=generated.time_complexity,
            space_complexity=generated.space_complexity,
        )
        db.add(sol)
        db.commit()
        db.refresh(sol)

    return AiSolutionOut(
        explanation_md=sol.explanation_md,
        solution_code=sol.solution_code,
        time_complexity=sol.time_complexity,
        space_complexity=sol.space_complexity,
    )
