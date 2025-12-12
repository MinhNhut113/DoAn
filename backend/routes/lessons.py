from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, Lesson, LessonProgress, Enrollment, User
from datetime import datetime
from models import Quiz, QuizQuestion, QuizQuestionMapping

bp = Blueprint('lessons', __name__)

@bp.route('/course/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course_lessons(course_id):
    try:
        user_id = get_current_user_id()
        
        # Allow access if user is admin or enrolled in the course
        user = User.query.get(user_id)
        is_admin = user and user.role == 'admin'
        
        if not is_admin:
            enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
            if not enrollment:
                return jsonify({'error': 'Not enrolled in this course'}), 403
        
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
        
        lesson_list = []
        for lesson in lessons:
            lesson_data = lesson.to_dict()
            if not is_admin:
                progress = LessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson.lesson_id).first()
                lesson_data['is_completed'] = progress.is_completed if progress else False
                lesson_data['time_spent_minutes'] = progress.time_spent_minutes if progress else 0
            else:
                lesson_data['is_completed'] = False
                lesson_data['time_spent_minutes'] = 0
            lesson_list.append(lesson_data)
        
        return jsonify(lesson_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_lesson(lesson_id):
    try:
        user_id = get_current_user_id()
        lesson = Lesson.query.get(lesson_id)
        
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        # Allow access if user is admin or enrolled in the course
        user = User.query.get(user_id)
        is_admin = user and user.role == 'admin'
        
        if not is_admin:
            enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=lesson.course_id).first()
            if not enrollment:
                return jsonify({'error': 'Not enrolled in this course'}), 403
        
        lesson_data = lesson.to_dict()
        
        # Only track progress for non-admin users
        if not is_admin:
            progress = LessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
            
            if progress:
                progress.last_accessed = datetime.utcnow()
            else:
                progress = LessonProgress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    last_accessed=datetime.utcnow()
                )
                db.session.add(progress)
            
            db.session.commit()
            
            lesson_data['is_completed'] = progress.is_completed
            lesson_data['time_spent_minutes'] = progress.time_spent_minutes
            lesson_data['last_accessed'] = progress.last_accessed.isoformat() if progress.last_accessed else None
        else:
            # For admins viewing lesson, don't include progress data
            lesson_data['is_completed'] = False
            lesson_data['time_spent_minutes'] = 0
            lesson_data['last_accessed'] = None
        
        return jsonify(lesson_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:lesson_id>/quiz', methods=['GET'])
@jwt_required()
def get_lesson_quiz(lesson_id):
    """Return the quiz associated with a lesson (if any)"""
    try:
        user_id = get_current_user_id()
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404

        # ensure user has access (admin or enrolled)
        user = User.query.get(user_id)
        is_admin = user and user.role == 'admin'
        if not is_admin:
            enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=lesson.course_id).first()
            if not enrollment:
                return jsonify({'error': 'Not enrolled in this course'}), 403

        # Find quiz by naming convention created by AI: LessonQuiz:{lesson_id}:
        prefix = f"LessonQuiz:{lesson_id}:"
        quiz = Quiz.query.filter(Quiz.quiz_name.startswith(prefix)).first()
        if not quiz:
            return jsonify({'message': 'No quiz available for this lesson yet'}), 200

        # Load questions
        mappings = QuizQuestionMapping.query.filter_by(quiz_id=quiz.quiz_id).order_by(QuizQuestionMapping.question_order).all()
        questions = []
        for m in mappings:
            q = QuizQuestion.query.get(m.question_id)
            if not q: continue
            try:
                opts = q.options
                import json as _json
                opts_parsed = _json.loads(opts) if opts else []
            except Exception:
                opts_parsed = q.options
            questions.append({
                'question_id': q.question_id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'options': opts_parsed,
                'difficulty_level': q.difficulty_level
            })

        return jsonify({
            'quiz': quiz.to_dict(),
            'questions': questions
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:lesson_id>/complete', methods=['POST'])
@jwt_required()
def complete_lesson(lesson_id):
    try:
        user_id = get_current_user_id()
        lesson = Lesson.query.get(lesson_id)
        
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        progress = LessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
        
        if not progress:
            progress = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                is_completed=True,
                completion_date=datetime.utcnow()
            )
            db.session.add(progress)
        else:
            progress.is_completed = True
            if not progress.completion_date:
                progress.completion_date = datetime.utcnow()
        
        # Update course progress
        enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=lesson.course_id).first()
        if enrollment:
            total_lessons = Lesson.query.filter_by(course_id=lesson.course_id).count()
            # Get all lessons for this course
            all_lessons = Lesson.query.filter_by(course_id=lesson.course_id).all()
            lesson_ids = [l.lesson_id for l in all_lessons]
            completed_progress = LessonProgress.query.filter(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id.in_(lesson_ids),
                LessonProgress.is_completed == True
            ).count()
            
            enrollment.progress_percentage = (completed_progress / total_lessons * 100) if total_lessons > 0 else 0
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lesson marked as completed',
            'progress': {
                'is_completed': progress.is_completed,
                'completion_date': progress.completion_date.isoformat() if progress.completion_date else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

