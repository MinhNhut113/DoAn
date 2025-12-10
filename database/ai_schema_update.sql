-- SQL Schema Updates for AI Features
-- Thêm các bảng mới cho chức năng AI

-- Table cho AI Chat Messages
CREATE TABLE ai_chat_messages (
    message_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    lesson_id INT FOREIGN KEY REFERENCES lessons(lesson_id),
    course_id INT FOREIGN KEY REFERENCES courses(course_id),
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    conversation_id VARCHAR(100),
    message_type VARCHAR(50) DEFAULT 'question',  -- question, clarification, explanation
    helpful_rating INT,  -- 1-5 rating
    created_at DATETIME DEFAULT GETDATE(),
    INDEX idx_user_id (user_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at)
);

-- Table cho AI Generated Questions
CREATE TABLE ai_generated_questions (
    gen_question_id INT PRIMARY KEY IDENTITY(1,1),
    topic_id INT NOT NULL FOREIGN KEY REFERENCES topics(topic_id),
    course_id INT NOT NULL FOREIGN KEY REFERENCES courses(course_id),
    lesson_id INT FOREIGN KEY REFERENCES lessons(lesson_id),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice',  -- multiple_choice, true_false, short_answer
    options TEXT,  -- JSON format
    correct_answer INT,
    explanation TEXT,
    difficulty_level INT DEFAULT 1,  -- 1-5
    generated_by VARCHAR(50) DEFAULT 'openai',
    is_approved BIT DEFAULT 0,
    approved_by INT FOREIGN KEY REFERENCES users(user_id),
    approval_date DATETIME,
    created_at DATETIME DEFAULT GETDATE(),
    times_used INT DEFAULT 0,
    INDEX idx_topic_id (topic_id),
    INDEX idx_course_id (course_id),
    INDEX idx_is_approved (is_approved),
    INDEX idx_created_at (created_at)
);

-- Table cho Generation Requests
CREATE TABLE generation_requests (
    request_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    request_type VARCHAR(50) NOT NULL,  -- question_generation, chat, recommendation
    topic_id INT FOREIGN KEY REFERENCES topics(topic_id),
    course_id INT FOREIGN KEY REFERENCES courses(course_id),
    lesson_id INT FOREIGN KEY REFERENCES lessons(lesson_id),
    input_prompt TEXT,
    request_params TEXT,  -- JSON format
    status VARCHAR(50) DEFAULT 'processing',  -- processing, completed, failed
    result_ids TEXT,  -- JSON format
    error_message TEXT,
    processing_time_seconds FLOAT,
    created_at DATETIME DEFAULT GETDATE(),
    completed_at DATETIME,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Optional: Create indexes for better performance
CREATE INDEX idx_ai_chat_user_lesson ON ai_chat_messages(user_id, lesson_id);
CREATE INDEX idx_ai_chat_user_course ON ai_chat_messages(user_id, course_id);
CREATE INDEX idx_ai_questions_difficulty ON ai_generated_questions(difficulty_level);
CREATE INDEX idx_ai_questions_approved ON ai_generated_questions(is_approved, created_at);

-- Optional: Create view for recommendation analysis
CREATE VIEW vw_learning_analytics AS
SELECT 
    u.user_id,
    u.username,
    c.course_id,
    c.course_name,
    t.topic_id,
    t.topic_name,
    AVG(CAST(qr.score AS FLOAT)) as avg_score,
    COUNT(qr.result_id) as attempt_count,
    MAX(qr.submitted_at) as last_attempt
FROM users u
JOIN quiz_results qr ON u.user_id = qr.user_id
JOIN quizzes q ON qr.quiz_id = q.quiz_id
JOIN topics t ON q.topic_id = t.topic_id
JOIN courses c ON t.course_id = c.course_id
GROUP BY u.user_id, u.username, c.course_id, c.course_name, t.topic_id, t.topic_name;

-- Optional: Create view for question quality metrics
CREATE VIEW vw_question_metrics AS
SELECT 
    gen_question_id,
    question_text,
    difficulty_level,
    times_used,
    is_approved,
    DATEDIFF(DAY, created_at, GETDATE()) as days_since_creation,
    CASE 
        WHEN times_used > 10 THEN 'Popular'
        WHEN times_used > 5 THEN 'Moderate'
        ELSE 'Unused'
    END as usage_level
FROM ai_generated_questions;

-- Table cho phân tích câu trả lời sai
CREATE TABLE incorrect_answer_analysis (
    analysis_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    question_id INT NOT NULL FOREIGN KEY REFERENCES quiz_questions(question_id),
    topic_id INT NOT NULL FOREIGN KEY REFERENCES topics(topic_id),
    course_id INT NOT NULL FOREIGN KEY REFERENCES courses(course_id),
    lesson_id INT FOREIGN KEY REFERENCES lessons(lesson_id),
    quiz_id INT FOREIGN KEY REFERENCES quizzes(quiz_id),
    question_text TEXT NOT NULL,
    user_answer INT,  -- Index of user's answer (0-3)
    correct_answer INT NOT NULL,
    difficulty_level INT DEFAULT 1,  -- 1-5
    error_type VARCHAR(50),  -- conceptual, careless, misunderstanding, systematic
    concept_area VARCHAR(200),  -- Khái niệm cụ thể bị sai
    ai_analysis TEXT,  -- AI phân tích lỗi
    recommended_lessons TEXT,  -- JSON array of lesson_ids
    times_similar_wrong INT DEFAULT 0,  -- Bao nhiêu lần sai tương tự
    created_at DATETIME DEFAULT GETDATE(),
    analyzed_at DATETIME,
    INDEX idx_user_id (user_id),
    INDEX idx_topic_id (topic_id),
    INDEX idx_course_id (course_id),
    INDEX idx_error_type (error_type),
    INDEX idx_created_at (created_at)
);

-- Index tính năng
CREATE INDEX idx_incorrect_answer_user_course ON incorrect_answer_analysis(user_id, course_id);
CREATE INDEX idx_incorrect_answer_question ON incorrect_answer_analysis(question_id, user_id);

-- View để xem lỗi phổ biến
CREATE VIEW vw_common_mistakes AS
SELECT 
    c.course_id,
    c.course_name,
    t.topic_id,
    t.topic_name,
    iaa.error_type,
    COUNT(DISTINCT iaa.user_id) as affected_students,
    COUNT(iaa.analysis_id) as total_mistakes,
    CAST(COUNT(iaa.analysis_id) AS FLOAT) / COUNT(DISTINCT iaa.user_id) as avg_mistakes_per_student
FROM incorrect_answer_analysis iaa
JOIN topics t ON iaa.topic_id = t.topic_id
JOIN courses c ON iaa.course_id = c.course_id
GROUP BY c.course_id, c.course_name, t.topic_id, t.topic_name, iaa.error_type;

