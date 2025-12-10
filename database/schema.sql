-- Database Schema cho Hệ Thống Học Trực Tuyến với AI

-- Xóa các bảng nếu đã tồn tại (theo thứ tự ngược lại để tránh lỗi foreign key)
IF OBJECT_ID('assignment_submissions', 'U') IS NOT NULL DROP TABLE assignment_submissions;
IF OBJECT_ID('assignments', 'U') IS NOT NULL DROP TABLE assignments;
IF OBJECT_ID('notifications', 'U') IS NOT NULL DROP TABLE notifications;
IF OBJECT_ID('ai_recommendations', 'U') IS NOT NULL DROP TABLE ai_recommendations;
IF OBJECT_ID('learning_analytics', 'U') IS NOT NULL DROP TABLE learning_analytics;
IF OBJECT_ID('quiz_answers', 'U') IS NOT NULL DROP TABLE quiz_answers;
IF OBJECT_ID('quiz_results', 'U') IS NOT NULL DROP TABLE quiz_results;
IF OBJECT_ID('quiz_question_mapping', 'U') IS NOT NULL DROP TABLE quiz_question_mapping;
IF OBJECT_ID('quizzes', 'U') IS NOT NULL DROP TABLE quizzes;
IF OBJECT_ID('quiz_questions', 'U') IS NOT NULL DROP TABLE quiz_questions;
IF OBJECT_ID('topics', 'U') IS NOT NULL DROP TABLE topics;
IF OBJECT_ID('lesson_progress', 'U') IS NOT NULL DROP TABLE lesson_progress;
IF OBJECT_ID('enrollments', 'U') IS NOT NULL DROP TABLE enrollments;
IF OBJECT_ID('learning_materials', 'U') IS NOT NULL DROP TABLE learning_materials;
IF OBJECT_ID('lessons', 'U') IS NOT NULL DROP TABLE lessons;
IF OBJECT_ID('courses', 'U') IS NOT NULL DROP TABLE courses;
IF OBJECT_ID('learning_goals', 'U') IS NOT NULL DROP TABLE learning_goals;
IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;

