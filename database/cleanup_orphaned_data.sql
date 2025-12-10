-- Script để xóa dữ liệu orphaned sau khi bỏ CASCADE
-- Chạy script này định kỳ để dọn dẹp dữ liệu không còn tham chiếu

-- Xóa quiz_questions không còn thuộc course nào (nếu course đã bị xóa)
DELETE FROM quiz_questions 
WHERE course_id IS NOT NULL 
  AND course_id NOT IN (SELECT course_id FROM courses);

-- Xóa quiz_question_mapping có quiz đã bị xóa
DELETE FROM quiz_question_mapping 
WHERE quiz_id NOT IN (SELECT quiz_id FROM quizzes);

-- Xóa quiz_question_mapping có question đã bị xóa
DELETE FROM quiz_question_mapping 
WHERE question_id NOT IN (SELECT question_id FROM quiz_questions);

-- Xóa quiz_answers có result đã bị xóa
DELETE FROM quiz_answers 
WHERE result_id NOT IN (SELECT result_id FROM quiz_results);

-- Xóa quiz_answers có question đã bị xóa
DELETE FROM quiz_answers 
WHERE question_id NOT IN (SELECT question_id FROM quiz_questions);

PRINT 'Đã dọn dẹp dữ liệu orphaned!';

