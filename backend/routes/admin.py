from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, User, Course, Lesson, QuizQuestion, Quiz, QuizQuestionMapping, AIGeneratedQuestion, GenerationRequest, Enrollment, QuizResult, Assignment
from functools import wraps
from datetime import datetime
import json
import time
from backend.ai_models.ai_service import get_ai_service

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
@bp.route('/courses/<int:course_id>/lessons', methods=['GET'])
@admin_required
def get_course_lessons_admin(course_id):
    """Get all lessons for a course (admin access, no enrollment check)"""
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
        return jsonify([lesson.to_dict() for lesson in lessons]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Enrollment management for admin
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
        return jsonify({'error': str(e)}), 500

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

        # After lesson is created, automatically generate AI quiz (default 5 MC questions)
        try:
            generate_quiz_for_lesson(lesson.lesson_id, num_questions=5)
        except Exception as e:
            # Don't fail the request if quiz generation fails - just log
            import logging
            logging.getLogger(__name__).exception(f"AI quiz generation failed for lesson {lesson.lesson_id}: {e}")

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

        # After lesson update, regenerate AI quiz (replace existing auto-generated quiz)
        try:
            generate_quiz_for_lesson(lesson.lesson_id, num_questions=5)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"AI quiz generation failed for lesson update {lesson.lesson_id}: {e}")

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

@bp.route('/questions', methods=['GET'])
@admin_required
def list_questions():
    try:
        questions = QuizQuestion.query.all()
        return jsonify([q.to_dict(include_answer=False) for q in questions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/questions/<int:question_id>', methods=['GET'])
@admin_required
def get_question(question_id):
    try:
        q = QuizQuestion.query.get(question_id)
        if not q:
            return jsonify({'error': 'Question not found'}), 404
        return jsonify(q.to_dict(include_answer=True)), 200
    except Exception as e:
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


def generate_quiz_for_lesson(lesson_id: int, num_questions: int = 5):
    """Generate a multiple-choice quiz for a lesson using AI and save as a Quiz with mappings."""
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
    {"key_point":"Thẻ <a> dùng để tạo liên kết","question_text":"Thẻ HTML nào dùng để tạo liên kết?","options":["<a>","<p>","<div>"],"correct_answer":0},
    {"key_point":"Thẻ <h1> là tiêu đề lớn nhất","question_text":"Thẻ nào thường dùng cho tiêu đề lớn nhất?","options":["<h1>","<h3>","<span>"],"correct_answer":0}
]

Bài học (title và nội dung):
Title: {lesson.lesson_title}
Content: {lesson.lesson_content or ''}

Trả về CHÍNH XÁC JSON array gồm {num_questions} phần tử, mỗi phần tử chứa `key_point` và một câu hỏi tương ứng.
"""

    raw = ai.generate_response(prompt)
    if not raw:
        raise RuntimeError('AI returned no response')

    # Preserve raw response for auditing
    raw_response = raw

    # Try parse JSON robustly
    questions = None
    try:
        questions = json.loads(raw)
    except Exception:
        # Try to extract the first JSON array substring
        import re
        m = re.search(r"\[\s*\{.*?\}\s*\]", raw, re.DOTALL)
        if m:
            try:
                questions = json.loads(m.group())
            except Exception:
                # Attempt to balance braces heuristically
                start = raw.find('[')
                end = raw.rfind(']')
                if start != -1 and end != -1 and end > start:
                    questions = json.loads(raw[start:end+1])
        if questions is None:
            raise RuntimeError('Failed to parse JSON from AI response')

    # Validate and normalize questions (expecting key_point present)
    clean_questions = []
    for i, q in enumerate(questions[:num_questions]):
        # prefer to associate question with a key_point
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
            # Skip invalid question
            continue

        # Determine correct answer index
        corr = q.get('correct_answer')
        if isinstance(corr, str):
            # Accept letter e.g. 'A' or 'a' or textual answer - map to index
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
            # If out of range, fallback to 0
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
    quiz_name = f"LessonQuiz:{lesson.lesson_id}:{lesson.lesson_title[:80]}"
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
        except Exception:
            pass
        db.session.add(gen)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return quiz.quiz_id