-- Bảng Người Dùng
CREATE TABLE users (
    user_id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(50) UNIQUE NOT NULL,
    email NVARCHAR(100) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    full_name NVARCHAR(100) NOT NULL,
    avatar_url NVARCHAR(500),
    role NVARCHAR(20) NOT NULL DEFAULT 'student', -- 'student', 'admin'
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- Bảng Mục Tiêu Học Tập
CREATE TABLE learning_goals (
    goal_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    goal_description NVARCHAR(500),
    target_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Bảng Khóa Học
CREATE TABLE courses (
    course_id INT PRIMARY KEY IDENTITY(1,1),
    course_name NVARCHAR(200) NOT NULL,
    description NVARCHAR(MAX),
    thumbnail_url NVARCHAR(500),
    instructor_id INT,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    is_active BIT DEFAULT 1,
    FOREIGN KEY (instructor_id) REFERENCES users(user_id)
);

-- Bảng Bài Giảng
CREATE TABLE lessons (
    lesson_id INT PRIMARY KEY IDENTITY(1,1),
    course_id INT NOT NULL,
    lesson_title NVARCHAR(200) NOT NULL,
    lesson_content NVARCHAR(MAX),
    lesson_order INT NOT NULL,
    video_url NVARCHAR(500),
    duration_minutes INT,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

-- Bảng Tài Liệu Học Tập
CREATE TABLE learning_materials (
    material_id INT PRIMARY KEY IDENTITY(1,1),
    lesson_id INT NOT NULL,
    material_name NVARCHAR(200),
    material_url NVARCHAR(500),
    material_type NVARCHAR(50), -- 'pdf', 'video', 'link'
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id) ON DELETE CASCADE
);

-- Bảng Đăng Ký Khóa Học
CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    enrolled_at DATETIME DEFAULT GETDATE(),
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    last_accessed DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE(user_id, course_id)
);

-- Bảng Tiến Độ Học Tập
CREATE TABLE lesson_progress (
    progress_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    lesson_id INT NOT NULL,
    is_completed BIT DEFAULT 0,
    completion_date DATETIME,
    time_spent_minutes INT DEFAULT 0,
    last_accessed DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    UNIQUE(user_id, lesson_id)
);

-- Bảng Chủ Đề
CREATE TABLE topics (
    topic_id INT PRIMARY KEY IDENTITY(1,1),
    topic_name NVARCHAR(100) NOT NULL,
    course_id INT,
    description NVARCHAR(500),
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

CREATE TABLE quiz_questions (
    question_id INT PRIMARY KEY IDENTITY(1,1),
    topic_id INT,
    course_id INT,
    question_text NVARCHAR(MAX) NOT NULL,
    question_type NVARCHAR(20) DEFAULT 'multiple_choice', -- 'multiple_choice', 'true_false'
    options NVARCHAR(MAX), -- JSON string: ["option1", "option2", "option3", "option4"]
    correct_answer INT NOT NULL, -- Index of correct option
    explanation NVARCHAR(MAX),
    difficulty_level INT DEFAULT 1, -- 1: Easy, 2: Medium, 3: Hard
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Bảng Bài Kiểm Tra
CREATE TABLE quizzes (
    quiz_id INT PRIMARY KEY IDENTITY(1,1),
    quiz_name NVARCHAR(200) NOT NULL,
    course_id INT,
    topic_id INT,
    time_limit_minutes INT,
    passing_score INT DEFAULT 60,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
);

-- Bảng Câu Hỏi trong Bài Kiểm Tra
CREATE TABLE quiz_question_mapping (
    mapping_id INT PRIMARY KEY IDENTITY(1,1),
    quiz_id INT NOT NULL,
    question_id INT NOT NULL,
    question_order INT,
    CONSTRAINT FK_quiz_question_mapping_quiz FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    CONSTRAINT FK_quiz_question_mapping_question FOREIGN KEY (question_id) REFERENCES quiz_questions(question_id) ON DELETE NO ACTION, 
    UNIQUE(quiz_id, question_id)
);

-- Bảng Kết Quả Bài Kiểm Tra
CREATE TABLE quiz_results (
    result_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    quiz_id INT NOT NULL,
    score DECIMAL(5,2),
    total_questions INT,
    correct_answers INT,
    time_taken_minutes INT,
    submitted_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE
);

-- Bảng Chi Tiết Câu Trả Lời
CREATE TABLE quiz_answers (
    answer_id INT PRIMARY KEY IDENTITY(1,1),
    result_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_answer INT,
    is_correct BIT,
    time_spent_seconds INT,
    CONSTRAINT FK_quiz_answers_result FOREIGN KEY (result_id) REFERENCES quiz_results(result_id) ON DELETE CASCADE,
    CONSTRAINT FK_quiz_answers_question FOREIGN KEY (question_id) REFERENCES quiz_questions(question_id)
);

-- Bảng Phân Tích Học Tập (AI)
CREATE TABLE learning_analytics (
    analytics_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    topic_id INT,
    course_id INT,
    strength_score DECIMAL(5,2), -- 0-100
    weakness_score DECIMAL(5,2), -- 0-100
    recommendation NVARCHAR(MAX), -- AI generated recommendations
    analyzed_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Bảng Gợi Ý AI
CREATE TABLE ai_recommendations (
    recommendation_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    recommendation_type NVARCHAR(50), -- 'lesson_order', 'topic_review', 'related_content'
    content_type NVARCHAR(50), -- 'lesson', 'course', 'article'
    content_id INT, -- ID of lesson, course, or article
    priority INT DEFAULT 1, -- Higher = more important
    reason NVARCHAR(500), -- Why this is recommended
    created_at DATETIME DEFAULT GETDATE(),
    is_viewed BIT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Bảng Thông Báo
CREATE TABLE notifications (
    notification_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    title NVARCHAR(200),
    message NVARCHAR(MAX),
    notification_type NVARCHAR(50), -- 'course_update', 'quiz_reminder', 'achievement'
    is_read BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Bảng Bài Tập
CREATE TABLE assignments (
    assignment_id INT PRIMARY KEY IDENTITY(1,1),
    course_id INT NOT NULL,
    lesson_id INT,
    assignment_title NVARCHAR(200) NOT NULL,
    assignment_description NVARCHAR(MAX),
    due_date DATETIME,
    max_score INT DEFAULT 100,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id)
);

-- Bảng Kết Quả Bài Tập
CREATE TABLE assignment_submissions (
    submission_id INT PRIMARY KEY IDENTITY(1,1),
    assignment_id INT NOT NULL,
    user_id INT NOT NULL,
    submission_content NVARCHAR(MAX),
    file_url NVARCHAR(500),
    score DECIMAL(5,2),
    feedback NVARCHAR(MAX),
    submitted_at DATETIME DEFAULT GETDATE(),
    graded_at DATETIME,
    FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_lesson_progress_user ON lesson_progress(user_id);
CREATE INDEX idx_quiz_results_user ON quiz_results(user_id);
CREATE INDEX idx_quiz_results_quiz ON quiz_results(quiz_id);
CREATE INDEX idx_learning_analytics_user ON learning_analytics(user_id);
CREATE INDEX idx_ai_recommendations_user ON ai_recommendations(user_id);




