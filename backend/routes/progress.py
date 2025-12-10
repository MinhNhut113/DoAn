from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, Enrollment, LessonProgress, Lesson, QuizResult, Topic, LearningAnalytics, Quiz
from sqlalchemy import func

bp = Blueprint('progress', __name__)

@bp.route('/course/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course_progress(course_id):
    try:
        user_id = get_current_user_id()
        enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        
        if not enrollment:
            return jsonify({'error': 'Not enrolled in this course'}), 404
        
        # Get all lessons
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
        
        completed_count = 0
        total_time = 0
        lesson_details = []
        
        for lesson in lessons:
            progress = LessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson.lesson_id).first()
            is_completed = progress.is_completed if progress else False
            time_spent = progress.time_spent_minutes if progress else 0
            
            if is_completed:
                completed_count += 1
            total_time += time_spent
            
            lesson_details.append({
                'lesson_id': lesson.lesson_id,
                'lesson_title': lesson.lesson_title,
                'lesson_order': lesson.lesson_order,
                'is_completed': is_completed,
                'time_spent_minutes': time_spent
            })
        
        progress_percentage = float(enrollment.progress_percentage) if enrollment.progress_percentage else 0
        
        return jsonify({
            'course_id': course_id,
            'progress_percentage': progress_percentage,
            'total_lessons': len(lessons),
            'completed_lessons': completed_count,
            'total_time_spent_minutes': total_time,
            'lessons': lesson_details
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_learning_analytics():
    try:
        user_id = get_current_user_id()
        course_id = request.args.get('course_id', type=int)
        
        # Get quiz results by topic
        query = db.session.query(
            Topic.topic_id,
            Topic.topic_name,
            func.avg(QuizResult.score).label('avg_score'),
            func.count(QuizResult.result_id).label('quiz_count')
        ).join(Quiz, Quiz.topic_id == Topic.topic_id
        ).join(QuizResult, QuizResult.quiz_id == Quiz.quiz_id
        ).filter(QuizResult.user_id == user_id)
        
        if course_id:
            query = query.filter(Topic.course_id == course_id)
        
        topic_stats = query.group_by(Topic.topic_id, Topic.topic_name).all()
        
        analytics = []
        for topic_id, topic_name, avg_score, quiz_count in topic_stats:
            strength_score = float(avg_score) if avg_score else 0
            analytics.append({
                'topic_id': topic_id,
                'topic_name': topic_name,
                'average_score': strength_score,
                'quiz_count': quiz_count,
                'strength_level': 'Strong' if strength_score >= 80 else 'Good' if strength_score >= 60 else 'Needs improvement'
            })
        
        return jsonify(analytics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_current_user_id()
        
        # Get user enrollments
        enrollments = Enrollment.query.filter_by(user_id=user_id).all()
        total_courses = len(enrollments)
        
        # Calculate overall stats
        total_progress = 0
        for enrollment in enrollments:
            total_progress += float(enrollment.progress_percentage) if enrollment.progress_percentage else 0
        
        average_progress = (total_progress / total_courses) if total_courses > 0 else 0
        
        # Get recent quiz results
        recent_quizzes = QuizResult.query.filter_by(user_id=user_id).order_by(
            QuizResult.submitted_at.desc()
        ).limit(5).all()
        
        return jsonify({
            'total_courses': total_courses,
            'average_progress': average_progress,
            'recent_quizzes': [
                {
                    'quiz_id': q.quiz_id,
                    'score': float(q.score),
                    'submitted_at': q.submitted_at.isoformat() if q.submitted_at else None
                }
                for q in recent_quizzes
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

