from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, User, Course, Lesson, QuizQuestion, Quiz, Enrollment, QuizResult, Assignment
from functools import wraps
from datetime import datetime

bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# User Management
@bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'User deactivated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = True
        db.session.commit()
        
        return jsonify({'message': 'User activated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Course Management
@bp.route('/courses', methods=['POST'])
@admin_required
def create_course():
    try:
        data = request.get_json()
        course = Course(
            course_name=data.get('course_name'),
            description=data.get('description'),
            thumbnail_url=data.get('thumbnail_url'),
            instructor_id=data.get('instructor_id')
        )
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Course created successfully',
            'course': course.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/courses/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        data = request.get_json()
        if 'course_name' in data:
            course.course_name = data['course_name']
        if 'description' in data:
            course.description = data['description']
        if 'thumbnail_url' in data:
            course.thumbnail_url = data['thumbnail_url']
        if 'is_active' in data:
            course.is_active = data['is_active']
        
        course.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Course updated successfully',
            'course': course.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/courses/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({'message': 'Course deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Lesson Management
@bp.route('/lessons', methods=['POST'])
@admin_required
def create_lesson():
    try:
        data = request.get_json()
        lesson = Lesson(
            course_id=data.get('course_id'),
            lesson_title=data.get('lesson_title'),
            lesson_content=data.get('lesson_content'),
            lesson_order=data.get('lesson_order'),
            video_url=data.get('video_url'),
            duration_minutes=data.get('duration_minutes')
        )
        db.session.add(lesson)
        db.session.commit()
        
        return jsonify({
            'message': 'Lesson created successfully',
            'lesson': lesson.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/lessons/<int:lesson_id>', methods=['PUT'])
@admin_required
def update_lesson(lesson_id):
    try:
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        data = request.get_json()
        if 'lesson_title' in data:
            lesson.lesson_title = data['lesson_title']
        if 'lesson_content' in data:
            lesson.lesson_content = data['lesson_content']
        if 'lesson_order' in data:
            lesson.lesson_order = data['lesson_order']
        if 'video_url' in data:
            lesson.video_url = data['video_url']
        
        lesson.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Lesson updated successfully',
            'lesson': lesson.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/lessons/<int:lesson_id>', methods=['DELETE'])
@admin_required
def delete_lesson(lesson_id):
    try:
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        db.session.delete(lesson)
        db.session.commit()
        
        return jsonify({'message': 'Lesson deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Quiz Question Management
@bp.route('/questions', methods=['POST'])
@admin_required
def create_question():
    try:
        data = request.get_json()
        import json
        
        question = QuizQuestion(
            topic_id=data.get('topic_id'),
            course_id=data.get('course_id'),
            question_text=data.get('question_text'),
            question_type=data.get('question_type', 'multiple_choice'),
            options=json.dumps(data.get('options', [])) if isinstance(data.get('options'), list) else data.get('options'),
            correct_answer=data.get('correct_answer'),
            explanation=data.get('explanation'),
            difficulty_level=data.get('difficulty_level', 1)
        )
        db.session.add(question)
        db.session.commit()
        
        return jsonify({
            'message': 'Question created successfully',
            'question': question.to_dict(include_answer=True)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/questions/<int:question_id>', methods=['PUT'])
@admin_required
def update_question(question_id):
    try:
        question = QuizQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        data = request.get_json()
        import json
        
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'options' in data:
            question.options = json.dumps(data['options']) if isinstance(data['options'], list) else data['options']
        if 'correct_answer' in data:
            question.correct_answer = data['correct_answer']
        if 'explanation' in data:
            question.explanation = data['explanation']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Question updated successfully',
            'question': question.to_dict(include_answer=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/questions/<int:question_id>', methods=['DELETE'])
@admin_required
def delete_question(question_id):
    try:
        question = QuizQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({'message': 'Question deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Statistics
@bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("[ADMIN] Getting statistics...")
        
        total_users = User.query.count()
        logger.info(f"[ADMIN] Total users: {total_users}")
        
        total_courses = Course.query.count()
        logger.info(f"[ADMIN] Total courses: {total_courses}")
        
        total_enrollments = Enrollment.query.count()
        logger.info(f"[ADMIN] Total enrollments: {total_enrollments}")
        
        # Completion rates
        enrollments = Enrollment.query.all()
        logger.info(f"[ADMIN] Fetched {len(enrollments)} enrollments")
        
        completion_stats = {
            'total': len(enrollments),
            'completed': 0,
            'in_progress': 0,
            'not_started': 0
        }
        
        for enrollment in enrollments:
            progress = float(enrollment.progress_percentage) if enrollment.progress_percentage else 0
            if progress == 100:
                completion_stats['completed'] += 1
            elif progress > 0:
                completion_stats['in_progress'] += 1
            else:
                completion_stats['not_started'] += 1
        
        avg_completion_rate = (
            (completion_stats['completed'] / completion_stats['total'] * 100)
            if completion_stats['total'] > 0 else 0
        )
        
        response_data = {
            'users': {
                'total': total_users,
                'active': User.query.filter_by(is_active=True).count()
            },
            'courses': {
                'total': total_courses,
                'active': Course.query.filter_by(is_active=True).count()
            },
            'enrollments': total_enrollments,
            'completion': {
                'average_rate': avg_completion_rate,
                'details': completion_stats
            }
        }
        
        logger.info(f"[ADMIN] Returning statistics: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[ADMIN] Error getting statistics: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

