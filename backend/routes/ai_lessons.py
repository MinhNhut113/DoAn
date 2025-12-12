from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ai_models.ai_service import get_ai_service
import logging

bp = Blueprint('ai_lessons', __name__)
logger = logging.getLogger(__name__)

@bp.route('/generate-lesson', methods=['POST'])
@jwt_required()
def generate_lesson_ai():
    """
    API tạo nội dung bài học tự động
    Input: { "topic": "Lập trình Python", "level": "Cơ bản" }
    """
    try:
        data = request.get_json()
        topic = data.get('topic')
        level = data.get('level', 'beginner')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        ai_service = get_ai_service()
        if not ai_service:
            logger.error("[AI] AI service returned None")
            return jsonify({'error': 'AI service not available'}), 503

        logger.info(f"[AI] Generating lesson for topic: {topic}, level: {level}")
        try:
            lesson_data = ai_service.generate_lesson_content(topic, level)
        except Exception as e:
            logger.error(f"[AI] generate_lesson_content raised exception: {e}")
            lesson_data = None

        if lesson_data:
            return jsonify(lesson_data), 200

        # Fallback: try to get a plain text response and return as content
        try:
            logger.warning(f"[AI] Lesson generation returned no parsed JSON for topic: {topic}. Attempting fallback text response.")
            system_prompt = (
                "Bạn là một giảng viên chuyên nghiệp. Soạn một bài giảng ngắn gọn về chủ đề dưới đây. "
                "Nếu có thể, trả về nội dung bằng Markdown."
            )
            fallback_text = ai_service.generate_response(f"Soạn nội dung bài giảng về: {topic} (trình độ: {level})", None, system_prompt)
            if fallback_text:
                fallback = {
                    'title': topic,
                    'summary': (fallback_text.split('\n')[0] if '\n' in fallback_text else fallback_text)[:200],
                    'content': fallback_text,
                    'duration_minutes': 10
                }
                logger.info(f"[AI] Returning fallback lesson content for topic: {topic}")
                return jsonify(fallback), 200
        except Exception as e:
            logger.error(f"[AI] Fallback generation error: {e}")

        # Log more context for debugging when generation fails
        logger.error(f"[AI] Lesson generation returned no data for topic: {topic}. Check AI service keys and model output.")
        return jsonify({'error': 'AI failed to generate lesson content'}), 500
        
    except Exception as e:
        logger.error(f"[AI] Generate lesson error: {e}")
        return jsonify({'error': str(e)}), 500