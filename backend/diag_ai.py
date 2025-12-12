from dotenv import load_dotenv
import os
import json
import traceback

load_dotenv()

print('ENV AI_PROVIDER=', os.getenv('AI_PROVIDER'))
print('GEMINI set=', bool(os.getenv('GEMINI_API_KEY')))
print('OPENAI set=', bool(os.getenv('OPENAI_API_KEY')))

try:
    from ai_models.ai_service import get_ai_service, AIServiceConfig
    cfg = AIServiceConfig()
    print('Config: provider=', cfg.ai_provider, 'model=', cfg.gemini_model if cfg.ai_provider=='gemini' else cfg.openai_model)

    svc = get_ai_service()
    print('Service instance:', type(svc))
    print('Has client:', hasattr(svc, 'client') and svc.client is not None)

    topic = 'Giới thiệu Python'
    level = 'beginner'
    print('\n--- Calling generate_lesson_content ---')
    lesson = svc.generate_lesson_content(topic, level)
    print('Result type:', type(lesson))
    print('Result content (first 1000 chars):')
    if isinstance(lesson, dict):
        print(json.dumps(lesson, ensure_ascii=False, indent=2))
    else:
        print(str(lesson)[:1000])

    print('\n--- Calling generate_response fallback ---')
    resp = svc.generate_response(f'Soạn nội dung bài giảng về: {topic} (trình độ: {level})')
    print('Fallback response type:', type(resp))
    print('Fallback response (first 1000 chars):')
    print(str(resp)[:1000])

except Exception as e:
    print('ERROR during diagnostic:')
    traceback.print_exc()
