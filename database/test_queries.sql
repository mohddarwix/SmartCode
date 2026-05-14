-- ============================================================================
-- AI Programming Tutor - Verification Queries
-- Run AFTER schema.sql + seed.sql. Highlight a block and press F9 in HeidiSQL.
-- ============================================================================

USE ai_tutor_system;

-- ---------------------------------------------------------------------------
-- 1. Row counts per table
-- ---------------------------------------------------------------------------
SELECT 'users'              AS table_name, COUNT(*) AS rows FROM users
UNION ALL SELECT 'skills',              COUNT(*) FROM skills
UNION ALL SELECT 'problems',            COUNT(*) FROM problems
UNION ALL SELECT 'problem_skills',      COUNT(*) FROM problem_skills
UNION ALL SELECT 'test_cases',          COUNT(*) FROM test_cases
UNION ALL SELECT 'diagnostic_attempts', COUNT(*) FROM diagnostic_attempts
UNION ALL SELECT 'diagnostic_items',    COUNT(*) FROM diagnostic_items
UNION ALL SELECT 'submissions',         COUNT(*) FROM submissions
UNION ALL SELECT 'metrics',             COUNT(*) FROM metrics
UNION ALL SELECT 'feedback',            COUNT(*) FROM feedback
UNION ALL SELECT 'hint_templates',      COUNT(*) FROM hint_templates
UNION ALL SELECT 'hint_requests',       COUNT(*) FROM hint_requests
UNION ALL SELECT 'user_skill',          COUNT(*) FROM user_skill
UNION ALL SELECT 'user_skill_history',  COUNT(*) FROM user_skill_history
UNION ALL SELECT 'problem_status',      COUNT(*) FROM problem_status
UNION ALL SELECT 'recommendations',     COUNT(*) FROM recommendations
UNION ALL SELECT 'ai_solutions',        COUNT(*) FROM ai_solutions;

-- ---------------------------------------------------------------------------
-- 2. Skill profile for a user (powers the radar chart)
-- ---------------------------------------------------------------------------
SELECT s.name AS skill, us.score
FROM user_skill us
JOIN skills s ON s.skill_id = us.skill_id
WHERE us.user_id = 2  -- Alice
ORDER BY s.display_order;

-- ---------------------------------------------------------------------------
-- 3. Solved problems list for a user
-- ---------------------------------------------------------------------------
SELECT p.problem_id, p.title, p.difficulty, ps.best_score,
       GROUP_CONCAT(s.name ORDER BY s.display_order SEPARATOR ', ') AS skills
FROM problem_status ps
JOIN problems p              ON p.problem_id = ps.problem_id
LEFT JOIN problem_skills psk ON psk.problem_id = p.problem_id
LEFT JOIN skills s           ON s.skill_id = psk.skill_id
WHERE ps.user_id = 2 AND ps.status = 'solved'
GROUP BY p.problem_id, p.title, p.difficulty, ps.best_score
ORDER BY ps.solved_at DESC;

-- ---------------------------------------------------------------------------
-- 4. Visible test cases for a problem (what the editor shows)
-- ---------------------------------------------------------------------------
SELECT name, visibility, input_blob, expected_blob
FROM test_cases
WHERE problem_id = 1
  AND visibility IN ('sample', 'public')
ORDER BY test_case_id;

-- ---------------------------------------------------------------------------
-- 5. Submission detail (powers the feedback screen)
-- ---------------------------------------------------------------------------
SELECT s.submission_id, u.full_name, p.title, s.status, s.score,
       s.total_runtime_ms, s.total_memory_kb,
       m.score_correctness, m.score_edge_cases, m.score_code_quality,
       m.score_time_complexity, m.inferred_big_o,
       fb.summary_md, fb.bullets_json
FROM submissions s
JOIN users u       ON u.user_id = s.user_id
JOIN problems p    ON p.problem_id = s.problem_id
LEFT JOIN metrics m  ON m.submission_id = s.submission_id
LEFT JOIN feedback fb ON fb.submission_id = s.submission_id
WHERE s.submission_id = 4;

-- ---------------------------------------------------------------------------
-- 6. Next-problem recommendation
-- ---------------------------------------------------------------------------
SELECT r.recommendation_id, p.title, p.difficulty, r.reason_md
FROM recommendations r
JOIN problems p ON p.problem_id = r.problem_id
WHERE r.user_id = 2 AND r.is_consumed = FALSE
ORDER BY r.created_at DESC
LIMIT 1;

-- ---------------------------------------------------------------------------
-- 7. Recommendation candidates: active problems NOT yet solved
-- ---------------------------------------------------------------------------
SELECT p.problem_id, p.title, p.difficulty
FROM problems p
LEFT JOIN problem_status ps
       ON ps.problem_id = p.problem_id
      AND ps.user_id = 2
      AND ps.status = 'solved'
WHERE p.is_active = TRUE
  AND ps.problem_status_id IS NULL
ORDER BY FIELD(p.difficulty, 'easy', 'medium', 'hard'), p.problem_id;

-- ---------------------------------------------------------------------------
-- 8. Admin users summary
-- ---------------------------------------------------------------------------
SELECT u.user_id, u.full_name, u.email,
       SUM(CASE WHEN ps.status = 'solved' THEN 1 ELSE 0 END) AS solved,
       COALESCE(ROUND(AVG(NULLIF(ps.best_score, 0))), 0)     AS avg_score,
       u.last_login_at
FROM users u
LEFT JOIN problem_status ps ON ps.user_id = u.user_id
WHERE u.role = 'student'
GROUP BY u.user_id, u.full_name, u.email, u.last_login_at
ORDER BY solved DESC;

-- ---------------------------------------------------------------------------
-- 9. Problems with their skill tags (admin Problems list)
-- ---------------------------------------------------------------------------
SELECT p.problem_id, p.title, p.difficulty, p.is_active,
       GROUP_CONCAT(s.name ORDER BY s.display_order SEPARATOR ', ') AS skills
FROM problems p
LEFT JOIN problem_skills ps ON ps.problem_id = p.problem_id
LEFT JOIN skills s          ON s.skill_id   = ps.skill_id
GROUP BY p.problem_id, p.title, p.difficulty, p.is_active
ORDER BY p.problem_id;
