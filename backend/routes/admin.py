from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import (
    db,
    User,
    Course,
    Lesson,
    QuizQuestion,
    Quiz,
    QuizQuestionMapping,
    AIGeneratedQuestion,
    GenerationRequest,
    Enrollment,
    QuizResult,
    Assignment,
    Notification,
)
from functools import wraps
from datetime import datetime
import json
import logging
import re
from ai_models.ai_service import get_ai_service

bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)


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


def generate_quiz_for_lesson(lesson_id: int, num_questions: int = 5) -> int:
    """Generate a multiple-choice quiz for a lesson using AI and save as a Quiz with mappings.

    Returns the created quiz_id.
    Raises RuntimeError/ValueError on failures.
    """
    ai = get_ai_service()
    lesson = Lesson.query.get(lesson_id)

    if not lesson:
        raise ValueError('Lesson not found')

    # Build a stricter prompt for AI: extract key points and create one MC question per key point
    prompt = f"""
Bạn là một trợ lý tạo câu hỏi kiểm tra (quiz) cho bài giảng. Nhiệm vụ: 1) Rút ra {num_questions} điểm chính (key points) từ bài học; 2) Sinh chính xác MỘT câu hỏi Multiple Choice cho mỗi điểm chính.

Yêu cầu định dạng đầu ra (CHÍNH XÁC JSON, KHÔNG THÊM VĂN BẢN):
Trả về một JSON array gồm {num_questions} objects. Mỗi object phải có các trường:
    - key_point: chuỗi ngắn mô tả điểm chính (10-30 từ)
    - question_text: chuỗi (nội dung câu hỏi liên quan trực tiếp tới key_point)
    - options: mảng các chuỗi (3 hoặc 4 lựa chọn)
    - correct_answer: số nguyên (index bắt đầu từ 0)
    - difficulty_level: số nguyên 1-5 (tùy chọn)
    - explanation: chuỗi ngắn (tùy chọn) giải thích tại sao đáp án đúng

Ví dụ hợp lệ (2 phần tử):
[
    {{"key_point":"Thẻ <a> dùng để tạo liên kết","question_text":"Thẻ HTML nào dùng để tạo liên kết?","options":["<a>","<p>","<div>"],"correct_answer":0}},
    {{"key_point":"Thẻ <h1> là tiêu đề lớn nhất","question_text":"Thẻ nào thường dùng cho tiêu đề lớn nhất?","options":["<h1>","<h3>","<span>"],"correct_answer":0}}
]

Bài học (title và nội dung):
Title: {lesson.lesson_title}
Content: {lesson.lesson_content or ''}

Trả về CHÍNH XÁC JSON array gồm {num_questions} phần tử, mỗi phần tử chứa `key_point` và một câu hỏi tương ứng.
"""

    raw = ai.generate_response(prompt)
    if not raw:
        raise RuntimeError('AI returned no response')

    raw_response = raw  # preserve for auditing

    # Try parse JSON robustly
    questions = None
    try:
        questions = json.loads(raw)
    except Exception:
        # Try to extract the first JSON array substring (more robust)
        m = re.search(r"\[\s*\{.*\}\s*\]", raw, re.DOTALL)
        if m:
            try:
                questions = json.loads(m.group())
            except Exception:
                # Attempt to balance braces heuristically
                start = raw.find('[')
                end = raw.rfind(']')
                if start != -1 and end != -1 and end > start:
                    try:
                        questions = json.loads(raw[start:end+1])
                    except Exception:
                        questions = None
        if questions is None:
            raise RuntimeError('Failed to parse JSON from AI response')

    # Validate and normalize questions (expecting key_point present)
    clean_questions = []
    for i, q in enumerate(questions[:num_questions]):
        if not isinstance(q, dict):
            continue

        key_point = q.get('key_point') or q.get('point') or ''
        qt = q.get('question_text') or q.get('question') or ''
        opts = q.get('options') or []

        # If options are a string (comma separated), try split
        if isinstance(opts, str):
            opts = [o.strip() for o in opts.split(',') if o.strip()]

        if not isinstance(opts, list):
            opts = []

        # Ensure at least 2 options
        if len(opts) < 2:
            continue

        # Determine correct answer index
        corr = q.get('correct_answer')
        corr_idx = 0
        if isinstance(corr, str):
            corr_str = corr.strip()
            if len(corr_str) == 1 and corr_str.isalpha():
                corr_idx = ord(corr_str.upper()) - ord('A')
            else:
                try:
                    corr_idx = int(corr_str)
                except Exception:
                    corr_idx = 0
        else:
            try:
                corr_idx = int(corr) if corr is not None else 0
            except Exception:
                corr_idx = 0

        if corr_idx < 0 or corr_idx >= len(opts):
            corr_idx = 0

        difficulty = q.get('difficulty_level') or q.get('difficulty') or 1
        try:
            difficulty = int(difficulty)
        except Exception:
            difficulty = 1

        explanation = q.get('explanation') or q.get('explain') or None

        clean_questions.append({
            'key_point': key_point,
            'question_text': qt,
            'options': opts,
            'correct_answer': corr_idx,
            'difficulty_level': max(1, min(5, difficulty)),
            'explanation': explanation
        })

    if len(clean_questions) == 0:
        raise RuntimeError('No valid questions parsed from AI response')

    # Create a Quiz for this lesson (name includes lesson id for lookup)
    quiz_name = f"LessonQuiz:{lesson.lesson_id}:{(lesson.lesson_title or '')[:80]}"
    quiz = Quiz(quiz_name=quiz_name, course_id=lesson.course_id, topic_id=None)
    db.session.add(quiz)
    db.session.commit()

    created_question_ids = []
    order = 1
    for q in clean_questions[:num_questions]:
        qq = QuizQuestion(
            topic_id=None,
            course_id=lesson.course_id,
            question_text=q['question_text'],
            question_type='multiple_choice',
            options=json.dumps(q['options']),
            correct_answer=int(q['correct_answer']),
            explanation=q.get('explanation'),
            difficulty_level=int(q.get('difficulty_level', 1))
        )
        db.session.add(qq)
        db.session.commit()

        mapping = QuizQuestionMapping(quiz_id=quiz.quiz_id, question_id=qq.question_id, question_order=order)
        db.session.add(mapping)
        db.session.commit()

        created_question_ids.append(qq.question_id)
        order += 1

    # Record generation request including raw response for auditing
    try:
        gen = GenerationRequest(
            user_id=None,
            request_type='question_generation',
            topic_id=None,
            course_id=lesson.course_id,
            lesson_id=lesson.lesson_id,
            input_prompt=prompt,
            request_params=json.dumps({'num_questions': num_questions}),
            status='completed',
            result_ids=json.dumps({'quiz_id': quiz.quiz_id, 'question_ids': created_question_ids}),
            error_message=None,
            processing_time_seconds=0.0,
            completed_at=datetime.utcnow()
        )
        # save raw response into error_message field if necessary (or extend model)
        try:
            gen.error_message = f"AI raw response: {raw_response[:2000]}"
        except Exception as e:
            logger.debug(f"[Admin] Failed to store raw response: {e}")
        db.session.add(gen)
        db.session.commit()
    except Exception as e:
        logger.error(f"[Admin] Error creating generation request: {e}")
        db.session.rollback()

    return quiz.quiz_id


