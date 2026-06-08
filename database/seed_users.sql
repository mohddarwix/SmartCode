-- ============================================================================
-- AI Programming Tutor - USERS / DEMO DATA SEED
-- DESTRUCTIVE: wipes every user account and all of its history (submissions,
-- diagnostic attempts, skill scores, recommendations). Run only when you
-- want to restore the canonical 5 demo accounts.
--
-- Requires seed_problems.sql to have been applied first (FKs reference
-- problems and skills).
-- ============================================================================

USE ai_tutor_system;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE recommendations;
TRUNCATE TABLE problem_status;
TRUNCATE TABLE user_skill_history;
TRUNCATE TABLE user_skill;
TRUNCATE TABLE hint_requests;
TRUNCATE TABLE feedback;
TRUNCATE TABLE metrics;
TRUNCATE TABLE submissions;
TRUNCATE TABLE diagnostic_items;
TRUNCATE TABLE diagnostic_attempts;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------------
-- USERS  (all seeded passwords are bcrypt("Test1234"))
-- ---------------------------------------------------------------------------
INSERT INTO users (user_id, full_name, email, password_hash, role, created_at, last_login_at, diagnostic_completed_at) VALUES
(1, 'System Admin',  'admin@example.com',  '$2b$12$/WFU2IdILcF/tCRkJjn9ZeETFxCmeoFZBWcaRp3MglHbJ3UJMkkX2', 'admin',   '2026-03-01 09:00:00', '2026-05-13 08:00:00', NULL),
(2, 'Alice Johnson', 'alice@example.com',  '$2b$12$/WFU2IdILcF/tCRkJjn9ZeETFxCmeoFZBWcaRp3MglHbJ3UJMkkX2', 'student', '2026-03-10 10:00:00', '2026-05-12 19:30:00', '2026-03-10 10:32:00'),
(3, 'Bob Lee',       'bob@example.com',    '$2b$12$/WFU2IdILcF/tCRkJjn9ZeETFxCmeoFZBWcaRp3MglHbJ3UJMkkX2', 'student', '2026-03-12 10:00:00', '2026-05-13 11:00:00', '2026-03-12 10:25:00'),
(4, 'Carla Singh',   'carla@example.com',  '$2b$12$/WFU2IdILcF/tCRkJjn9ZeETFxCmeoFZBWcaRp3MglHbJ3UJMkkX2', 'student', '2026-04-01 14:00:00', '2026-05-10 17:00:00', NULL),
(5, 'Daniel Park',   'daniel@example.com', '$2b$12$/WFU2IdILcF/tCRkJjn9ZeETFxCmeoFZBWcaRp3MglHbJ3UJMkkX2', 'student', '2026-02-20 09:00:00', '2026-05-13 12:00:00', '2026-02-20 09:35:00');

