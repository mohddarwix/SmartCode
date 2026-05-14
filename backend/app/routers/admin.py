from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import (
    AuditLog,
    Problem,
    ProblemSkill,
    ProblemStatus,
    Skill,
    Submission,
    TestCase,
    User,
    UserSkill,
)
from ..schemas import (
    AdminProblemRow,
    AdminProblemUpsert,
    AdminSkillRow,
    AdminSkillUpsert,
    AdminStats,
    AdminTestCaseRow,
    AdminTestCaseUpsert,
    AdminUserActivity,
    AdminUserCreate,
    AdminUserDetail,
    AdminUserRow,
    MySubmissionListItem,
    UserSkillOut,
)
from ..security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------------------------- Stats ----------------------------------------

@router.get("/stats", response_model=AdminStats)
def admin_stats(db: Session = Depends(get_db)) -> AdminStats:
    users = db.scalar(select(func.count()).select_from(User)) or 0
    students = db.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0
    problems = db.scalar(select(func.count()).select_from(Problem)) or 0
    skills = db.scalar(select(func.count()).select_from(Skill)) or 0
    submissions = db.scalar(select(func.count()).select_from(Submission)) or 0

    today = date.today()
    seven_days_ago = today - timedelta(days=6)
    rows = db.execute(
        select(func.date(Submission.submitted_at).label("d"), func.count().label("c"))
        .where(Submission.submitted_at >= seven_days_ago)
        .group_by("d")
    ).all()
    counts_by_day = {str(r.d): r.c for r in rows}
    series = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        series.append({"day": d.strftime("%a"), "count": counts_by_day.get(d.isoformat(), 0)})

    return AdminStats(
        users=users,
        students=students,
        problems=problems,
        skills=skills,
        submissions=submissions,
        submissions_last_7_days=series,
    )


# ---------------------------- Users ----------------------------------------

