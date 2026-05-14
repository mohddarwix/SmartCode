from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_diagnostic_complete
from ..llm import recommender
from ..models import Problem, ProblemSkill, ProblemStatus, Recommendation, Skill, User, UserSkill
from ..schemas import NextProblemSuggestion

router = APIRouter(prefix="/me", tags=["recommendations"])


@router.get("/recommendations/next", response_model=list[NextProblemSuggestion])
def next_recommendations(
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> list[NextProblemSuggestion]:
    """
    Return up to 3 unconsumed recommendations for the user. If no unconsumed
    rows exist, generate a fresh batch from the LLM (heuristic fallback) and
    persist them.
    """
    # 1) Already have a stored recommendation batch? Use the 3 most recent.
    rec_rows = db.scalars(
        select(Recommendation)
        .where(Recommendation.user_id == user.user_id, Recommendation.is_consumed.is_(False))
        .order_by(Recommendation.created_at.desc(), Recommendation.recommendation_id.desc())
        .limit(3)
    ).all()
    if rec_rows:
        out: list[NextProblemSuggestion] = []
        seen_pids: set[int] = set()
        for r in rec_rows:
            if r.problem_id in seen_pids:
                continue
            problem = db.get(Problem, r.problem_id)
            if not problem or not problem.is_active:
                continue
            seen_pids.add(r.problem_id)
            out.append(NextProblemSuggestion(
                problem_id=problem.problem_id,
                title=problem.title,
                difficulty=problem.difficulty,
                reason_md=r.reason_md,
                estimated_minutes=problem.estimated_minutes,
            ))
        if out:
            return out

    # 2) No stored recs — generate a fresh batch (3 picks) via the LLM.
    catalogue = _build_catalogue(db, user.user_id)
    skill_scores = _user_skill_scores(db, user.user_id)
    rec_set = recommender.recommend_problem(skills=skill_scores, catalogue=catalogue)
    if rec_set is None:
        return []

    suggestions: list[NextProblemSuggestion] = []
    for pick in rec_set.picks:
        problem = db.get(Problem, pick.problem_id)
        if problem is None:
            continue
        db.add(
            Recommendation(
                user_id=user.user_id,
                problem_id=problem.problem_id,
                reason_md=pick.reason_md,
                algo_version=f"{rec_set.source}-v2-3picks",
            )
        )
        suggestions.append(NextProblemSuggestion(
            problem_id=problem.problem_id,
            title=problem.title,
            difficulty=problem.difficulty,
            reason_md=pick.reason_md,
            estimated_minutes=problem.estimated_minutes,
        ))
    db.commit()
    return suggestions


def _build_catalogue(db: Session, user_id: int) -> list[recommender.CatalogueProblem]:
    solved_ids = set(
        db.scalars(
            select(ProblemStatus.problem_id).where(
                ProblemStatus.user_id == user_id, ProblemStatus.status == "solved"
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

    return [
        recommender.CatalogueProblem(
            problem_id=p.problem_id,
            title=p.title,
            difficulty=p.difficulty,
            skills=skills_by_problem.get(p.problem_id, []),
            is_solved=p.problem_id in solved_ids,
        )
        for p in problems
    ]


def _user_skill_scores(db: Session, user_id: int) -> list[recommender.SkillScore]:
    rows = db.execute(
        select(Skill.name, UserSkill.score)
        .join(UserSkill, (UserSkill.skill_id == Skill.skill_id) & (UserSkill.user_id == user_id), isouter=True)
        .order_by(Skill.display_order)
    ).all()
    return [recommender.SkillScore(name=name, score=score or 0) for name, score in rows]
