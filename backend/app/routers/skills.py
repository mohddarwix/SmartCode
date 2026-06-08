from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_diagnostic_complete
from ..models import Skill, User, UserSkill, UserSkillHistory
from ..schemas import SkillHistoryPoint, SkillOut, UserSkillOut

router = APIRouter(prefix="/me", tags=["skills"])


@router.get("/skills", response_model=list[UserSkillOut])
def my_skills(
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> list[UserSkillOut]:
    """Current user's score per skill, in display order. Includes skills with no row yet (score=0)."""
    rows = db.execute(
        select(Skill.skill_id, Skill.name, UserSkill.score)
        .join(
            UserSkill,
            (UserSkill.skill_id == Skill.skill_id)
            & (UserSkill.user_id == user.user_id),
            isouter=True,
        )
        .order_by(Skill.display_order)
    ).all()
    return [
        UserSkillOut(skill_id=sid, name=name, score=score or 0)
        for sid, name, score in rows
    ]


@router.get("/skills/history", response_model=list[SkillHistoryPoint])
def my_skill_history(
    skill_id: int = Query(..., ge=1),
    user: User = Depends(require_diagnostic_complete),
    db: Session = Depends(get_db),
) -> list[SkillHistoryPoint]:
    rows = db.execute(
        select(UserSkillHistory.day, UserSkillHistory.score)
        .where(
            UserSkillHistory.user_id == user.user_id,
            UserSkillHistory.skill_id == skill_id,
        )
        .order_by(UserSkillHistory.day)
    ).all()
    return [SkillHistoryPoint(day=d, score=s) for d, s in rows]


# Public skill catalogue (used by the admin Skills screen and by problem detail).
catalog_router = APIRouter(prefix="/skills", tags=["skills"])


@catalog_router.get("", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)) -> list[SkillOut]:
    skills = db.scalars(select(Skill).order_by(Skill.display_order)).all()
    return [SkillOut.model_validate(s) for s in skills]
