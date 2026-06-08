from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

# Top-N weak passwords that pass the character-class checks but are still
# trivially guessable. Kept small on purpose -- this is a school project, not
# a bank. Cover the cases real students actually pick first.
_COMMON_WEAK_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "qwerty123",
    "12345678",
    "abc12345",
    "letmein1",
    "welcome1",
    "iloveyou",
    "monkey123",
    "admin123",
    "test1234",
    "passw0rd",
    "pa$$w0rd",
    "p@ssw0rd",
    "changeme",
    "trustno1",
    "shadow12",
    "master12",
    "qwerty12",
    "asdf1234",
    "1q2w3e4r",
    "1qaz2wsx",
    "qazwsx12",
    "zaq12wsx",
    "lebanon1",
    "beirut12",
    "lau12345",
}


def _validate_strong_password(value: str) -> str:
    """Reject obviously-weak passwords. Run BEFORE bcrypt; pydantic's min_length
    handles too-short. We additionally require character-class diversity and
    block a small blacklist of trivially-guessable strings."""
    pwd = value
    if len(pwd) < 8:
        # Belt-and-suspenders; Field min_length already enforces this.
        raise ValueError("Password must be at least 8 characters.")
    has_lower = any(c.islower() for c in pwd)
    has_upper = any(c.isupper() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    missing = []
    if not has_lower:
        missing.append("a lowercase letter")
    if not has_upper:
        missing.append("an uppercase letter")
    if not has_digit:
        missing.append("a digit")
    if missing:
        raise ValueError("Password must include " + ", ".join(missing) + ".")
    if pwd.lower() in _COMMON_WEAK_PASSWORDS:
        raise ValueError(
            "This password is on the list of most-guessed passwords. Pick something less common."
        )
    return pwd


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_strong_password(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: EmailStr
    role: Literal["student", "admin"]
    created_at: datetime
    last_login_at: Optional[datetime] = None
    diagnostic_completed_at: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: int
    name: str
    description: Optional[str] = None
    display_order: int


class UserSkillOut(BaseModel):
    skill_id: int
    name: str
    score: int


class SkillHistoryPoint(BaseModel):
    day: date
    score: int


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------


class ProblemSummary(BaseModel):
    problem_id: int
    slug: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    source: Optional[str] = None
    estimated_minutes: Optional[int] = None
    skills: list[str]
    is_active: bool
    user_status: Literal["not_started", "attempted", "solved"] = "not_started"
    best_score: int = 0


class TestCaseOut(BaseModel):
    name: Optional[str] = None
    visibility: Literal["sample", "public", "hidden"]
    input_blob: str
    expected_blob: str


class ProblemDetail(BaseModel):
    problem_id: int
    slug: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    source: Optional[str] = None
    estimated_minutes: Optional[int] = None
    statement_md: str
    constraints_md: Optional[str] = None
    starter_code_md: Optional[str] = None
    cheatsheet_md: Optional[str] = None  # per-problem Python syntax reference
    skills: list[str]
    test_cases: list[TestCaseOut]  # visible cases only (sample + public)
    has_hidden_tests: bool


class HintRequestPayload(BaseModel):
    """POST body for /problems/:id/hint. The current code lets the LLM tailor the hint."""

    code: str = ""
    language: Literal["python"] = "python"
    level: int = Field(default=1, ge=1, le=3)


class HintOut(BaseModel):
    hint_level: int
    hint_text_md: str
    source: Literal["llm", "heuristic"] = "llm"
    cost_points: int = 0  # how many points this single hint cost (escalating)
    total_hints_used: int = 0  # cumulative for this user+problem (incl. this one)
    total_cost_points: int = 0  # cumulative penalty (incl. this one)


class AiSolutionOut(BaseModel):
    explanation_md: str
    solution_code: str
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None


# --- Interactive AI tutor (step-by-step chat) ---


class TutorMessageIn(BaseModel):
    role: Literal["tutor", "student"]
    content: str
    step_index: Optional[int] = None


class TutorTurnRequest(BaseModel):
    history: list[TutorMessageIn] = []
    student_message: Optional[str] = None  # null on the very first turn


class TutorTurnResponse(BaseModel):
    tutor_response: str
    step_index: int
    total_steps: int
    is_complete: bool
    source: Literal["llm", "heuristic"] = "llm"


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------


class SubmissionCreate(BaseModel):
    problem_id: int
    code: str = Field(min_length=1)
    language: Literal["python"] = "python"


class FeedbackBullet(BaseModel):
    kind: Literal["good", "warn", "bad"] = "good"
    text: str


class MetricsOut(BaseModel):
    score_correctness: int
    score_edge_cases: int
    score_code_quality: int
    score_time_complexity: int
    passed_count: int
    total_count: int
    inferred_big_o: Optional[str] = None


class TestCaseResultOut(BaseModel):
    case_index: int
    name: Optional[str] = None
    visibility: Literal["sample", "public", "hidden"]
    input_blob: str
    expected_blob: str
    predicted_output: str
    passed: bool
    explanation_md: str = ""
    severity: Optional[Literal["minor", "moderate", "severe"]] = None


class RunRequest(BaseModel):
    code: str = Field(min_length=1)
    language: Literal["python"] = "python"


class RunResult(BaseModel):
    """Returned by POST /api/problems/:id/run* endpoints."""

    cases: list[TestCaseResultOut]
    passed_count: int
    total_count: int
    all_passed: bool
    status: Literal[
        "accepted", "wrong_answer", "runtime_error", "time_limit", "compile_error"
    ]
    # "sandbox" = plain code execution (no LLM, no severity, no penalty)
    # "llm"     = sandbox + LLM commentary (severity, code-quality, fail-cost)
    # "heuristic" = LLM was offline, fell back to no-AI grading
    source: Literal["llm", "heuristic", "sandbox"]


class SkillDelta(BaseModel):
    skill: str
    before: int
    after: int


class NextProblemSuggestion(BaseModel):
    problem_id: int
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    reason_md: Optional[str] = None
    estimated_minutes: Optional[int] = None


class ScoreAdjustment(BaseModel):
    """How the saved `score` was reduced from the raw LLM grade."""

    raw_score: int  # the grader's verdict before any penalty
    penalty_points: int  # total severity points from prior failed attempts (>=0)
    prior_failed_attempts: int  # how many earlier failed submissions contributed
    final_score: int  # raw_score - 2 * penalty_points, clamped to [50, 100]


class SubmissionDetail(BaseModel):
    submission_id: int
    problem_id: int
    problem_title: str
    language: str
    status: Literal[
        "pending",
        "accepted",
        "wrong_answer",
        "runtime_error",
        "time_limit",
        "compile_error",
    ]
    score: int
    submitted_at: datetime
    total_runtime_ms: Optional[int] = None
    total_memory_kb: Optional[int] = None
    metrics: Optional[MetricsOut] = None
    feedback_summary_md: Optional[str] = None
    feedback_bullets: list[FeedbackBullet] = []
    cases: list[TestCaseResultOut] = []
    skills_updated: list[SkillDelta] = []
    next_problem: Optional[NextProblemSuggestion] = (
        None  # kept for back-compat; mirrors next_problems[0]
    )
    next_problems: list[NextProblemSuggestion] = (
        []
    )  # up to 3 picks (LLM + heuristic fallback)
    grader_source: Optional[Literal["llm", "heuristic"]] = None
    score_adjustment: Optional[ScoreAdjustment] = None
    # Optional — populated by GET /problems/:id/my-attempt and similar review endpoints
    # so the read-only solved view can show the user's accepted source.
    code: Optional[str] = None


class HintRecord(BaseModel):
    hint_level: int
    hint_text_md: str
    source: Literal["template", "llm"]
    created_at: datetime


class MySubmissionListItem(BaseModel):
    """Compact row in the EditorScreen 'Submissions' tab."""

    submission_id: int
    kind: Literal["run", "submit"]
    status: Literal[
        "pending",
        "accepted",
        "wrong_answer",
        "runtime_error",
        "time_limit",
        "compile_error",
    ]
    score: int
    submitted_at: datetime
    language: str
    code: str
    passed_count: Optional[int] = None
    total_count: Optional[int] = None


class MyAttemptOut(BaseModel):
    """Read-only view a student gets after they've solved a problem."""

    submission: SubmissionDetail
    hints: list[HintRecord]
    hint_total_cost: int


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------


class DiagnosticItemSubmit(BaseModel):
    """One question the user just answered. The backend grades it (LLM if available)."""

    order_index: int
    skill_id: Optional[int] = None
    skill_name: Optional[str] = None  # legacy single-skill hint (kept for label/UI)
    # Multiple skills each question exercises. Replaces the single-skill model:
    # every coding question naturally tests Algorithms + Edge Cases + Code Quality
    # + Time Complexity, etc. The grader returns per-skill sub-scores for each
    # tested skill, and skill totals are averaged across all items that tested
    # them. If omitted, defaults to [skill_name] for backwards compatibility.
    tested_skills: list[str] = Field(default_factory=list)
    problem_id: Optional[int] = None
    type: Literal["mcq", "coding"] = "mcq"
    question: str = Field(min_length=1)
    user_answer: str = ""
    correct_answer: Optional[str] = None  # canonical answer for MCQs; None for coding
    time_spent_seconds: int = Field(ge=0, default=0)
    hints_used: int = Field(ge=0, default=0)


class DiagnosticSubmit(BaseModel):
    items: list[DiagnosticItemSubmit] = Field(min_length=1)


class DiagnosticItemResultOut(BaseModel):
    order_index: int
    skill_name: Optional[str] = None
    tested_skills: list[str] = Field(default_factory=list)
    per_skill_scores: dict[str, int] = Field(
        default_factory=dict
    )  # this item's score along each skill it tested
    type: Literal["mcq", "coding"]
    question: str
    user_answer: str
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: int
    explanation_md: str
    answer_kind: Literal["code", "pseudo_english", "blank"] = "code"


class DiagnosticResultOut(BaseModel):
    """Returned by POST /diagnostic and GET /diagnostic/last."""

    diagnostic_attempt_id: int
    finished_at: Optional[datetime] = None
    overall_score: int
    summary_md: str
    grader_source: Literal["llm", "heuristic"]
    items: list[DiagnosticItemResultOut]
    skill_scores: list[UserSkillOut]
    weak_skills: list[str]
    next_problem: Optional["NextProblemSuggestion"] = (
        None  # back-compat; mirrors next_problems[0]
    )
    next_problems: list["NextProblemSuggestion"] = []  # up to 3 picks
    user: UserOut


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------


class AdminUserRow(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    role: Literal["student", "admin"]
    solved: int
    avg_score: int
    last_login_at: Optional[datetime] = None
    created_at: datetime


class AdminStats(BaseModel):
    users: int
    students: int
    problems: int
    skills: int
    submissions: int
    submissions_last_7_days: list[
        dict[str, Any]
    ]  # [{day: "2026-05-08", count: 12}, ...]


class AdminUserCreate(BaseModel):
    """Admin-only invite/create. Used when self-registration is closed in prod."""

    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["student", "admin"] = "student"

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_strong_password(v)


class AdminProblemUpsert(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=150)
    difficulty: Literal["easy", "medium", "hard"]
    source: Optional[str] = None
    estimated_minutes: Optional[int] = Field(default=None, ge=1)
    statement_md: str = Field(min_length=1)
    constraints_md: Optional[str] = None
    starter_code_md: Optional[str] = None
    is_active: bool = True
    skill_ids: list[int] = []


class AdminProblemRow(BaseModel):
    problem_id: int
    slug: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    source: Optional[str] = None
    estimated_minutes: Optional[int] = None
    statement_md: str
    constraints_md: Optional[str] = None
    starter_code_md: Optional[str] = None
    is_active: bool
    skills: list[str]
    skill_ids: list[int]


class AdminUserActivity(BaseModel):
    """One row in the admin per-user drilldown timeline."""

    when: datetime
    event_type: str  # e.g. "submission.accepted", "login.success"
    target_kind: Optional[str] = None
    target_id: Optional[str] = None
    detail: Optional[str] = None
    source_ip: Optional[str] = None


class AdminUserDetail(BaseModel):
    """Per-user drilldown view (FR-Admin 5)."""

    user: AdminUserRow
    skill_scores: list[UserSkillOut]
    recent_submissions: list[MySubmissionListItem]
    audit_events: list[AdminUserActivity]


class AdminTestCaseUpsert(BaseModel):
    """Admin payload for create/update of a single test case."""

    name: Optional[str] = Field(default=None, max_length=100)
    visibility: Literal["sample", "public", "hidden"] = "hidden"
    input_blob: str = Field(min_length=1)
    expected_blob: str = Field(min_length=1)


class AdminTestCaseRow(BaseModel):
    test_case_id: int
    problem_id: int
    name: Optional[str] = None
    visibility: Literal["sample", "public", "hidden"]
    input_blob: str
    expected_blob: str


class AdminSkillUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    display_order: int = 0


class AdminSkillRow(BaseModel):
    skill_id: int
    name: str
    description: Optional[str] = None
    display_order: int
    problem_count: int
