"""
Diagnostic router.

POST /api/diagnostic
  Body: { items: [{order_index, skill_id, skill_name, type, question,
                   user_answer, correct_answer?, time_spent_seconds, hints_used}] }
  - Calls the LLM grader (Gemini), or falls back to a heuristic if no key/quota.
  - Persists diagnostic_attempt + per-item rows (with corrections).
  - Updates user_skill from the per-skill scores.
  - Sets users.diagnostic_completed_at.
  - Picks a follow-up problem tailored to the weakest skills.
  - Returns the full graded result for the review screen.

GET /api/diagnostic/last
  Returns the most recent completed diagnostic for the current user (for the
  review screen, or to re-display the corrections later).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..llm import diagnostic_grader, recommender
from ..models import (
    DiagnosticAttempt,
    DiagnosticItem,
    Problem,
    ProblemSkill,
    ProblemStatus,
    Recommendation,
    Skill,
    User,
    UserSkill,
)
from ..schemas import (
    DiagnosticItemResultOut,
    DiagnosticResultOut,
    DiagnosticSubmit,
    NextProblemSuggestion,
    UserOut,
    UserSkillOut,
)

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


# --------------------------- POST /api/diagnostic ---------------------------

@router.post("", response_model=DiagnosticResultOut, status_code=status.HTTP_201_CREATED)
def submit_diagnostic(
    payload: DiagnosticSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiagnosticResultOut:
    # 1) Build the grader inputs (resolve skill_id <-> skill_name)
    skill_by_id = {s.skill_id: s for s in db.scalars(select(Skill)).all()}
    skill_by_name = {s.name: s for s in skill_by_id.values()}

    def resolve_skill_name(item) -> str:
        if item.skill_name:
            return item.skill_name
        if item.skill_id and item.skill_id in skill_by_id:
            return skill_by_id[item.skill_id].name
        return "General"

    def normalize_tested_skills(item) -> list[str]:
        # Prefer explicit tested_skills; fall back to [primary skill]; drop unknown names.
        primary = resolve_skill_name(item)
        names = list(item.tested_skills) if item.tested_skills else [primary]
        seen, out = set(), []
        for n in names:
            if n in skill_by_name and n not in seen:
                seen.add(n)
                out.append(n)
        return out or [primary]

    grader_inputs = [
        diagnostic_grader.DiagnosticItemInput(
            order_index=it.order_index,
            skill=resolve_skill_name(it),
            tested_skills=normalize_tested_skills(it),
            type=it.type,
            question=it.question,
            user_answer=it.user_answer or "",
            correct_answer=it.correct_answer,
        )
        for it in payload.items
    ]

    # 2) Grade (LLM or heuristic, transparent to caller)
    graded = diagnostic_grader.grade_diagnostic(grader_inputs)

    # 3) Persist attempt + items
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    attempt = DiagnosticAttempt(
        user_id=user.user_id,
        started_at=now,
        finished_at=now,
        status="completed",
        overall_score=graded.overall_score,
        summary_md=graded.summary_md,
        grader_source=graded.source,
    )
    db.add(attempt)
    db.flush()  # need attempt id

    item_by_index = {it.order_index: it for it in payload.items}
    result_by_index = {r.order_index: r for r in graded.items}

    for inp in payload.items:
        result = result_by_index.get(inp.order_index)
        if result is None:
            continue
        # Resolve skill_id from skill_name if the frontend only sent the name.
        skill_id = inp.skill_id
        if skill_id is None and inp.skill_name and inp.skill_name in skill_by_name:
            skill_id = skill_by_name[inp.skill_name].skill_id
        db.add(
            DiagnosticItem(
                diagnostic_attempt_id=attempt.diagnostic_attempt_id,
                skill_id=skill_id,
                problem_id=inp.problem_id,
                order_index=inp.order_index,
                question_md=inp.question,
                user_answer=inp.user_answer,
                correct_answer=result.correct_answer or inp.correct_answer,
                is_correct=result.is_correct,
                explanation_md=result.explanation_md,
                score=result.score,
                time_spent_seconds=inp.time_spent_seconds,
                hints_used=inp.hints_used,
            )
        )

    # 4) Update user_skill (overwrite with the graded scores)
    for skill_name, score in graded.skill_scores.items():
        skill = skill_by_name.get(skill_name)
        if skill is None:
            continue
        us = db.scalar(
            select(UserSkill).where(
                UserSkill.user_id == user.user_id, UserSkill.skill_id == skill.skill_id
            )
        )
        if us is None:
            db.add(UserSkill(user_id=user.user_id, skill_id=skill.skill_id, score=score))
        else:
            us.score = score

    # 5) Mark diagnostic as completed on the user
    user.diagnostic_completed_at = now

    # 6) Pick a follow-up problem targeting the weak skills
    db.flush()  # so user_skill changes are visible to the recommender query
    next_suggestions = _make_next_recommendation(db, user, graded.weak_skills)

    db.commit()
    db.refresh(user)
    db.refresh(attempt)

    return _build_result_out(db, user, attempt, graded.weak_skills, next_suggestions, graded=graded)


# --------------------------- GET /api/diagnostic/last -----------------------

@router.get("/last", response_model=DiagnosticResultOut)
def last_diagnostic(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiagnosticResultOut:
    attempt = db.scalar(
        select(DiagnosticAttempt)
        .where(
            DiagnosticAttempt.user_id == user.user_id,
            DiagnosticAttempt.status == "completed",
        )
        .order_by(DiagnosticAttempt.finished_at.desc().nullslast())
    )
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No completed diagnostic yet."
        )
    # Recompute weak skills from the persisted skill scores
    skill_scores = _user_skills(db, user.user_id)
    weak_skills = [
        s.name for s in sorted(skill_scores, key=lambda r: r.score)[:3]
    ]
    return _build_result_out(db, user, attempt, weak_skills, [])


# --------------------------- helpers ---------------------------------------

def _user_skills(db: Session, user_id: int) -> list[UserSkillOut]:
    rows = db.execute(
        select(Skill.skill_id, Skill.name, UserSkill.score)
        .join(UserSkill, (UserSkill.skill_id == Skill.skill_id) & (UserSkill.user_id == user_id), isouter=True)
        .order_by(Skill.display_order)
    ).all()
    return [UserSkillOut(skill_id=sid, name=name, score=score or 0) for sid, name, score in rows]


def _make_next_recommendation(
    db: Session, user: User, weak_skills: list[str]
) -> list[NextProblemSuggestion]:
    # Build the catalogue: active problems not yet solved by this user
    solved_ids = set(
        db.scalars(
            select(ProblemStatus.problem_id).where(
                ProblemStatus.user_id == user.user_id, ProblemStatus.status == "solved"
            )
        ).all()
    )
    problems = db.scalars(select(Problem).where(Problem.is_active.is_(True))).all()
    skills_by_problem: dict[int, list[str]] = {}
    rows = db.execute(
        select(ProblemSkill.problem_id, Skill.name)
        .join(Skill, Skill.skill_id == ProblemSkill.skill_id)
        .order_by(Skill.display_order)
    ).all()
    for pid, name in rows:
        skills_by_problem.setdefault(pid, []).append(name)

    catalogue = [
        recommender.CatalogueProblem(
            problem_id=p.problem_id,
            title=p.title,
            difficulty=p.difficulty,
            skills=skills_by_problem.get(p.problem_id, []),
            is_solved=p.problem_id in solved_ids,
        )
        for p in problems
    ]

    # Skill scores for the user (in the schema the recommender expects)
    skill_scores = [
        recommender.SkillScore(name=us.name, score=us.score)
        for us in _user_skills(db, user.user_id)
    ]

    # If we have explicit weak_skills from the grader, prepend them to the
    # ordering by zeroing them out (so the LLM/heuristic biases toward them).
    weak_set = set(weak_skills)
    if weak_set:
        skill_scores.sort(key=lambda s: (s.name not in weak_set, s.score))

    rec_set = recommender.recommend_problem(skills=skill_scores, catalogue=catalogue)
    if rec_set is None:
        return []

    # Persist all 3 picks so /api/me/recommendations/next returns them.
    out: list[NextProblemSuggestion] = []
    by_id = {p.problem_id: p for p in problems}
    for pick in rec_set.picks:
        problem = by_id.get(pick.problem_id)
        if problem is None:
            continue
        db.add(
            Recommendation(
                user_id=user.user_id,
                problem_id=pick.problem_id,
                reason_md=pick.reason_md,
                algo_version=f"{rec_set.source}-v2-3picks",
            )
        )
        out.append(NextProblemSuggestion(
            problem_id=problem.problem_id,
            title=problem.title,
            difficulty=problem.difficulty,
            reason_md=pick.reason_md,
            estimated_minutes=problem.estimated_minutes,
        ))
    return out


def _build_result_out(
    db: Session,
    user: User,
    attempt: DiagnosticAttempt,
    weak_skills: list[str],
    next_suggestions: list[NextProblemSuggestion],
    graded: diagnostic_grader.DiagnosticResult | None = None,
) -> DiagnosticResultOut:
    items = db.scalars(
        select(DiagnosticItem)
        .where(DiagnosticItem.diagnostic_attempt_id == attempt.diagnostic_attempt_id)
        .order_by(DiagnosticItem.order_index)
    ).all()
    skill_by_id = {s.skill_id: s for s in db.scalars(select(Skill)).all()}

    # The DB row doesn't store tested_skills / per_skill_scores / answer_kind.
    # When we have the in-memory `graded` result (post-submit), we read those
    # fields from it. For `/diagnostic/last` they fall back to defaults.
    graded_by_index = {r.order_index: r for r in (graded.items if graded else [])}

    def item_type(question_md: str | None) -> str:
        # We didn't persist the type column; infer cheaply from the question.
        if question_md and ("```" in question_md or "function" in question_md.lower() or "write" in question_md.lower()):
            return "coding"
        return "mcq"

    items_out: list[DiagnosticItemResultOut] = []
    for it in items:
        g = graded_by_index.get(it.order_index)
        items_out.append(DiagnosticItemResultOut(
            order_index=it.order_index,
            skill_name=skill_by_id[it.skill_id].name if it.skill_id in skill_by_id else None,
            tested_skills=list((g.per_skill_scores or {}).keys()) if g else [],
            per_skill_scores=dict(g.per_skill_scores) if g else {},
            type=item_type(it.question_md),
            question=it.question_md or "",
            user_answer=it.user_answer or "",
            correct_answer=it.correct_answer,
            is_correct=it.is_correct,
            score=it.score,
            explanation_md=it.explanation_md or "",
            answer_kind=g.answer_kind if g else "code",
        ))

    return DiagnosticResultOut(
        diagnostic_attempt_id=attempt.diagnostic_attempt_id,
        finished_at=attempt.finished_at,
        overall_score=attempt.overall_score or 0,
        summary_md=attempt.summary_md or "",
        grader_source=attempt.grader_source,
        items=items_out,
        skill_scores=_user_skills(db, user.user_id),
        weak_skills=weak_skills,
        next_problem=next_suggestions[0] if next_suggestions else None,
        next_problems=next_suggestions,
        user=UserOut.model_validate(user),
    )
