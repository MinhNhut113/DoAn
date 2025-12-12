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

        # Anthropic / Claude settings
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        # Default to Haiku 4.5 as requested
        self.claude_model = os.getenv('CLAUDE_MODEL', 'claude-haiku-4.5')

        # Default provider - set to 'claude' to enable Claude Haiku 4.5 for clients
        self.ai_provider = os.getenv('AI_PROVIDER', 'claude').lower()
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

    def generate_explanation(self, question_text: str, user_answer: str, correct_answer: str) -> Optional[str]:
        """Generate AI explanation for why an answer is wrong"""
        if not self.client:
            return None
        try:
            prompt = f"""Câu hỏi: {question_text}

Câu trả lời của học sinh: {user_answer}

Câu trả lời đúng: {correct_answer}

Hãy giải thích ngắn gọn (2-3 câu) tại sao câu trả lời của học sinh sai và tại sao câu trả lời đúng là đúng. Giải thích phải dễ hiểu và hữu ích cho học sinh."""
            
            model = self.client.GenerativeModel(self.config.gemini_model)
            response = model.generate_content(prompt)
            explanation = getattr(response, 'text', str(response)).strip()
            return explanation if explanation else None
        except Exception as e:
            logger.error(f"[AI] Gemini explanation error: {e}")
            return None

def get_ai_service():
    config = AIServiceConfig()
    if config.ai_provider == 'openai':
        return OpenAIService()
    if config.ai_provider in ('claude', 'anthropic'):
        # Lazy import Anthropic service implementation
        try:
            return AnthropicService()
        except Exception:
            logger.warning('[AI] Anthropic/Claude service not available, falling back to Gemini')
            return GoogleGeminiService()
    return GoogleGeminiService()


class AnthropicService:
    """Service for Anthropic Claude interactions (tries to use `anthropic` package)."""
    def __init__(self):
        self.config = AIServiceConfig()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            # Try to import official anthropic client
            from anthropic import Anthropic
            if self.config.claude_api_key:
                self.client = Anthropic(api_key=self.config.claude_api_key)
                logger.info(f"[AI] Anthropic client initialized: {self.config.claude_model}")
            else:
                logger.warning('[AI] CLAUDE_API_KEY not set; Anthropic service disabled')
        except Exception as e:
            logger.error(f"[AI] Failed to initialize Anthropic/Claude client: {e}")

    def generate_response(self, user_message: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.client:
            return None
        try:
            prompt = (system_prompt or self.config.system_prompt_base) + "\n\n"
            if context:
                prompt += f"Context: {context}\n\n"
            prompt += f"User: {user_message}"

            # Use client completion/create depending on client implementation
            try:
                resp = self.client.completions.create(model=self.config.claude_model, prompt=prompt, max_tokens=self.config.max_tokens, temperature=self.config.temperature)
                # Newer clients may return attribute 'completion' or 'text'
                result = getattr(resp, 'completion', None) or getattr(resp, 'text', None) or (resp.get('completion') if isinstance(resp, dict) else None)
                return result
            except Exception:
                # Try alternate method name
                resp = self.client.create_completion(model=self.config.claude_model, prompt=prompt, max_tokens=self.config.max_tokens, temperature=self.config.temperature)
                result = getattr(resp, 'completion', None) or getattr(resp, 'text', None) or (resp.get('completion') if isinstance(resp, dict) else None)
                return result
        except Exception as e:
            logger.error(f"[AI] Anthropic error: {e}")
            return None

    def generate_lesson_content(self, topic: str, level: str = "beginner") -> Optional[Dict]:
        if not self.client:
            return None
        try:
            prompt = f"""You are an educational assistant. Create a lesson about: '{topic}' (level: {level})\nReturn a JSON object with title, content, duration_minutes and summary."""
            try:
                resp = self.client.completions.create(model=self.config.claude_model, prompt=prompt, max_tokens=self.config.max_tokens, temperature=self.config.temperature)
                text = getattr(resp, 'completion', None) or getattr(resp, 'text', None) or (resp.get('completion') if isinstance(resp, dict) else str(resp))
            except Exception:
                resp = self.client.create_completion(model=self.config.claude_model, prompt=prompt, max_tokens=self.config.max_tokens, temperature=self.config.temperature)
                text = getattr(resp, 'completion', None) or getattr(resp, 'text', None) or (resp.get('completion') if isinstance(resp, dict) else str(resp))

            try:
                return json.loads(text)
            except Exception:
                import re
                m = re.search(r'\{.*\}', text, re.DOTALL)
                if m:
                    try:
                        return json.loads(m.group())
                    except Exception:
                        return None
                return None
        except Exception as e:
            logger.error(f"[AI] Anthropic lesson generation error: {e}")
            return None