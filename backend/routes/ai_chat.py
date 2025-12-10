"""Routes for AI Chatbot - Student questions and lesson help"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import (
    db, User, AIChatMessage, Lesson, Course, Topic
)
from ai_models.ai_service import generate_ai_response, get_ai_service
from datetime import datetime
import uuid
import logging
from sqlalchemy import func

bp = Blueprint('ai_chat', __name__)
logger = logging.getLogger(__name__)

@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat_with_ai():
    """
    Main chatbot endpoint - student asks questions about lessons
    Expected JSON: {
        "message": "Câu hỏi của sinh viên",
        "lesson_id": 1,  # Optional
        "course_id": 1,  # Optional
        "conversation_id": "uuid"  # Optional, to group related messages
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data.get('message').strip()
        lesson_id = data.get('lesson_id')
        course_id = data.get('course_id')
        conversation_id = data.get('conversation_id') or str(uuid.uuid4())
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get lesson/course context if provided
        context = ""
        if lesson_id:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                context = f"Bài học: {lesson.lesson_title}\n\n"
                if lesson.lesson_content:
                    context += f"Nội dung: {lesson.lesson_content[:1000]}"  # First 1000 chars
        elif course_id:
            course = Course.query.get(course_id)
            if course:
                context = f"Khóa học: {course.course_name}\n\n{course.description}"
        
        # Generate AI response
        ai_service = get_ai_service('openai')
        if not ai_service:
            # Fallback to a simple response
            ai_response = "Xin lỗi, dịch vụ AI hiện không khả dụng. Vui lòng thử lại sau."
            logger.warning("[Chat] AI service not available")
        else:
            system_prompt = """Bạn là một trợ lý giáo dục thông minh cho sinh viên học trực tuyến.
            
Hãy:
- Trả lời bằng tiếng Việt rõ ràng và dễ hiểu
- Giải thích chi tiết để sinh viên hiểu rõ
- Sử dụng ví dụ thực tế khi cần
- Nếu câu hỏi liên quan đến bài học, sử dụng nội dung bài học để giải thích
- Khuyến khích học tập tích cực
- Giới hạn câu trả lời dưới 500 từ"""
            
            ai_response = ai_service.generate_response(user_message, context, system_prompt)
            
            if not ai_response:
                ai_response = "Xin lỗi, tôi không thể tạo phản hồi. Vui lòng thử câu hỏi khác."
        
        # Save chat message to database
        chat_message = AIChatMessage(
            user_id=user_id,
            lesson_id=lesson_id,
            course_id=course_id,
            user_message=user_message,
            ai_response=ai_response,
            conversation_id=conversation_id,
            message_type='question'
        )
        
        db.session.add(chat_message)
        db.session.commit()
        
        logger.info(f"[Chat] Message saved - User: {user_id}, Conversation: {conversation_id}")
        
        return jsonify({
            'message_id': chat_message.message_id,
            'user_message': user_message,
            'ai_response': ai_response,
            'conversation_id': conversation_id,
            'timestamp': chat_message.created_at.isoformat(),
            'lesson_id': lesson_id,
            'course_id': course_id
        }), 201
        
    except Exception as e:
        logger.error(f"[Chat] Error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/chat/history/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation_history(conversation_id):
    """Get full conversation history"""
    try:
        user_id = get_current_user_id()
        
        messages = AIChatMessage.query.filter_by(
            user_id=user_id,
            conversation_id=conversation_id
        ).order_by(AIChatMessage.created_at).all()
        
        if not messages:
            return jsonify({'error': 'Conversation not found'}), 404
        
        return jsonify({
            'conversation_id': conversation_id,
            'messages': [
                {
                    'message_id': m.message_id,
                    'user_message': m.user_message,
                    'ai_response': m.ai_response,
                    'timestamp': m.created_at.isoformat(),
                    'helpful_rating': m.helpful_rating,
                    'lesson_id': m.lesson_id,
                    'course_id': m.course_id
                } for m in messages
            ],
            'total_messages': len(messages)
        }), 200
        
    except Exception as e:
        logger.error(f"[Chat] Error getting history: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/chat/rate/<int:message_id>', methods=['POST'])
@jwt_required()
def rate_message(message_id):
    """Rate AI response helpfulness (1-5)"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        rating = data.get('rating')
        
        if rating is None or not (1 <= rating <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        message = AIChatMessage.query.filter_by(
            message_id=message_id,
            user_id=user_id
        ).first()
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        message.helpful_rating = rating
        db.session.commit()
        
        logger.info(f"[Chat] Message {message_id} rated {rating}/5")
        
        return jsonify({
            'message_id': message_id,
            'rating': rating,
            'message': 'Rating saved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"[Chat] Error rating message: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/chat/conversations', methods=['GET'])
@jwt_required()
def get_user_conversations():
    """Get all conversations for current user"""
    try:
        user_id = get_current_user_id()
        
        conversations = db.session.query(
            AIChatMessage.conversation_id,
            AIChatMessage.lesson_id,
            AIChatMessage.course_id,
            func.max(AIChatMessage.created_at).label('last_message_at'),
            func.count(AIChatMessage.message_id).label('message_count')
        ).filter_by(user_id=user_id).group_by(
            AIChatMessage.conversation_id,
            AIChatMessage.lesson_id,
            AIChatMessage.course_id
        ).order_by(
            func.max(AIChatMessage.created_at).desc()
        ).all()
        
        result = []
        for conv in conversations:
            lesson_info = None
            course_info = None
            
            if conv.lesson_id:
                lesson = Lesson.query.get(conv.lesson_id)
                if lesson:
                    lesson_info = {'lesson_id': lesson.lesson_id, 'title': lesson.lesson_title}
            
            if conv.course_id:
                course = Course.query.get(conv.course_id)
                if course:
                    course_info = {'course_id': course.course_id, 'name': course.course_name}
            
            result.append({
                'conversation_id': conv.conversation_id,
                'lesson': lesson_info,
                'course': course_info,
                'message_count': conv.message_count,
                'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None
            })
        
        return jsonify({
            'conversations': result,
            'total_conversations': len(result)
        }), 200
        
    except Exception as e:
        logger.error(f"[Chat] Error getting conversations: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Check AI service health"""
    try:
        ai_service = get_ai_service('openai')
        status = 'available' if ai_service and ai_service.client else 'unavailable'
        
        return jsonify({
            'status': status,
            'service': 'openai',
            'message': 'AI service is ' + status
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Import func for queries
from sqlalchemy import func