# User Management
@bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        logger.exception("Failed to fetch users")
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
        logger.exception("Failed to deactivate user")
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
        logger.exception("Failed to activate user")
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
        logger.exception("Failed to delete user")
        return jsonify({'error': str(e)}), 500


@bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}

        role = data.get('role')
        if role:
            if role not in ('student', 'instructor', 'admin'):
                return jsonify({'error': 'Invalid role'}), 400
            user.role = role

        if 'is_active' in data:
            user.is_active = bool(data.get('is_active'))

        new_password = data.get('password')
        if new_password:
            user.set_password(new_password)

        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update user")
        return jsonify({'error': str(e)}), 500


# Course Management
@bp.route('/courses', methods=['POST'])
@admin_required
def create_course():
    try:
        data = request.get_json() or {}
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
        logger.exception("Failed to create course")
        return jsonify({'error': str(e)}), 500


@bp.route('/courses/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        data = request.get_json() or {}
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
        logger.exception("Failed to update course")
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
        logger.exception("Failed to delete course")
        return jsonify({'error': str(e)}), 500


@bp.route('/courses/<int:course_id>/lessons', methods=['GET'])
@admin_required
def get_course_lessons_admin(course_id):
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
        return jsonify([lesson.to_dict() for lesson in lessons]), 200
    except Exception as e:
        logger.exception("Failed to list course lessons")
        return jsonify({'error': str(e)}), 500


@bp.route('/courses/<int:course_id>/enrollments', methods=['GET'])
@admin_required
def list_enrollments(course_id):
    try:
        enrolls = Enrollment.query.filter_by(course_id=course_id).all()
        return jsonify([{
            'user_id': e.user_id,
            'course_id': e.course_id,
            'progress_percentage': e.progress_percentage
        } for e in enrolls]), 200
    except Exception as e:
        logger.exception("Failed to list enrollments")
        return jsonify({'error': str(e)}), 500


@bp.route('/courses/<int:course_id>/enroll', methods=['POST'])
@admin_required
def enroll_user(course_id):
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        existing = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if existing:
            return jsonify({'message': 'Already enrolled'}), 200
        enroll = Enrollment(user_id=user_id, course_id=course_id, progress_percentage=0)
        db.session.add(enroll)
        db.session.commit()
        return jsonify({'message': 'User enrolled'}), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to enroll user")
        return jsonify({'error': str(e)}), 500


@bp.route('/courses/<int:course_id>/unenroll', methods=['POST'])
@admin_required
def unenroll_user(course_id):
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        enroll = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if not enroll:
            return jsonify({'error': 'Enrollment not found'}), 404
        db.session.delete(enroll)
        db.session.commit()
        return jsonify({'message': 'User unenrolled'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to unenroll user")
        return jsonify({'error': str(e)}), 500


@bp.route('/lessons', methods=['POST'])
@admin_required
def create_lesson():
    try:
        data = request.get_json() or {}

        # Validate course exists before creating lesson
        course_id = data.get('course_id')
        if course_id:
            course = Course.query.get(course_id)
            if not course:
                return jsonify({'error': 'Course not found'}), 404

        lesson = Lesson(
            course_id=course_id,
            lesson_title=data.get('lesson_title'),
            lesson_content=data.get('lesson_content'),
            lesson_order=data.get('lesson_order'),
            video_url=data.get('video_url'),
            duration_minutes=data.get('duration_minutes')
        )
        db.session.add(lesson)
        db.session.commit()

        try:
            # Try to auto-generate quiz but don't block lesson creation on failure
            generate_quiz_for_lesson(lesson.lesson_id, num_questions=5)
        except Exception as e:
            logger.exception(f"AI quiz generation failed for lesson {lesson.lesson_id}: {e}")

        return jsonify({
            'message': 'Lesson created successfully',
            'lesson': lesson.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to create lesson")
        return jsonify({'error': str(e)}), 500


@bp.route('/lessons/<int:lesson_id>', methods=['PUT'])
@admin_required
def update_lesson(lesson_id):
    try:
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404

        data = request.get_json() or {}
        if 'lesson_title' in data:
            lesson.lesson_title = data['lesson_title']
        if 'lesson_content' in data:
            lesson.lesson_content = data['lesson_content']
        if 'lesson_order' in data:
            lesson.lesson_order = data['lesson_order']
        if 'video_url' in data:
            lesson.video_url = data['video_url']
        if 'duration_minutes' in data:
            lesson.duration_minutes = data['duration_minutes']

        lesson.updated_at = datetime.utcnow()
        db.session.commit()

        try:
            generate_quiz_for_lesson(lesson.lesson_id, num_questions=5)
        except Exception as e:
            logger.exception(f"AI quiz generation failed for lesson update {lesson.lesson_id}: {e}")

        return jsonify({
            'message': 'Lesson updated successfully',
            'lesson': lesson.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update lesson")
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
        logger.exception("Failed to delete lesson")
        return jsonify({'error': str(e)}), 500


# ------------------ Notifications ------------------
@bp.route('/notifications/send', methods=['POST'])
@admin_required
def send_notifications():
    """Admin: send notification to users. Input JSON: {title, message, target}
       target: 'all' currently supported"""
    try:
        data = request.get_json() or {}
        title = data.get('title')
        message = data.get('message')
        target = data.get('target', 'all')

        if not title or not message:
            return jsonify({'error': 'title and message are required'}), 400

        if target == 'all':
            # Create notifications for all users
            # Use a robust extraction of user ids
            user_rows = User.query.with_entities(User.user_id).all()
            user_ids = []
            for row in user_rows:
                # row may be a tuple or an object with attribute
                if isinstance(row, tuple):
                    user_ids.append(row[0])
                else:
                    user_ids.append(getattr(row, 'user_id', None))
            user_ids = [uid for uid in user_ids if uid is not None]

            now = datetime.utcnow()
            objs = [Notification(user_id=uid, title=title, message=message, notification_type='admin_broadcast', is_read=False, created_at=now) for uid in user_ids]
            if objs:
                db.session.bulk_save_objects(objs)
                db.session.commit()
            return jsonify({'message': 'Notifications created', 'count': len(objs)}), 201

        return jsonify({'error': 'Unsupported target'}), 400
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to send notifications")
        return jsonify({'error': str(e)}), 500


@bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for current user. Optional query param: unread=true|false"""
    try:
        user_id = get_current_user_id()
        unread = request.args.get('unread', None)

        query = Notification.query.filter_by(user_id=user_id)
        if unread is not None:
            want_unread = str(unread).lower() in ('1', 'true', 'yes')
            # want_unread == True  => filter is_read == False
            query = query.filter_by(is_read=(not want_unread))

        notes = query.order_by(Notification.created_at.desc()).limit(50).all()
        return jsonify([{
            'notification_id': n.notification_id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None
        } for n in notes]), 200
    except Exception as e:
        logger.exception("Failed to fetch notifications")
        return jsonify({'error': str(e)}), 500