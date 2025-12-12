"""Routes for AI-Generated Quiz Questions"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import (
    db, User, AIGeneratedQuestion, GenerationRequest, Topic, 
    Lesson, Course, QuizQuestionMapping, Quiz
)
from ai_models.ai_service import get_ai_service
import json
from datetime import datetime
import time
import logging

bp = Blueprint('ai_questions', __name__)
logger = logging.getLogger(__name__)

@bp.route('/generate-questions', methods=['POST'])
@jwt_required()
def generate_questions():
    """
    Generate quiz questions using AI
    Expected JSON: {
        "topic_id": 1,
        "lesson_id": 1,
        "num_questions": 5,
        "difficulty": 2,  # 1-5
        "lesson_content": "Optional lesson content to generate from"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Validate user is admin/instructor
        user = User.query.get(user_id)
        if not user or user.role not in ['admin', 'instructor']:
            return jsonify({'error': 'Only instructors can generate questions'}), 403
        
        topic_id = data.get('topic_id')
        lesson_id = data.get('lesson_id')
        course_id = data.get('course_id')
        num_questions = min(data.get('num_questions', 5), 10)  # Max 10
        difficulty = max(1, min(data.get('difficulty', 2), 5))  # 1-5
        lesson_content = data.get('lesson_content')
        
        if not topic_id and not lesson_id:
            return jsonify({'error': 'Either topic_id or lesson_id is required'}), 400
        
        # Get lesson content if not provided
        if not lesson_content and lesson_id:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                lesson_content = lesson.lesson_content or lesson.lesson_title
        
        if not lesson_content:
            return jsonify({'error': 'Lesson content required to generate questions'}), 400
        
        # Get topic information
        if not topic_id and lesson_id:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                course_id = lesson.course_id
        
        topic = Topic.query.get(topic_id) if topic_id else None
        topic_name = topic.topic_name if topic else "General"
        
        # Create generation request record
        gen_request = GenerationRequest(
            user_id=user_id,
            request_type='question_generation',
            topic_id=topic_id,
            course_id=course_id,
            lesson_id=lesson_id,
            input_prompt=f"Generate {num_questions} questions about {topic_name}",
            request_params=json.dumps({
                'num_questions': num_questions,
                'difficulty': difficulty
            }),
            status='processing'
        )
        db.session.add(gen_request)
        db.session.flush()
        request_id = gen_request.request_id
        
        # Generate questions using AI
        start_time = time.time()
        ai_service = get_ai_service('openai')
        
        if not ai_service:
            gen_request.status = 'failed'
            gen_request.error_message = 'AI service not available'
            db.session.commit()
            return jsonify({'error': 'AI service not available'}), 503
        
        # Generate questions
        questions = ai_service.generate_quiz_questions(
            topic_name,
            lesson_content,
            num_questions,
            difficulty
        )
        
        if not questions:
            gen_request.status = 'failed'
            gen_request.error_message = 'Failed to generate questions'
            db.session.commit()
            logger.error(f"[Questions] Failed to generate questions for topic {topic_id}")
            return jsonify({'error': 'Failed to generate questions'}), 500
        
        # Save generated questions to database
        generated_ids = []
        for i, q in enumerate(questions):
            try:
                # Parse options
                options_text = json.dumps(q.get('options', []))
                correct_answer = q.get('correct_answer', 0)
                
                gen_question = AIGeneratedQuestion(
                    topic_id=topic_id,
                    course_id=course_id,
                    lesson_id=lesson_id,
                    question_text=q.get('question', ''),
                    question_type='multiple_choice',
                    options=options_text,
                    correct_answer=correct_answer,
                    explanation=q.get('explanation', ''),
                    difficulty_level=difficulty,
                    generated_by='openai'
                )
                db.session.add(gen_question)
                db.session.flush()
                generated_ids.append(gen_question.gen_question_id)
                
            except Exception as e:
                logger.error(f"[Questions] Error saving question {i}: {e}")
        
        # Update generation request
        processing_time = time.time() - start_time
        gen_request.status = 'completed'
        gen_request.result_ids = json.dumps(generated_ids)
        gen_request.processing_time_seconds = processing_time
        db.session.commit()
        
        logger.info(f"[Questions] Generated {len(generated_ids)} questions in {processing_time:.2f}s")
        
        return jsonify({
            'request_id': request_id,
            'status': 'completed',
            'questions_generated': len(generated_ids),
            'processing_time_seconds': processing_time,
            'question_ids': generated_ids,
            'message': f'Successfully generated {len(generated_ids)} questions'
        }), 201
        
    except Exception as e:
        logger.error(f"[Questions] Error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/generated-questions', methods=['GET'])
@jwt_required()
def get_generated_questions():
    """List AI-generated questions with filters"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        # Only admins can see all, instructors see their own
        topic_id = request.args.get('topic_id', type=int)
        course_id = request.args.get('course_id', type=int)
        lesson_id = request.args.get('lesson_id', type=int)
        is_approved = request.args.get('approved', type=lambda x: x.lower() == 'true')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = AIGeneratedQuestion.query
        
        if topic_id:
            query = query.filter_by(topic_id=topic_id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        if lesson_id:
            query = query.filter_by(lesson_id=lesson_id)
        if is_approved is not None:
            query = query.filter_by(is_approved=is_approved)
        
        # For non-admins, only show approved questions
        if user and user.role != 'admin':
            query = query.filter_by(is_approved=True)
        
        paginated = query.order_by(AIGeneratedQuestion.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'questions': [q.to_dict() for q in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"[Questions] Error listing: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/generated-questions/<int:question_id>', methods=['GET'])
@jwt_required()
def get_generated_question(question_id):
    """Get single generated question details"""
    try:
        user_id = get_current_user_id()
        question = AIGeneratedQuestion.query.get(question_id)
        
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        user = User.query.get(user_id)
        
        # Check permissions
        if user and user.role == 'student' and not question.is_approved:
            return jsonify({'error': 'Question not approved yet'}), 403
        
        return jsonify(question.to_dict(include_answer=True)), 200
        
    except Exception as e:
        logger.error(f"[Questions] Error getting question: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/generated-questions/<int:question_id>/approve', methods=['POST'])
@jwt_required()
def approve_question(question_id):
    """Admin approves AI-generated question"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Only admins can approve questions'}), 403
        
        question = AIGeneratedQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        question.is_approved = True
        question.approved_by = user_id
        question.approval_date = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"[Questions] Question {question_id} approved by admin {user_id}")
        
        return jsonify({
            'message': 'Question approved successfully',
            'question_id': question_id,
            'is_approved': True
        }), 200
        
    except Exception as e:
        logger.error(f"[Questions] Error approving: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/generated-questions/<int:question_id>/reject', methods=['POST'])
@jwt_required()
def reject_question(question_id):
    """Admin rejects/deletes AI-generated question"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Only admins can reject questions'}), 403
        
        question = AIGeneratedQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        # Don't delete if already used in quizzes
        usage_count = QuizQuestionMapping.query.filter_by(
            question_id=question_id
        ).count()
        
        if usage_count > 0:
            return jsonify({
                'error': f'Cannot reject: question already used in {usage_count} quiz(zes)'
            }), 400
        
        db.session.delete(question)
        db.session.commit()
        
        logger.info(f"[Questions] Question {question_id} rejected by admin {user_id}")
        
        return jsonify({
            'message': 'Question rejected and deleted',
            'question_id': question_id
        }), 200
        
    except Exception as e:
        logger.error(f"[Questions] Error rejecting: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/generated-questions/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_generated_question(question_id):
    """Allow admin to modify AI-generated question content before approval."""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Only admins can update generated questions'}), 403

        question = AIGeneratedQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        data = request.get_json() or {}

        if 'question_text' in data:
            question.question_text = data.get('question_text')

        if 'options' in data:
            opts = data.get('options')
            # Accept list or JSON string or comma-separated
            if isinstance(opts, list):
                question.options = json.dumps(opts)
            elif isinstance(opts, str):
                try:
                    # try parse JSON
                    parsed = json.loads(opts)
                    if isinstance(parsed, list):
                        question.options = json.dumps(parsed)
                    else:
                        # fallback to storing as single option
                        question.options = json.dumps([opts])
                except Exception:
                    # comma-separated
                    parts = [p.trim() if hasattr(p, 'trim') else p.strip() for p in opts.split(',')]
                    question.options = json.dumps([p for p in parts if p])

        if 'correct_answer' in data:
            try:
                question.correct_answer = int(data.get('correct_answer'))
            except Exception:
                pass

        if 'explanation' in data:
            question.explanation = data.get('explanation')

        if 'difficulty_level' in data:
            try:
                question.difficulty_level = int(data.get('difficulty_level'))
            except Exception:
                pass

        # Do not automatically approve on edit; admin may call approve separately
        question.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Question updated', 'question': question.to_dict(include_answer=True)}), 200
    except Exception as e:
        logger.error(f"[Questions] Error updating question: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/generation-status/<int:request_id>', methods=['GET'])
@jwt_required()
def get_generation_status(request_id):
    """Get status of a generation request"""
    try:
        user_id = get_current_user_id()
        gen_request = GenerationRequest.query.get(request_id)
        
        if not gen_request:
            return jsonify({'error': 'Request not found'}), 404
        
        # Users can only check their own requests
        if gen_request.user_id != user_id:
            user = User.query.get(user_id)
            if not user or user.role != 'admin':
                return jsonify({'error': 'Permission denied'}), 403
        
        result_ids = []
        if gen_request.result_ids:
            try:
                result_ids = json.loads(gen_request.result_ids)
            except Exception as e:
                logger.debug(f"[Questions] Failed to parse gen_request.result_ids JSON: {e}")
        
        return jsonify({
            'request_id': request_id,
            'request_type': gen_request.request_type,
            'status': gen_request.status,
            'processing_time_seconds': gen_request.processing_time_seconds,
            'result_ids': result_ids,
            'error_message': gen_request.error_message,
            'created_at': gen_request.created_at.isoformat(),
            'completed_at': gen_request.completed_at.isoformat() if gen_request.completed_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"[Questions] Error getting status: {e}")
        return jsonify({'error': str(e)}), 500
