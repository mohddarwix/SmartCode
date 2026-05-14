-- ============================================================================
-- AI Programming Tutor - FULL DEMO RESET
--
-- DESTRUCTIVE: this wipes ALL real user accounts (registrations, submissions,
-- diagnostic attempts, skill history) and restores the canonical demo state.
-- Only run this when you explicitly want that. For just refreshing the
-- problem/test-case content without touching users, run seed_problems.sql.
--
-- For MariaDB CLI:
--   SOURCE seed_problems.sql;
--   SOURCE seed_users.sql;
-- For HeidiSQL or any other GUI: open and execute the two files in order.
-- ============================================================================

SOURCE seed_problems.sql;
SOURCE seed_problems_extra.sql;
SOURCE seed_users.sql;
