"""AI Service for handling LLM interactions (OpenAI, Google Gemini, etc.)"""
import os
import json
import logging
from typing import Optional, List, Dict, Any
import re

logger = logging.getLogger(__name__)

class AIServiceConfig:
    """Configuration for AI Services"""
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        
        self.ai_provider = os.getenv('AI_PROVIDER', 'gemini').lower()
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '2000'))
        
        self.system_prompt_base = "Bạn là một trợ lý giáo dục thông minh."

class OpenAIService:
    """Service for OpenAI API interactions"""
    def __init__(self):
        self.config = AIServiceConfig()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            import openai
            if self.config.openai_api_key:
                self.client = openai.OpenAI(api_key=self.config.openai_api_key)
                logger.info("[AI] OpenAI client initialized")
        except Exception as e:
            logger.error(f"[AI] Failed to initialize OpenAI: {e}")

    def generate_response(self, user_message: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.client: return None
        try:
            messages = [{"role": "system", "content": system_prompt or self.config.system_prompt_base}]
            if context: messages.append({"role": "system", "content": f"Ngữ cảnh: {context}"})
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[AI] OpenAI error: {e}")
            return None

    def generate_lesson_content(self, topic: str, level: str = "beginner") -> Optional[Dict]:
        """Generate lesson content based on topic"""
        if not self.client: return None
        try:
            prompt = f"""Hãy đóng vai một giảng viên chuyên nghiệp.
            Hãy soạn thảo một bài giảng chi tiết về chủ đề: "{topic}"
            Trình độ: {level}
            
            Yêu cầu định dạng JSON chính xác:
            {{
                "title": "Tiêu đề bài học hấp dẫn",
                "content": "Nội dung bài giảng chi tiết (dùng định dạng Markdown), bao gồm định nghĩa, ví dụ minh họa và bài tập nhỏ.",
                "duration_minutes": 15,
                "summary": "Tóm tắt ngắn gọn bài học (dưới 50 từ)"
            }}
            """
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            text = response.choices[0].message.content
            logger.debug(f"[AI][OpenAI] Lesson generation raw text: {text}")

            # Try robust JSON extraction strategies
            json_obj = None
            try:
                # Try direct JSON parse
                json_obj = json.loads(text)
            except Exception:
                # Try regex extract first {...}
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    try:
                        json_obj = json.loads(json_match.group())
                    except Exception:
                        # Try extracting between first '{' and last '}'
                        try:
                            start = text.find('{')
                            end = text.rfind('}')
                            if start != -1 and end != -1 and end > start:
                                json_obj = json.loads(text[start:end+1])
                        except Exception:
                            json_obj = None

            if not json_obj:
                logger.warning('[AI][OpenAI] Failed to parse JSON from model output for topic: %s', topic)
            return json_obj
        except Exception as e:
            logger.error(f"[AI] Lesson generation error: {e}")
            return None

class GoogleGeminiService:
    """Service for Google Gemini API interactions"""
    def __init__(self):
        self.config = AIServiceConfig()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            import google.generativeai as genai
            if self.config.gemini_api_key:
                genai.configure(api_key=self.config.gemini_api_key)
                self.client = genai
                logger.info(f"[AI] Gemini client initialized: {self.config.gemini_model}")
        except Exception as e:
            logger.error(f"[AI] Failed to initialize Gemini: {e}")

    def generate_response(self, user_message: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.client: return None
        try:
            full_prompt = f"{system_prompt or self.config.system_prompt_base}\n\n"
            if context: full_prompt += f"Ngữ cảnh: {context}\n\n"
            full_prompt += f"Câu hỏi: {user_message}"
            
            model = self.client.GenerativeModel(self.config.gemini_model)
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"[AI] Gemini error: {e}")
            return None

    def generate_lesson_content(self, topic: str, level: str = "beginner") -> Optional[Dict]:
        """Generate lesson content using Gemini"""
        if not self.client: return None
        try:
            prompt = f"""Hãy đóng vai một giảng viên chuyên nghiệp.
            Hãy soạn thảo một bài giảng chi tiết về chủ đề: "{topic}"
            Trình độ: {level}
            
            Yêu cầu định dạng JSON chính xác (không thêm markdown ```json):
            {{
                "title": "Tiêu đề bài học hấp dẫn",
                "content": "Nội dung bài giảng chi tiết (dùng định dạng Markdown), bao gồm định nghĩa, ví dụ minh họa và bài tập nhỏ.",
                "duration_minutes": 15,
                "summary": "Tóm tắt ngắn gọn bài học (dưới 50 từ)"
            }}
            """
            model = self.client.GenerativeModel(self.config.gemini_model)
            response = model.generate_content(prompt)
            text = getattr(response, 'text', str(response))
            logger.debug(f"[AI][Gemini] Lesson generation raw text: {text}")

            # Try robust JSON extraction strategies
            json_obj = None
            try:
                json_obj = json.loads(text)
            except Exception:
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    try:
                        json_obj = json.loads(json_match.group())
                    except Exception:
                        try:
                            start = text.find('{')
                            end = text.rfind('}')
                            if start != -1 and end != -1 and end > start:
                                json_obj = json.loads(text[start:end+1])
                        except Exception:
                            json_obj = None

            if not json_obj:
                logger.warning('[AI][Gemini] Failed to parse JSON from model output for topic: %s', topic)
            return json_obj
        except Exception as e:
            logger.error(f"[AI] Gemini lesson error: {e}")
            return None

def get_ai_service():
    config = AIServiceConfig()
    if config.ai_provider == 'openai':
        return OpenAIService()
    return GoogleGeminiService()