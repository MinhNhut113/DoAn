from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(500))
    role = db.Column(db.String(20), default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Course(db.Model):
    __tablename__ = 'courses'
    
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(500))
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'description': self.description,
            'thumbnail_url': self.thumbnail_url,
            'instructor_id': self.instructor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    lesson_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    lesson_content = db.Column(db.Text)
    lesson_order = db.Column(db.Integer, nullable=False)
    video_url = db.Column(db.String(500))
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'lesson_id': self.lesson_id,
            'course_id': self.course_id,
            'lesson_title': self.lesson_title,
            'lesson_content': self.lesson_content,
            'lesson_order': self.lesson_order,
            'video_url': self.video_url,
            'duration_minutes': self.duration_minutes
        }

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    enrollment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress_percentage = db.Column(db.Numeric(5, 2), default=0)
    last_accessed = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id'),)
    
    def to_dict(self):
        return {
            'enrollment_id': self.enrollment_id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'progress_percentage': float(self.progress_percentage) if self.progress_percentage else 0,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }

class LessonProgress(db.Model):
    __tablename__ = 'lesson_progress'
    
    progress_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime)
    time_spent_minutes = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    question_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')
    options = db.Column(db.Text)  # JSON string
    correct_answer = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text)
    difficulty_level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, include_answer=False):
        data = {
            'question_id': self.question_id,
            'topic_id': self.topic_id,
            'course_id': self.course_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'options': self.options,
            'explanation': self.explanation,
            'difficulty_level': self.difficulty_level
        }
        if include_answer:
            data['correct_answer'] = self.correct_answer
        return data

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    quiz_id = db.Column(db.Integer, primary_key=True)
    quiz_name = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'))
    time_limit_minutes = db.Column(db.Integer)
    passing_score = db.Column(db.Integer, default=60)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'quiz_id': self.quiz_id,
            'quiz_name': self.quiz_name,
            'course_id': self.course_id,
            'topic_id': self.topic_id,
            'time_limit_minutes': self.time_limit_minutes,
            'passing_score': self.passing_score
        }

class QuizQuestionMapping(db.Model):
    __tablename__ = 'quiz_question_mapping'
    
    mapping_id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.question_id'), nullable=False)
    question_order = db.Column(db.Integer)
    
    __table_args__ = (db.UniqueConstraint('quiz_id', 'question_id'),)

class QuizAnswer(db.Model):
    __tablename__ = 'quiz_answers'
    
    answer_id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('quiz_results.result_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.question_id'), nullable=False)
    selected_answer = db.Column(db.Integer)
    is_correct = db.Column(db.Boolean)
    time_spent_seconds = db.Column(db.Integer)

class QuizResult(db.Model):
    __tablename__ = 'quiz_results'
    
    result_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id'), nullable=False)
    score = db.Column(db.Numeric(5, 2))
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    time_taken_minutes = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'result_id': self.result_id,
            'user_id': self.user_id,
            'quiz_id': self.quiz_id,
            'score': float(self.score) if self.score else 0,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'time_taken_minutes': self.time_taken_minutes,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }

class Topic(db.Model):
    __tablename__ = 'topics'
    
    topic_id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    description = db.Column(db.String(500))
    
    def to_dict(self):
        return {
            'topic_id': self.topic_id,
            'topic_name': self.topic_name,
            'course_id': self.course_id,
            'description': self.description
        }

class LearningAnalytics(db.Model):
    __tablename__ = 'learning_analytics'
    
    analytics_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    strength_score = db.Column(db.Numeric(5, 2))
    weakness_score = db.Column(db.Numeric(5, 2))
    recommendation = db.Column(db.Text)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

class AIRecommendation(db.Model):
    __tablename__ = 'ai_recommendations'
    
    recommendation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    recommendation_type = db.Column(db.String(50))
    content_type = db.Column(db.String(50))
    content_id = db.Column(db.Integer)
    priority = db.Column(db.Integer, default=1)
    reason = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_viewed = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    notification_type = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    assignment_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'))
    assignment_title = db.Column(db.String(200), nullable=False)
    assignment_description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'assignment_id': self.assignment_id,
            'course_id': self.course_id,
            'lesson_id': self.lesson_id,
            'assignment_title': self.assignment_title,
            'assignment_description': self.assignment_description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'max_score': self.max_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'
    
    submission_id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.assignment_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    submission_content = db.Column(db.Text)
    file_url = db.Column(db.String(500))
    score = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    graded_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'submission_id': self.submission_id,
            'assignment_id': self.assignment_id,
            'user_id': self.user_id,
            'submission_content': self.submission_content,
            'file_url': self.file_url,
            'score': float(self.score) if self.score else None,
            'feedback': self.feedback,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None
        }

