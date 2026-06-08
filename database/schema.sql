-- ============================================================================
-- AI Programming Tutor - Database Schema (single Problem Solving track)
-- Trimmed to what the app actually uses. MariaDB / MySQL compatible.
-- Run this once to (re)create the database.
-- ============================================================================

DROP DATABASE IF EXISTS ai_tutor_system;
CREATE DATABASE ai_tutor_system
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE ai_tutor_system;

-- ---------------------------------------------------------------------------
-- 1. USERS
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    user_id                 INT AUTO_INCREMENT PRIMARY KEY,
    full_name               VARCHAR(100) NOT NULL,
    email                   VARCHAR(150) NOT NULL UNIQUE,
    password_hash           VARCHAR(255) NOT NULL,
    role                    ENUM('student','admin') NOT NULL DEFAULT 'student',
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at           TIMESTAMP NULL DEFAULT NULL,
    diagnostic_completed_at TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 2. SKILLS  (the six radar axes in the dashboard)
-- ---------------------------------------------------------------------------
CREATE TABLE skills (
    skill_id      INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    description   TEXT,
    display_order INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 3. PROBLEMS
-- ---------------------------------------------------------------------------
CREATE TABLE problems (
    problem_id        INT AUTO_INCREMENT PRIMARY KEY,
    slug              VARCHAR(120) NOT NULL UNIQUE,
    title             VARCHAR(150) NOT NULL,
    difficulty        ENUM('easy','medium','hard') NOT NULL,
    source            VARCHAR(40) NULL,
    estimated_minutes INT NULL,
    statement_md      TEXT NOT NULL,
    constraints_md    TEXT,
    starter_code_md   TEXT,
    cheatsheet_md     TEXT NULL DEFAULT NULL,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_problems_active (is_active),
    INDEX idx_problems_difficulty (difficulty)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 4. PROBLEM_SKILLS  (many-to-many with weights)
-- ---------------------------------------------------------------------------
CREATE TABLE problem_skills (
    problem_skill_id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id       INT NOT NULL,
    skill_id         INT NOT NULL,
    weight           DECIMAL(4,2) NOT NULL DEFAULT 1.0,
    UNIQUE KEY uq_problem_skill (problem_id, skill_id),
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id)   REFERENCES skills(skill_id)    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 5. TEST_CASES  (input/expected pairs directly tied to a problem)
-- ---------------------------------------------------------------------------
CREATE TABLE test_cases (
    test_case_id    INT AUTO_INCREMENT PRIMARY KEY,
    problem_id      INT NOT NULL,
    name            VARCHAR(100) NULL,
    visibility      ENUM('sample','public','hidden') NOT NULL DEFAULT 'public',
    weight          DECIMAL(4,2) NOT NULL DEFAULT 1.0,
    input_blob      TEXT NOT NULL,
    expected_blob   TEXT NOT NULL,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
    INDEX idx_test_cases_problem (problem_id, visibility)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 6. DIAGNOSTIC_ATTEMPTS
-- ---------------------------------------------------------------------------
CREATE TABLE diagnostic_attempts (
    diagnostic_attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    started_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at  TIMESTAMP NULL DEFAULT NULL,
    status       ENUM('in_progress','completed','abandoned') NOT NULL DEFAULT 'in_progress',
    overall_score INT NULL,
    summary_md   TEXT NULL,
    grader_source ENUM('llm','heuristic') NOT NULL DEFAULT 'heuristic',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 7. DIAGNOSTIC_ITEMS  (one row per question answered in a diagnostic)
-- ---------------------------------------------------------------------------
CREATE TABLE diagnostic_items (
    diagnostic_item_id    INT AUTO_INCREMENT PRIMARY KEY,
    diagnostic_attempt_id INT NOT NULL,
    skill_id              INT NULL,
    problem_id            INT NULL,
    order_index           INT NOT NULL,
    question_md           TEXT NULL,
    user_answer           TEXT NULL,
    correct_answer        TEXT NULL,
    is_correct            BOOLEAN NULL,
    explanation_md        TEXT NULL,
    score                 INT NOT NULL DEFAULT 0,
    time_spent_seconds    INT NOT NULL DEFAULT 0,
    hints_used            INT NOT NULL DEFAULT 0,
    FOREIGN KEY (diagnostic_attempt_id) REFERENCES diagnostic_attempts(diagnostic_attempt_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id)              REFERENCES skills(skill_id)   ON DELETE SET NULL,
    FOREIGN KEY (problem_id)            REFERENCES problems(problem_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 8. SUBMISSIONS  (one attempt at a problem; stores the code inline)
-- ---------------------------------------------------------------------------
CREATE TABLE submissions (
    submission_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NOT NULL,
    problem_id        INT NOT NULL,
    language          VARCHAR(20) NOT NULL DEFAULT 'python',
    kind              ENUM('run','submit') NOT NULL DEFAULT 'submit',
    code              MEDIUMTEXT NOT NULL,
    status            ENUM('pending','accepted','wrong_answer','runtime_error','time_limit','compile_error') NOT NULL DEFAULT 'pending',
    score             INT NOT NULL DEFAULT 0,
    submitted_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_runtime_ms  INT NULL,
    total_memory_kb   INT NULL,
    case_results_json JSON NULL,
    FOREIGN KEY (user_id)    REFERENCES users(user_id)      ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
    INDEX idx_submissions_user_problem (user_id, problem_id),
    INDEX idx_submissions_user_problem_kind (user_id, problem_id, kind, status),
    INDEX idx_submissions_submitted_at (submitted_at)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 9. METRICS  (per-submission scoring detail)
-- ---------------------------------------------------------------------------
CREATE TABLE metrics (
    metrics_id              INT AUTO_INCREMENT PRIMARY KEY,
    submission_id           INT NOT NULL UNIQUE,
    score_correctness       INT NOT NULL DEFAULT 0,
    score_edge_cases        INT NOT NULL DEFAULT 0,
    score_code_quality      INT NOT NULL DEFAULT 0,
    score_time_complexity   INT NOT NULL DEFAULT 0,
    cyclomatic_complexity   INT NULL,
    lint_warnings           INT NULL,
    inferred_big_o          VARCHAR(50) NULL,
    passed_count            INT NOT NULL DEFAULT 0,
    total_count             INT NOT NULL DEFAULT 0,
    computed_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 10. FEEDBACK
-- ---------------------------------------------------------------------------
CREATE TABLE feedback (
    feedback_id    INT AUTO_INCREMENT PRIMARY KEY,
    submission_id  INT NOT NULL,
    source         ENUM('rule','llm','hybrid') NOT NULL DEFAULT 'hybrid',
    summary_md     TEXT NOT NULL,
    bullets_json   JSON NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 11. HINT_TEMPLATES
-- ---------------------------------------------------------------------------
CREATE TABLE hint_templates (
    hint_template_id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id       INT NOT NULL,
    hint_level       INT NOT NULL,
    hint_text_md     TEXT NOT NULL,
    UNIQUE KEY uq_problem_hintlevel (problem_id, hint_level),
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 12. HINT_REQUESTS  (log of hint requests)
-- ---------------------------------------------------------------------------
CREATE TABLE hint_requests (
    hint_request_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id                INT NOT NULL,
    problem_id             INT NOT NULL,
    submission_id          INT NULL,
    hint_level_requested   INT NOT NULL,
    source                 ENUM('template','llm') NOT NULL DEFAULT 'template',
    hint_text_md           TEXT NOT NULL,
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)       REFERENCES users(user_id)             ON DELETE CASCADE,
    FOREIGN KEY (problem_id)    REFERENCES problems(problem_id)       ON DELETE CASCADE,
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 13. USER_SKILL
-- ---------------------------------------------------------------------------
CREATE TABLE user_skill (
    user_skill_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    skill_id      INT NOT NULL,
    score         INT NOT NULL DEFAULT 0,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_skill (user_id, skill_id),
    FOREIGN KEY (user_id)  REFERENCES users(user_id)   ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 14. USER_SKILL_HISTORY
-- ---------------------------------------------------------------------------
CREATE TABLE user_skill_history (
    user_skill_history_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT NOT NULL,
    skill_id INT NOT NULL,
    day      DATE NOT NULL,
    score    INT NOT NULL DEFAULT 0,
    UNIQUE KEY uq_user_skill_day (user_id, skill_id, day),
    FOREIGN KEY (user_id)  REFERENCES users(user_id)   ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 15. PROBLEM_STATUS
-- ---------------------------------------------------------------------------
CREATE TABLE problem_status (
    problem_status_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id            INT NOT NULL,
    problem_id         INT NOT NULL,
    status             ENUM('not_started','attempted','solved') NOT NULL DEFAULT 'not_started',
    best_score         INT NOT NULL DEFAULT 0,
    attempts_count     INT NOT NULL DEFAULT 0,
    last_attempted_at  TIMESTAMP NULL DEFAULT NULL,
    solved_at          TIMESTAMP NULL DEFAULT NULL,
    UNIQUE KEY uq_user_problem (user_id, problem_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id)       ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 16. RECOMMENDATIONS
-- ---------------------------------------------------------------------------
CREATE TABLE recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NOT NULL,
    problem_id        INT NOT NULL,
    reason_md         TEXT,
    algo_version      VARCHAR(50) NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_consumed       BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (user_id)    REFERENCES users(user_id)      ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
    INDEX idx_recommendations_user (user_id, is_consumed)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 18. AUDIT_LOG  (NFR 3.2.5 -- security/observability)
-- Records auth events (login/register), submissions, hint requests, admin
-- changes. Insert-only; nothing in the app deletes rows. Indexed for
-- per-user lookups and event-type filters.
-- ---------------------------------------------------------------------------
CREATE TABLE audit_log (
    audit_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NULL,
    event_type    VARCHAR(40) NOT NULL,
    target_kind   VARCHAR(40) NULL,
    target_id     VARCHAR(60) NULL,
    detail        VARCHAR(255) NULL,
    source_ip     VARCHAR(45) NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_user_time (user_id, created_at),
    INDEX idx_audit_event_time (event_type, created_at),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 17. AI_SOLUTIONS  (LLM-generated reference explanation per problem)
-- ---------------------------------------------------------------------------
CREATE TABLE ai_solutions (
    ai_solution_id    INT AUTO_INCREMENT PRIMARY KEY,
    problem_id        INT NOT NULL,
    explanation_md    TEXT NOT NULL,
    solution_code     MEDIUMTEXT NOT NULL,
    time_complexity   VARCHAR(50)  NULL,
    space_complexity  VARCHAR(50)  NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE
) ENGINE=InnoDB;