-- ---------------------------------------------------------------------------
-- USER_SKILL  (Alice matches the frontend mock's radar values)
-- ---------------------------------------------------------------------------
INSERT INTO user_skill (user_id, skill_id, score) VALUES
-- Alice
(2, 1, 75), (2, 2, 65), (2, 3, 45), (2, 4, 85), (2, 6, 50),
-- Bob
(3, 1, 82), (3, 2, 78), (3, 3, 70), (3, 4, 88), (3, 6, 72),
-- Carla
(4, 1, 35), (4, 2, 40), (4, 3, 25), (4, 4, 60), (4, 6, 30),
-- Daniel
(5, 1, 92), (5, 2, 90), (5, 3, 85), (5, 4, 95), (5, 6, 90);

-- ---------------------------------------------------------------------------
-- USER_SKILL_HISTORY  (Alice's Edge Cases trend feeds the dashboard line chart)
-- ---------------------------------------------------------------------------
INSERT INTO user_skill_history (user_id, skill_id, day, score) VALUES
(2, 3, '2026-04-13', 30),
(2, 3, '2026-04-20', 35),
(2, 3, '2026-04-27', 38),
(2, 3, '2026-05-04', 45),
(2, 3, '2026-05-13', 45);

-- ---------------------------------------------------------------------------
-- DIAGNOSTIC_ATTEMPTS + DIAGNOSTIC_ITEMS
-- ---------------------------------------------------------------------------
INSERT INTO diagnostic_attempts (diagnostic_attempt_id, user_id, started_at, finished_at, status) VALUES
(1, 2, '2026-03-10 10:05:00', '2026-03-10 10:32:00', 'completed'),
(2, 3, '2026-03-12 10:05:00', '2026-03-12 10:25:00', 'completed'),
(3, 5, '2026-02-20 09:10:00', '2026-02-20 09:35:00', 'completed');

INSERT INTO diagnostic_items (diagnostic_attempt_id, skill_id, problem_id, order_index, score, time_spent_seconds, hints_used) VALUES
(1, 1, NULL, 1, 100, 45, 0),
(1, 2, NULL, 2, 100, 30, 0),
(1, 3, NULL, 3,   0, 60, 0),
(1, 6, NULL, 4,   0, 55, 0),
(1, 4, NULL, 5, 100, 25, 0),
(1, NULL, NULL, 6, 100, 40, 0),
(1, 1, 1,    7,  80, 420, 1),
(1, 3, NULL, 8,  60, 360, 1);

-- ---------------------------------------------------------------------------
-- SUBMISSIONS  (Alice's solved history)
-- ---------------------------------------------------------------------------
INSERT INTO submissions (submission_id, user_id, problem_id, language, code, status, score, submitted_at, total_runtime_ms, total_memory_kb) VALUES
(1, 2, 1, 'python',
 'class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, x in enumerate(nums):\n            if target - x in seen:\n                return [seen[target - x], i]\n            seen[x] = i\n',
 'accepted', 92, '2026-04-15 14:20:00', 42, 9000),
(2, 2, 3, 'python',
 'class Solution:\n    def reverseList(self, head):\n        prev = None\n        cur = head\n        while cur:\n            nxt = cur.next\n            cur.next = prev\n            prev = cur\n            cur = nxt\n        return prev\n',
 'accepted', 88, '2026-04-22 16:00:00', 36, 9500),
(3, 2, 5, 'python',
 'class Solution:\n    def maxProfit(self, prices):\n        lo = float("inf"); best = 0\n        for p in prices:\n            lo = min(lo, p)\n            best = max(best, p - lo)\n        return best\n',
 'accepted', 78, '2026-05-05 17:00:00', 64, 10200),
(4, 2, 6, 'python',
 'class Solution:\n    def maxSubArray(self, nums):\n        best = cur = nums[0]\n        for x in nums[1:]:\n            cur = max(x, cur + x)\n            best = max(best, cur)\n        return best\n',
 'accepted', 85, '2026-05-12 19:25:00', 80, 11000);

-- ---------------------------------------------------------------------------
-- METRICS  (per-submission detailed scores)
-- ---------------------------------------------------------------------------
INSERT INTO metrics (submission_id, score_correctness, score_edge_cases, score_code_quality, score_time_complexity, cyclomatic_complexity, lint_warnings, inferred_big_o, passed_count, total_count) VALUES
(1, 100, 90, 95,  92, 2, 0, 'O(n)',     3, 3),
(2, 100, 85, 90,  90, 3, 0, 'O(n)',     3, 3),
(3, 100, 70, 88,  85, 3, 1, 'O(n)',     3, 3),
(4, 100, 85, 92,  90, 3, 0, 'O(n)',     3, 3);

-- ---------------------------------------------------------------------------
-- FEEDBACK
-- ---------------------------------------------------------------------------
INSERT INTO feedback (submission_id, source, summary_md, bullets_json) VALUES
(4, 'hybrid',
    'Strong, idiomatic implementation of Kadane''s algorithm. Edge cases are handled cleanly.',
    JSON_ARRAY(
        JSON_OBJECT('kind','good','text','Idiomatic Kadane implementation, easy to follow'),
        JSON_OBJECT('kind','good','text','Handles single-element and all-negative arrays correctly'),
        JSON_OBJECT('kind','warn','text','Consider adding a guard for empty input before indexing nums[0]'),
        JSON_OBJECT('kind','warn','text','Variable name "cur" could be more descriptive (e.g. running_max)')
    ));

-- ---------------------------------------------------------------------------
-- PROBLEM_STATUS
-- ---------------------------------------------------------------------------
INSERT INTO problem_status (user_id, problem_id, status, best_score, attempts_count, last_attempted_at, solved_at) VALUES
(2, 1, 'solved',    92, 1, '2026-04-15 14:20:00', '2026-04-15 14:20:01'),
(2, 3, 'solved',    88, 1, '2026-04-22 16:00:00', '2026-04-22 16:00:01'),
(2, 5, 'solved',    78, 1, '2026-05-05 17:00:00', '2026-05-05 17:00:01'),
(2, 6, 'solved',    85, 1, '2026-05-12 19:25:00', '2026-05-12 19:25:01'),
(2, 2, 'attempted', 40, 2, '2026-05-13 08:00:00', NULL);

-- ---------------------------------------------------------------------------
-- RECOMMENDATIONS  (next problem for Alice = Number of Islands)
-- ---------------------------------------------------------------------------
INSERT INTO recommendations (user_id, problem_id, reason_md, algo_version) VALUES
(2, 10, 'Strengthens your weakest skill (Edge Cases, 45%) while introducing graph traversal in 2D grids.', 'v0.1');
