CREATE DATABASE ai_tutor_system;
USE ai_tutor_system;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE problems (
    problem_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    difficulty ENUM('easy', 'medium', 'hard') NOT NULL,
    sample_input TEXT,
    sample_output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE problem_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id INT NOT NULL,
    skill_id INT NOT NULL,
    weight DECIMAL(4,2) DEFAULT 1.0,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

CREATE TABLE test_cases (
    test_case_id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id INT NOT NULL,
    input_data TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
);

CREATE TABLE submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    problem_id INT NOT NULL,
    code TEXT NOT NULL,
    verdict ENUM('accepted', 'wrong_answer', 'runtime_error', 'pending') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
);

CREATE TABLE evaluation_results (
    evaluation_id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT NOT NULL,
    correctness_score INT DEFAULT 0,
    edge_case_score INT DEFAULT 0,
    time_complexity_score INT DEFAULT 0,
    code_quality_score INT DEFAULT 0,
    final_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id)
);

CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT NOT NULL,
    feedback_text TEXT,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id)
);

CREATE TABLE hints (
    hint_id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id INT NOT NULL,
    hint_level INT NOT NULL,
    hint_text TEXT,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
);

CREATE TABLE user_skills (
    user_skill_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    score INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE(user_id, skill_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

CREATE TABLE recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    problem_id INT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
);

CREATE TABLE ai_solutions (
    ai_solution_id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id INT NOT NULL,
    explanation TEXT,
    solution_code TEXT,
    time_complexity VARCHAR(100),
    space_complexity VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
);

