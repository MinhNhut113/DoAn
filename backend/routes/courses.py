from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, Course, Enrollment, Lesson, LessonProgress
from datetime import datetime

bp = Blueprint('courses', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def get_courses():
    try:
        user_id = get_current_user_id()
        enrolled_only = request.args.get('enrolled_only', 'false').lower() == 'true'
        
        if enrolled_only:
            enrollments = Enrollment.query.filter_by(user_id=user_id).all()
            course_ids = [e.course_id for e in enrollments]
            courses = Course.query.filter(Course.course_id.in_(course_ids)).filter_by(is_active=True).all()
        else:
            courses = Course.query.filter_by(is_active=True).all()
        
        course_list = []
        for course in courses:
            course_data = course.to_dict()
            enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course.course_id).first()
            course_data['is_enrolled'] = enrollment is not None
            if enrollment:
                course_data['progress_percentage'] = float(enrollment.progress_percentage) if enrollment.progress_percentage else 0
            course_list.append(course_data)
        
        return jsonify(course_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    try:
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        course_data = course.to_dict()
        
        # Get lessons
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
        course_data['lessons'] = [lesson.to_dict() for lesson in lessons]
        
        # Get enrollment info
        user_id = get_current_user_id()
        enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if enrollment:
            course_data['is_enrolled'] = True
            course_data['progress_percentage'] = float(enrollment.progress_percentage) if enrollment.progress_percentage else 0
        else:
            course_data['is_enrolled'] = False
            course_data['progress_percentage'] = 0
        
        return jsonify(course_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    try:
        user_id = get_current_user_id()
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        existing_enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if existing_enrollment:
            return jsonify({'error': 'Already enrolled in this course'}), 400
        
        enrollment = Enrollment(
            user_id=user_id,
            course_id=course_id
        )
        db.session.add(enrollment)
        db.session.commit()
        
        return jsonify({
            'message': 'Enrolled successfully',
            'enrollment': enrollment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

