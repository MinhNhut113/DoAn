from dotenv import load_dotenv
import os
import json
import traceback

load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f'ENV AI_PROVIDER={os.getenv("AI_PROVIDER")}')
logger.info(f'GEMINI set={bool(os.getenv("GEMINI_API_KEY"))}')
logger.info(f'OPENAI set={bool(os.getenv("OPENAI_API_KEY"))}')

try:
    from ai_models.ai_service import get_ai_service, AIServiceConfig
    cfg = AIServiceConfig()
    logger.info(f'Config: provider={cfg.ai_provider} model={cfg.gemini_model if cfg.ai_provider=="gemini" else cfg.openai_model}')

    svc = get_ai_service()
    logger.info(f'Service instance: {type(svc)}')
    logger.info(f'Has client: {hasattr(svc, "client") and svc.client is not None}')

    topic = 'Giới thiệu Python'
    level = 'beginner'
    logger.info('--- Calling generate_lesson_content ---')
    lesson = svc.generate_lesson_content(topic, level)
    logger.info(f'Result type: {type(lesson)}')
    logger.info('Result content (first 1000 chars):')
    if isinstance(lesson, dict):
        logger.info(json.dumps(lesson, ensure_ascii=False, indent=2))
    else:
        logger.info(str(lesson)[:1000])

    logger.info('--- Calling generate_response fallback ---')
    resp = svc.generate_response(f'Soạn nội dung bài giảng về: {topic} (trình độ: {level})')
    logger.info(f'Fallback response type: {type(resp)}')
    logger.info('Fallback response (first 1000 chars):')
    logger.info(str(resp)[:1000])

except Exception as e:
    logger.error('ERROR during diagnostic:')
    logger.error(traceback.format_exc())
