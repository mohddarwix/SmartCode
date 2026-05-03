INSERT INTO users (full_name, email, password_hash)
VALUES 
('Mohamed Darwish', 'mohamed@test.com', 'hashed123'),
('Karim Koaik', 'karim@test.com', 'hashed456');

INSERT INTO skills (name, description)
VALUES 
('Arrays', 'Working with arrays'),
('Loops', 'Iteration concepts'),
('Edge Cases', 'Handling corner cases');

INSERT INTO problems (title, description, difficulty)
VALUES 
('Two Sum', 'Find two numbers that sum to target', 'easy'),
('Count Evens', 'Count even numbers in array', 'easy');

INSERT INTO problem_skills (problem_id, skill_id, weight)
VALUES
(1, 1, 1.0), -- Two Sum → Arrays
(1, 3, 0.5), -- Two Sum → Edge Cases
(2, 2, 1.0); -- Count Evens → Loops

INSERT INTO test_cases (problem_id, input_data, expected_output, is_hidden)
VALUES
(1, '[2,7,11,15],9', '[0,1]', FALSE),
(1, '[3,2,4],6', '[1,2]', TRUE),
(2, '[1,2,3,4]', '2', FALSE);

SELECT * FROM problems;

SELECT p.title, s.name AS skill, ps.weight
FROM problems p
JOIN problem_skills ps ON p.problem_id = ps.problem_id
JOIN skills s ON ps.skill_id = s.skill_id
WHERE p.problem_id = 1;

SELECT input_data, expected_output, is_hidden
FROM test_cases
WHERE problem_id = 1;

INSERT INTO submissions (user_id, problem_id, code, verdict)
VALUES (1, 1, 'def two_sum(): pass', 'wrong_answer');

SELECT * FROM submissions;

INSERT INTO evaluation_results (
    submission_id,
    correctness_score,
    edge_case_score,
    time_complexity_score,
    code_quality_score,
    final_score
)
VALUES (1, 70, 50, 80, 60, 65);

SELECT s.submission_id, e.final_score
FROM submissions s
JOIN evaluation_results e 
ON s.submission_id = e.submission_id;

SELECT f.feedback_text, f.suggestion
FROM feedback f
JOIN submissions s ON f.submission_id = s.submission_id
WHERE s.user_id = 1;

INSERT INTO user_skills (user_id, skill_id, score)
VALUES 
(1, 1, 50),
(1, 2, 40),
(1, 3, 30);

UPDATE user_skills
SET score = score + 5
WHERE user_id = 1 AND skill_id = 1;

SELECT u.full_name, s.name, us.score
FROM user_skills us
JOIN users u ON us.user_id = u.user_id
JOIN skills s ON us.skill_id = s.skill_id
WHERE u.user_id = 1;

INSERT INTO recommendations (user_id, problem_id, reason)
VALUES 
(1, 2, 'Improve loops skill');

SELECT p.title, r.reason
FROM recommendations r
JOIN problems p ON r.problem_id = p.problem_id
WHERE r.user_id = 1;

INSERT INTO ai_solutions (problem_id, explanation, solution_code)
VALUES 
(1, 'Use hash map to store complements',
 'def two_sum(nums, target): return []');
 
SELECT explanation, solution_code
FROM ai_solutions
WHERE problem_id = 1;

SELECT 
u.full_name,
p.title,
e.final_score,
f.feedback_text
FROM submissions s
JOIN users u ON s.user_id = u.user_id
JOIN problems p ON s.problem_id = p.problem_id
JOIN evaluation_results e ON s.submission_id = e.submission_id
JOIN feedback f ON s.submission_id = f.submission_id;