class AIChatMessage(db.Model):
    """Model for storing AI chatbot conversation messages"""
    __tablename__ = 'ai_chat_messages'
    
    message_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    conversation_id = db.Column(db.String(100))  # To group related messages
    message_type = db.Column(db.String(50), default='question')  # question, clarification, explanation
    helpful_rating = db.Column(db.Integer)  # 1-5 rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'lesson_id': self.lesson_id,
            'course_id': self.course_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'conversation_id': self.conversation_id,
            'message_type': self.message_type,
            'helpful_rating': self.helpful_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AIGeneratedQuestion(db.Model):
    """Model for AI-generated quiz questions"""
    __tablename__ = 'ai_generated_questions'
    
    gen_question_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'))
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')  # multiple_choice, true_false, short_answer
    options = db.Column(db.Text)  # JSON format for multiple choice
    correct_answer = db.Column(db.Integer)  # Index of correct option or answer
    explanation = db.Column(db.Text)
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5 difficulty
    generated_by = db.Column(db.String(50), default='openai')  # Which AI service generated it
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # Admin who approved
    approval_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    times_used = db.Column(db.Integer, default=0)  # Track usage statistics
    
    def to_dict(self, include_answer=False):
        data = {
            'gen_question_id': self.gen_question_id,
            'topic_id': self.topic_id,
            'course_id': self.course_id,
            'lesson_id': self.lesson_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'options': self.options,
            'explanation': self.explanation,
            'difficulty_level': self.difficulty_level,
            'generated_by': self.generated_by,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_answer:
            data['correct_answer'] = self.correct_answer
        return data

class GenerationRequest(db.Model):
    """Model to track AI generation requests and history"""
    __tablename__ = 'generation_requests'
    
    request_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # 'question_generation', 'chat', 'recommendation'
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'))
    input_prompt = db.Column(db.Text)
    request_params = db.Column(db.Text)  # JSON format for parameters
    status = db.Column(db.String(50), default='processing')  # processing, completed, failed
    result_ids = db.Column(db.Text)  # JSON format: IDs of generated items
    error_message = db.Column(db.Text)
    processing_time_seconds = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'request_type': self.request_type,
            'topic_id': self.topic_id,
            'course_id': self.course_id,
            'lesson_id': self.lesson_id,
            'status': self.status,
            'processing_time_seconds': self.processing_time_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class IncorrectAnswerAnalysis(db.Model):
    """Model để lưu phân tích những câu trả lời sai"""
    __tablename__ = 'incorrect_answer_analysis'
    
    analysis_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.question_id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'))
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id'))
    question_text = db.Column(db.Text, nullable=False)
    user_answer = db.Column(db.Integer)  # Index of user's answer
    correct_answer = db.Column(db.Integer, nullable=False)
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5
    error_type = db.Column(db.String(50))  # conceptual, careless, misunderstanding
    concept_area = db.Column(db.String(200))  # Khái niệm cụ thể bị sai
    ai_analysis = db.Column(db.Text)  # AI phân tích lỗi
    recommended_lessons = db.Column(db.Text)  # JSON array of lesson_ids
    times_similar_wrong = db.Column(db.Integer, default=0)  # Bao nhiêu lần sai tương tự
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyzed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        recommended = []
        if self.recommended_lessons:
            try:
                recommended = json.loads(self.recommended_lessons)
            except Exception as e:
                # If parsing fails, return empty list and log at debug level
                import logging
                logging.getLogger(__name__).debug(f"Failed to parse recommended_lessons JSON: {e}")
        
        return {
            'analysis_id': self.analysis_id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'topic_id': self.topic_id,
            'course_id': self.course_id,
            'lesson_id': self.lesson_id,
            'quiz_id': self.quiz_id,
            'question_text': self.question_text,
            'user_answer': self.user_answer,
            'correct_answer': self.correct_answer,
            'difficulty_level': self.difficulty_level,
            'error_type': self.error_type,
            'concept_area': self.concept_area,
            'ai_analysis': self.ai_analysis,
            'recommended_lessons': recommended,
            'times_similar_wrong': self.times_similar_wrong,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }



