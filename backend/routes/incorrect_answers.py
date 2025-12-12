"""Routes for analyzing incorrect answers and providing AI recommendations"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import (
    db, User, IncorrectAnswerAnalysis, QuizAnswer, QuizResult, 
    QuizQuestion, Quiz, Lesson, Topic
)
from ai_models.lesson_recommendation import IncorrectAnswerRecommendationEngine
from ai_models.ai_service import get_ai_service
from datetime import datetime
import logging

bp = Blueprint('incorrect_answers', __name__)
logger = logging.getLogger(__name__)

@bp.route('/api/incorrect-answers/analyze', methods=['POST'])
@jwt_required()
def analyze_incorrect_answer():
    """
    Phân tích một câu trả lời sai và gợi ý bài học
    Expected JSON: {
        "question_id": 1,
        "user_answer": 1,      # Index of answer (0-3)
        "correct_answer": 2,   # Index of correct answer
        "quiz_id": 1
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        question_id = data.get('question_id')
        user_answer = data.get('user_answer')
        correct_answer = data.get('correct_answer')
        quiz_id = data.get('quiz_id')
        
        if not all([question_id, user_answer is not None, 
                   correct_answer is not None, quiz_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Phân tích câu trả lời sai
        analysis = IncorrectAnswerRecommendationEngine.analyze_incorrect_answer(
            user_id, question_id, user_answer, correct_answer, quiz_id
        )
        
        if not analysis:
            return jsonify({'error': 'Failed to analyze answer'}), 500
        
        # Nếu có AI service, phân tích chi tiết hơn
        question = QuizQuestion.query.get(question_id)
        if question and analysis:
            ai_service = get_ai_service()
            if ai_service:
                try:
                    # Lấy thông tin các lựa chọn
                    import json
                    options = []
                    if question.options:
                        try:
                            options = json.loads(question.options)
                        except Exception as e:
                            logger.debug(f"[IncorrectAnswer] Failed to parse question options JSON: {e}")
                            options = []
                    
                    user_answer_text = options[user_answer] if user_answer < len(options) else "Unknown"
                    correct_answer_text = options[correct_answer] if correct_answer < len(options) else "Unknown"
                    
                    # Tạo prompt cho AI
                    prompt = f"""Phân tích tại sao sinh viên trả lời sai câu hỏi này:

Câu hỏi: {question.question_text}

Lựa chọn:
{chr(10).join([f"{i}. {opt}" for i, opt in enumerate(options)])}

Sinh viên chọn: {user_answer_text} (sai)
Đáp án đúng: {correct_answer_text}

Giải thích: {question.explanation}

Hãy:
1. Xác định lỗi khái niệm cụ thể
2. Giải thích tại sao sinh viên sai
3. Gợi ý khái niệm cần ôn lại

Trả lời bằng tiếng Việt, ngắn gọn (2-3 câu)."""
                    
                    ai_analysis = ai_service.generate_response(prompt)
                    if ai_analysis:
                        # Cập nhật analysis với AI insights
                        analysis_record = IncorrectAnswerAnalysis.query.get(analysis['analysis_id'])
                        if analysis_record:
                            analysis_record.ai_analysis = ai_analysis
                            db.session.commit()
                            analysis['ai_analysis'] = ai_analysis
                except Exception as e:
                    logger.warning(f"[IncorrectAnswer] AI analysis failed: {e}")
        
        return jsonify({
            'analysis': analysis,
            'message': 'Answer analyzed successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"[IncorrectAnswer] Error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/incorrect-answers/insights', methods=['GET'])
@jwt_required()
def get_incorrect_answer_insights():
    """
    Lấy danh sách những câu trả lời sai gần đây và gợi ý bài học
    Query params:
    - course_id: Optional course filter
    - limit: Max results (default 10)
    """
    try:
        user_id = get_current_user_id()
        course_id = request.args.get('course_id', type=int)
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        # Lấy insights
        insights = IncorrectAnswerRecommendationEngine.get_incorrect_answer_insights(
            user_id, course_id, limit
        )
        
        return jsonify({
            'insights': insights,
            'total': len(insights)
        }), 200
        
    except Exception as e:
        logger.error(f"[IncorrectAnswer] Error getting insights: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/incorrect-answers/common-mistakes', methods=['GET'])
@jwt_required()
def get_common_mistakes():
    """
    Lấy những lỗi thường gặp theo chủ đề (cho giáo viên/admin)
    Query params:
    - course_id: Required course ID
    - topic_id: Optional topic filter
    - limit: Max results (default 5)
    """
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        # Chỉ giáo viên & admin mới xem được
        if not user or user.role not in ['admin', 'instructor']:
            return jsonify({'error': 'Only instructors can view this'}), 403
        
        course_id = request.args.get('course_id', type=int)
        topic_id = request.args.get('topic_id', type=int)
        limit = min(request.args.get('limit', 5, type=int), 20)
        
        if not course_id:
            return jsonify({'error': 'course_id is required'}), 400
        
        # Lấy common mistakes
        mistakes = IncorrectAnswerRecommendationEngine.get_common_mistakes_by_topic(
            course_id, topic_id, limit
        )
        
        return jsonify({
            'common_mistakes': mistakes,
            'total': len(mistakes)
        }), 200
        
    except Exception as e:
        logger.error(f"[IncorrectAnswer] Error getting common mistakes: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/incorrect-answers/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_incorrect_answer_detail(analysis_id):
    """Lấy chi tiết một lỗi sai cụ thể"""
    try:
        user_id = get_current_user_id()
        
        analysis = IncorrectAnswerAnalysis.query.filter_by(
            analysis_id=analysis_id,
            user_id=user_id
        ).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Lấy thông tin lesson được gợi ý
        recommended_lessons = []
        if analysis.recommended_lessons:
            try:
                import json
                lesson_ids = json.loads(analysis.recommended_lessons)
                for lid in lesson_ids:
                    lesson = Lesson.query.get(lid)
                    if lesson:
                        recommended_lessons.append(lesson.to_dict())
            except Exception as e:
                logger.debug(f"[IncorrectAnswer] Failed to parse recommended_lessons JSON: {e}")
        
        result = analysis.to_dict()
        result['recommended_lessons_detail'] = recommended_lessons
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"[IncorrectAnswer] Error getting detail: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/incorrect-answers/related-lesson/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_related_incorrect_answers(lesson_id):
    """
    Lấy những câu trả lời sai liên quan đến một bài học
    (cho biết sinh viên cần ôn lại những gì khi xem bài học này)
    """
    try:
        user_id = get_current_user_id()
        
        # Lấy lesson
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        # Lấy những câu hỏi của bài học này
        questions = QuizQuestion.query.filter_by(lesson_id=lesson_id).all()
        question_ids = [q.question_id for q in questions]
        
        if not question_ids:
            return jsonify({
                'lesson_id': lesson_id,
                'lesson_title': lesson.lesson_title,
                'related_mistakes': [],
                'message': 'No quiz questions for this lesson'
            }), 200
        
        # Lấy những lỗi sai liên quan
        from sqlalchemy import func
        mistakes = db.session.query(
            IncorrectAnswerAnalysis
        ).filter(
            IncorrectAnswerAnalysis.user_id == user_id,
            IncorrectAnswerAnalysis.question_id.in_(question_ids)
        ).order_by(
            IncorrectAnswerAnalysis.created_at.desc()
        ).all()
        
        return jsonify({
            'lesson_id': lesson_id,
            'lesson_title': lesson.lesson_title,
            'related_mistakes': [m.to_dict() for m in mistakes],
            'total_related_mistakes': len(mistakes)
        }), 200
        
    except Exception as e:
        logger.error(f"[IncorrectAnswer] Error getting related mistakes: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/incorrect-answers/stats', methods=['GET'])
@jwt_required()
def get_incorrect_answer_stats():
    """
    Lấy thống kê về câu trả lời sai của sinh viên
    """
    try:
        user_id = get_current_user_id()
        course_id = request.args.get('course_id', type=int)
        
        query = IncorrectAnswerAnalysis.query.filter_by(user_id=user_id)
        
        if course_id:
            query = query.filter_by(course_id=course_id)
        
        total_incorrect = query.count()
        
        # Phân loại theo error type
        from sqlalchemy import func
        error_stats = db.session.query(
            IncorrectAnswerAnalysis.error_type,
            func.count(IncorrectAnswerAnalysis.analysis_id).label('count')
        ).filter_by(user_id=user_id)
        
        if course_id:
            error_stats = error_stats.filter_by(course_id=course_id)
        
        error_stats = error_stats.group_by(
            IncorrectAnswerAnalysis.error_type
        ).all()
        
        # Lỗi nhiều nhất
        most_common_topic = db.session.query(
            IncorrectAnswerAnalysis.topic_id,
            Topic.topic_name,
            func.count(IncorrectAnswerAnalysis.analysis_id).label('count')
        ).join(
            Topic, IncorrectAnswerAnalysis.topic_id == Topic.topic_id
        ).filter(IncorrectAnswerAnalysis.user_id == user_id)
        
        if course_id:
            most_common_topic = most_common_topic.filter(
                IncorrectAnswerAnalysis.course_id == course_id
            )
        
        most_common_topic = most_common_topic.group_by(
            IncorrectAnswerAnalysis.topic_id,
            Topic.topic_name
        ).order_by(
            func.count(IncorrectAnswerAnalysis.analysis_id).desc()
        ).first()
        
        return jsonify({
            'total_incorrect_answers': total_incorrect,
            'error_breakdown': [
                {
                    'error_type': stat.error_type or 'unknown',
                    'count': stat.count
                } for stat in error_stats
            ],
            'most_problematic_topic': {
                'topic_id': most_common_topic.topic_id,
                'topic_name': most_common_topic.topic_name,
                'mistakes_count': most_common_topic.count
            } if most_common_topic else None
        }), 200
        
    except Exception as e:
        logger.error(f"[IncorrectAnswer] Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500
