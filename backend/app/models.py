from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("student", "admin", name="user_role"),
        nullable=False,
        default="student",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    diagnostic_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Skill(Base):
    __tablename__ = "skills"

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Problem(Base):
    __tablename__ = "problems"

    problem_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    difficulty: Mapped[str] = mapped_column(
        Enum("easy", "medium", "hard", name="difficulty"),
        nullable=False,
    )
    source: Mapped[Optional[str]] = mapped_column(String(40))
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    statement_md: Mapped[str] = mapped_column(Text, nullable=False)
    constraints_md: Mapped[Optional[str]] = mapped_column(Text)
    starter_code_md: Mapped[Optional[str]] = mapped_column(Text)
    cheatsheet_md: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    skills: Mapped[List["ProblemSkill"]] = relationship(back_populates="problem", cascade="all, delete-orphan")
    test_cases: Mapped[List["TestCase"]] = relationship(back_populates="problem", cascade="all, delete-orphan")


class ProblemSkill(Base):
    __tablename__ = "problem_skills"

    problem_skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.0"))

    problem: Mapped["Problem"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship()


class TestCase(Base):
    __tablename__ = "test_cases"

    test_case_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    visibility: Mapped[str] = mapped_column(
        Enum("sample", "public", "hidden", name="visibility"),
        nullable=False,
        default="public",
    )
    weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.0"))
    input_blob: Mapped[str] = mapped_column(Text, nullable=False)
    expected_blob: Mapped[str] = mapped_column(Text, nullable=False)

    problem: Mapped["Problem"] = relationship(back_populates="test_cases")


class DiagnosticAttempt(Base):
    __tablename__ = "diagnostic_attempts"

    diagnostic_attempt_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        Enum("in_progress", "completed", "abandoned", name="diagnostic_status"),
        nullable=False,
        default="in_progress",
    )
    overall_score: Mapped[Optional[int]] = mapped_column(Integer)
    summary_md: Mapped[Optional[str]] = mapped_column(Text)
    grader_source: Mapped[str] = mapped_column(
        Enum("llm", "heuristic", name="grader_source"),
        nullable=False,
        default="heuristic",
    )


class DiagnosticItem(Base):
    __tablename__ = "diagnostic_items"

    diagnostic_item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    diagnostic_attempt_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_attempts.diagnostic_attempt_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("skills.skill_id", ondelete="SET NULL"))
    problem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("problems.problem_id", ondelete="SET NULL"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question_md: Mapped[Optional[str]] = mapped_column(Text)
    user_answer: Mapped[Optional[str]] = mapped_column(Text)
    correct_answer: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    explanation_md: Mapped[Optional[str]] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Submission(Base):
    __tablename__ = "submissions"

    submission_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="python")
    kind: Mapped[str] = mapped_column(
        Enum("run", "submit", name="submission_kind"),
        nullable=False,
        default="submit",
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "accepted", "wrong_answer", "runtime_error", "time_limit", "compile_error", name="submission_status"),
        nullable=False,
        default="pending",
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    total_runtime_ms: Mapped[Optional[int]] = mapped_column(Integer)
    total_memory_kb: Mapped[Optional[int]] = mapped_column(Integer)
    case_results_json: Mapped[Optional[list]] = mapped_column(JSON)


class Metric(Base):
    __tablename__ = "metrics"

    metrics_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.submission_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    score_correctness: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_edge_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_code_quality: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_time_complexity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cyclomatic_complexity: Mapped[Optional[int]] = mapped_column(Integer)
    lint_warnings: Mapped[Optional[int]] = mapped_column(Integer)
    inferred_big_o: Mapped[Optional[str]] = mapped_column(String(50))
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.submission_id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(
        Enum("rule", "llm", "hybrid", name="feedback_source"),
        nullable=False,
        default="hybrid",
    )
    summary_md: Mapped[str] = mapped_column(Text, nullable=False)
    bullets_json: Mapped[Optional[list]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class HintTemplate(Base):
    __tablename__ = "hint_templates"

    hint_template_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    hint_level: Mapped[int] = mapped_column(Integer, nullable=False)
    hint_text_md: Mapped[str] = mapped_column(Text, nullable=False)


class HintRequest(Base):
    __tablename__ = "hint_requests"

    hint_request_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    submission_id: Mapped[Optional[int]] = mapped_column(ForeignKey("submissions.submission_id", ondelete="SET NULL"))
    hint_level_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(
        Enum("template", "llm", name="hint_source"),
        nullable=False,
        default="template",
    )
    hint_text_md: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class UserSkill(Base):
    __tablename__ = "user_skill"

    user_skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class UserSkillHistory(Base):
    __tablename__ = "user_skill_history"

    user_skill_history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ProblemStatus(Base):
    __tablename__ = "problem_status"

    problem_status_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("not_started", "attempted", "solved", name="problem_status_enum"),
        nullable=False,
        default="not_started",
    )
    best_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    solved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    reason_md: Mapped[Optional[str]] = mapped_column(Text)
    algo_version: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    is_consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AuditLog(Base):
    """Insert-only audit trail. See NFR 3.2.5 / SRS audit logging."""
    __tablename__ = "audit_log"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_kind: Mapped[Optional[str]] = mapped_column(String(40))
    target_id: Mapped[Optional[str]] = mapped_column(String(60))
    detail: Mapped[Optional[str]] = mapped_column(String(255))
    source_ip: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class AiSolution(Base):
    __tablename__ = "ai_solutions"

    ai_solution_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.problem_id", ondelete="CASCADE"), nullable=False)
    explanation_md: Mapped[str] = mapped_column(Text, nullable=False)
    solution_code: Mapped[str] = mapped_column(Text, nullable=False)
    time_complexity: Mapped[Optional[str]] = mapped_column(String(50))
    space_complexity: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
