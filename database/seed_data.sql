-- Sample data for testing (optional)

-- Insert sample topics
INSERT INTO topics (topic_name, description) VALUES
('Lập trình cơ bản', 'Các khái niệm cơ bản về lập trình'),
('Cơ sở dữ liệu', 'SQL và quản lý database'),
('Thuật toán', 'Các thuật toán và cấu trúc dữ liệu');

-- Insert sample course
INSERT INTO courses (course_name, description, instructor_id, is_active) VALUES
('Lập trình Python cơ bản', 'Khóa học giới thiệu về ngôn ngữ lập trình Python', NULL, 1);

-- Insert sample lessons
DECLARE @course_id INT = SCOPE_IDENTITY();
INSERT INTO lessons (course_id, lesson_title, lesson_content, lesson_order, duration_minutes) VALUES
(@course_id, 'Giới thiệu Python', 'Bài học đầu tiên về Python...', 1, 30),
(@course_id, 'Biến và kiểu dữ liệu', 'Tìm hiểu về biến và các kiểu dữ liệu trong Python', 2, 45),
(@course_id, 'Cấu trúc điều khiển', 'If, for, while trong Python', 3, 45);

-- Insert sample quiz questions
DECLARE @topic_id INT = (SELECT TOP 1 topic_id FROM topics);
DECLARE @q1 INT, @q2 INT, @q3 INT;

INSERT INTO quiz_questions (topic_id, course_id, question_text, options, correct_answer, explanation, difficulty_level)
VALUES
(@topic_id, @course_id, 'Python là ngôn ngữ lập trình gì?', 
 '["Scripting", "Compiled", "Machine code", "Assembly"]', 0,
 'Python là ngôn ngữ lập trình scripting', 1);

SET @q1 = SCOPE_IDENTITY();

INSERT INTO quiz_questions (topic_id, course_id, question_text, options, correct_answer, explanation, difficulty_level)
VALUES
(@topic_id, @course_id, 'Kiểu dữ liệu nào sau đây là mutable trong Python?',
 '["List", "String", "Tuple", "None"]', 0,
 'List là kiểu dữ liệu mutable, có thể thay đổi sau khi tạo', 2);

SET @q2 = SCOPE_IDENTITY();

INSERT INTO quiz_questions (topic_id, course_id, question_text, options, correct_answer, explanation, difficulty_level)
VALUES
(@topic_id, @course_id, 'Vòng lặp nào sau đây chạy ít nhất 1 lần?',
 '["for", "while", "do-while", "Tất cả đều đúng"]', 2,
 'Python không có do-while, nhưng câu hỏi này kiểm tra kiến thức chung', 2);

SET @q3 = SCOPE_IDENTITY();

-- Create a quiz
INSERT INTO quizzes (quiz_name, course_id, topic_id, time_limit_minutes, passing_score)
VALUES ('Bài kiểm tra Python cơ bản', @course_id, @topic_id, 30, 60);

DECLARE @quiz_id INT = SCOPE_IDENTITY();

-- Add questions to quiz
INSERT INTO quiz_question_mapping (quiz_id, question_id, question_order)
VALUES
(@quiz_id, @q1, 1),
(@quiz_id, @q2, 2),
(@quiz_id, @q3, 3);

