-- Script sửa lỗi Foreign Key
-- Chạy script này nếu gặp lỗi với foreign key constraints

-- Xóa tất cả các foreign key constraints có vấn đề
IF OBJECT_ID('FK__quiz_ques__quest__73BA3083', 'F') IS NOT NULL
    ALTER TABLE quiz_answers DROP CONSTRAINT FK__quiz_ques__quest__73BA3083;

IF OBJECT_ID('FK__quiz_ques__quest', 'F') IS NOT NULL
    ALTER TABLE quiz_answers DROP CONSTRAINT FK__quiz_ques__quest;

-- Xóa các constraint tự động được tạo sai
DECLARE @sql NVARCHAR(MAX) = ''
SELECT @sql += 'ALTER TABLE ' + OBJECT_SCHEMA_NAME(parent_object_id) + '.' + OBJECT_NAME(parent_object_id) 
               + ' DROP CONSTRAINT ' + name + ';' + CHAR(13)
FROM sys.foreign_keys
WHERE OBJECT_NAME(referenced_object_id) = 'questions' 
   OR name LIKE '%question%'
   OR name LIKE '%FK__quiz%'

EXEC sp_executesql @sql;

-- Tạo lại constraint đúng
IF OBJECT_ID('quiz_answers', 'U') IS NOT NULL 
    AND OBJECT_ID('quiz_questions', 'U') IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys 
                   WHERE name = 'FK_quiz_answers_question')
    BEGIN
        ALTER TABLE quiz_answers
        ADD CONSTRAINT FK_quiz_answers_question 
        FOREIGN KEY (question_id) REFERENCES quiz_questions(question_id);
    END
END

PRINT 'Đã sửa xong các foreign key constraints!';