@router.get("/users", response_model=list[AdminUserRow])
def admin_users(db: Session = Depends(get_db)) -> list[AdminUserRow]:
    solved_sum = func.sum(case((ProblemStatus.status == "solved", 1), else_=0))
    avg_score = func.coalesce(
        func.round(func.avg(case((ProblemStatus.best_score > 0, ProblemStatus.best_score), else_=None))), 0
    )
    rows = db.execute(
        select(
            User.user_id,
            User.full_name,
            User.email,
            User.role,
            solved_sum.label("solved"),
            avg_score.label("avg_score"),
            User.last_login_at,
            User.created_at,
        )
        .join(ProblemStatus, ProblemStatus.user_id == User.user_id, isouter=True)
        .group_by(User.user_id, User.full_name, User.email, User.role, User.last_login_at, User.created_at)
        .order_by(User.role.desc(), User.user_id)
    ).all()
    return [
        AdminUserRow(
            user_id=r.user_id,
            full_name=r.full_name,
            email=r.email,
            role=r.role,
            solved=int(r.solved or 0),
            avg_score=int(r.avg_score or 0),
            last_login_at=r.last_login_at,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/users", response_model=AdminUserRow, status_code=status.HTTP_201_CREATED)
def admin_create_user(payload: AdminUserCreate, db: Session = Depends(get_db)) -> AdminUserRow:
    """
    Admin-only user creation. Use this in prod where public /register is
    disabled (ALLOW_REGISTRATION=false). Useful for onboarding graders /
    classmates without flipping the env var.
    """
    email = payload.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserRow(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        solved=0,
        avg_score=0,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


# ---------------------------- Problems CRUD --------------------------------

def _problem_to_row(db: Session, p: Problem) -> AdminProblemRow:
    rows = db.execute(
        select(Skill.skill_id, Skill.name)
        .join(ProblemSkill, ProblemSkill.skill_id == Skill.skill_id)
        .where(ProblemSkill.problem_id == p.problem_id)
        .order_by(Skill.display_order)
    ).all()
    return AdminProblemRow(
        problem_id=p.problem_id,
        slug=p.slug,
        title=p.title,
        difficulty=p.difficulty,
        source=p.source,
        estimated_minutes=p.estimated_minutes,
        statement_md=p.statement_md,
        constraints_md=p.constraints_md,
        starter_code_md=p.starter_code_md,
        is_active=p.is_active,
        skills=[r.name for r in rows],
        skill_ids=[r.skill_id for r in rows],
    )


@router.get("/problems", response_model=list[AdminProblemRow])
def admin_list_problems(db: Session = Depends(get_db)) -> list[AdminProblemRow]:
    problems = db.scalars(select(Problem).order_by(Problem.problem_id)).all()
    return [_problem_to_row(db, p) for p in problems]


@router.post("/problems", response_model=AdminProblemRow, status_code=status.HTTP_201_CREATED)
def admin_create_problem(payload: AdminProblemUpsert, db: Session = Depends(get_db)) -> AdminProblemRow:
    if db.scalar(select(Problem).where(Problem.slug == payload.slug)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A problem with this slug already exists.")
    p = Problem(
        slug=payload.slug,
        title=payload.title,
        difficulty=payload.difficulty,
        source=payload.source,
        estimated_minutes=payload.estimated_minutes,
        statement_md=payload.statement_md,
        constraints_md=payload.constraints_md,
        starter_code_md=payload.starter_code_md,
        is_active=payload.is_active,
    )
    db.add(p)
    db.flush()
    _replace_problem_skills(db, p.problem_id, payload.skill_ids)
    db.commit()
    db.refresh(p)
    return _problem_to_row(db, p)


@router.put("/problems/{problem_id}", response_model=AdminProblemRow)
def admin_update_problem(
    problem_id: int, payload: AdminProblemUpsert, db: Session = Depends(get_db)
) -> AdminProblemRow:
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # If slug changes, ensure it's unique
    if payload.slug != p.slug and db.scalar(select(Problem).where(Problem.slug == payload.slug)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A problem with this slug already exists.")

    p.slug = payload.slug
    p.title = payload.title
    p.difficulty = payload.difficulty
    p.source = payload.source
    p.estimated_minutes = payload.estimated_minutes
    p.statement_md = payload.statement_md
    p.constraints_md = payload.constraints_md
    p.starter_code_md = payload.starter_code_md
    p.is_active = payload.is_active

    _replace_problem_skills(db, p.problem_id, payload.skill_ids)
    db.commit()
    db.refresh(p)
    return _problem_to_row(db, p)


@router.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_problem(problem_id: int, db: Session = Depends(get_db)) -> None:
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    db.delete(p)
    db.commit()


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def admin_user_detail(user_id: int, db: Session = Depends(get_db)) -> AdminUserDetail:
    """
    Per-user drilldown (FR-Admin 5): roster summary + skill profile +
    recent submissions + audit timeline. Drives the "click a user" view.
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Roster row (with solved + avg_score)
    solved_sum = func.sum(case((ProblemStatus.status == "solved", 1), else_=0))
    avg_score = func.coalesce(
        func.round(func.avg(case((ProblemStatus.best_score > 0, ProblemStatus.best_score), else_=None))), 0
    )
    summary_row = db.execute(
        select(
            User.user_id, User.full_name, User.email, User.role,
            solved_sum.label("solved"),
            avg_score.label("avg_score"),
            User.last_login_at, User.created_at,
        )
        .join(ProblemStatus, ProblemStatus.user_id == User.user_id, isouter=True)
        .where(User.user_id == user_id)
        .group_by(User.user_id, User.full_name, User.email, User.role, User.last_login_at, User.created_at)
    ).first()
    user_row = AdminUserRow(
        user_id=summary_row.user_id,
        full_name=summary_row.full_name,
        email=summary_row.email,
        role=summary_row.role,
        solved=int(summary_row.solved or 0),
        avg_score=int(summary_row.avg_score or 0),
        last_login_at=summary_row.last_login_at,
        created_at=summary_row.created_at,
    )

    # Per-skill scores
    skill_rows = db.execute(
        select(Skill.skill_id, Skill.name, UserSkill.score)
        .join(UserSkill, (UserSkill.skill_id == Skill.skill_id) & (UserSkill.user_id == user_id), isouter=True)
        .order_by(Skill.display_order)
    ).all()
    skill_scores = [
        UserSkillOut(skill_id=sid, name=name, score=int(score or 0))
        for sid, name, score in skill_rows
    ]

    # Recent submissions (newest 20)
    sub_rows = db.scalars(
        select(Submission)
        .where(Submission.user_id == user_id, Submission.kind == "submit")
        .order_by(Submission.submission_id.desc())
        .limit(20)
    ).all()
    recent_submissions = [
        MySubmissionListItem(
            submission_id=s.submission_id,
            kind=s.kind,
            status=s.status,
            score=s.score,
            submitted_at=s.submitted_at,
            language=s.language,
            code=s.code,
            passed_count=None,
            total_count=None,
        )
        for s in sub_rows
    ]

    # Recent audit events (newest 40)
    audit_rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.audit_id.desc())
        .limit(40)
    ).all()
    audit_events = [
        AdminUserActivity(
            when=a.created_at,
            event_type=a.event_type,
            target_kind=a.target_kind,
            target_id=a.target_id,
            detail=a.detail,
            source_ip=a.source_ip,
        )
        for a in audit_rows
    ]

    return AdminUserDetail(
        user=user_row,
        skill_scores=skill_scores,
        recent_submissions=recent_submissions,
        audit_events=audit_events,
    )


def _test_case_to_row(tc: TestCase) -> AdminTestCaseRow:
    return AdminTestCaseRow(
        test_case_id=tc.test_case_id,
        problem_id=tc.problem_id,
        name=tc.name,
        visibility=tc.visibility,
        input_blob=tc.input_blob,
        expected_blob=tc.expected_blob,
    )


# ---------------------------- Test cases CRUD ------------------------------
# Closes FR-Admin 2: admins can add/edit/delete test cases through the UI
# instead of having to write raw SQL against the test_cases table.

@router.get("/problems/{problem_id}/test-cases", response_model=list[AdminTestCaseRow])
def admin_list_test_cases(problem_id: int, db: Session = Depends(get_db)) -> list[AdminTestCaseRow]:
    if db.get(Problem, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    rows = db.scalars(
        select(TestCase).where(TestCase.problem_id == problem_id).order_by(TestCase.test_case_id)
    ).all()
    return [_test_case_to_row(t) for t in rows]


@router.post(
    "/problems/{problem_id}/test-cases",
    response_model=AdminTestCaseRow,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_test_case(
    problem_id: int, payload: AdminTestCaseUpsert, db: Session = Depends(get_db)
) -> AdminTestCaseRow:
    if db.get(Problem, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    tc = TestCase(
        problem_id=problem_id,
        name=payload.name,
        visibility=payload.visibility,
        input_blob=payload.input_blob,
        expected_blob=payload.expected_blob,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return _test_case_to_row(tc)


@router.put("/test-cases/{test_case_id}", response_model=AdminTestCaseRow)
def admin_update_test_case(
    test_case_id: int, payload: AdminTestCaseUpsert, db: Session = Depends(get_db)
) -> AdminTestCaseRow:
    tc = db.get(TestCase, test_case_id)
    if tc is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    tc.name = payload.name
    tc.visibility = payload.visibility
    tc.input_blob = payload.input_blob
    tc.expected_blob = payload.expected_blob
    db.commit()
    db.refresh(tc)
    return _test_case_to_row(tc)


@router.delete("/test-cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_test_case(test_case_id: int, db: Session = Depends(get_db)) -> None:
    tc = db.get(TestCase, test_case_id)
    if tc is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    db.delete(tc)
    db.commit()


def _replace_problem_skills(db: Session, problem_id: int, skill_ids: list[int]) -> None:
    db.execute(ProblemSkill.__table__.delete().where(ProblemSkill.problem_id == problem_id))
    for sid in skill_ids:
        db.add(ProblemSkill(problem_id=problem_id, skill_id=sid))


# ---------------------------- Skills CRUD ----------------------------------

def _skill_to_row(db: Session, s: Skill) -> AdminSkillRow:
    count = db.scalar(
        select(func.count()).select_from(ProblemSkill).where(ProblemSkill.skill_id == s.skill_id)
    ) or 0
    return AdminSkillRow(
        skill_id=s.skill_id,
        name=s.name,
        description=s.description,
        display_order=s.display_order,
        problem_count=count,
    )


@router.get("/skills", response_model=list[AdminSkillRow])
def admin_list_skills(db: Session = Depends(get_db)) -> list[AdminSkillRow]:
    skills = db.scalars(select(Skill).order_by(Skill.display_order)).all()
    return [_skill_to_row(db, s) for s in skills]


@router.post("/skills", response_model=AdminSkillRow, status_code=status.HTTP_201_CREATED)
def admin_create_skill(payload: AdminSkillUpsert, db: Session = Depends(get_db)) -> AdminSkillRow:
    s = Skill(name=payload.name, description=payload.description, display_order=payload.display_order)
    db.add(s)
    db.commit()
    db.refresh(s)
    return _skill_to_row(db, s)


@router.put("/skills/{skill_id}", response_model=AdminSkillRow)
def admin_update_skill(skill_id: int, payload: AdminSkillUpsert, db: Session = Depends(get_db)) -> AdminSkillRow:
    s = db.get(Skill, skill_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    s.name = payload.name
    s.description = payload.description
    s.display_order = payload.display_order
    db.commit()
    db.refresh(s)
    return _skill_to_row(db, s)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_skill(skill_id: int, db: Session = Depends(get_db)) -> None:
    s = db.get(Skill, skill_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    db.delete(s)
    db.commit()
