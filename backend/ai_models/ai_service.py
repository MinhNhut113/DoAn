"""AI Service for handling LLM interactions (OpenAI, Google Gemini, etc.)"""
import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger(__name__)

class AIServiceConfig:
    """Configuration for AI Services"""
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        # Gemini API configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-pro')
        
        # For backward compatibility
        self.google_api_key = self.gemini_api_key or os.getenv('GOOGLE_API_KEY')
        
        # AI provider selection
        self.ai_provider = os.getenv('AI_PROVIDER', 'gemini').lower()
        
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '1000'))
        self.language = os.getenv('AI_LANGUAGE', 'vi')  # Vietnamese by default
        
        self.system_prompt_base = """Bạn là một trợ lý giáo dục thông minh, chuyên giúp sinh viên hiểu bài học.
        
Hãy:
- Trả lời bằng tiếng Việt
- Giải thích rõ ràng và chi tiết
- Sử dụng các ví dụ thực tế
- Chia nhỏ thông tin phức tạp
- Khuyến khích học tập
- Cấp độ ngôn ngữ phù hợp với sinh viên"""


class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.config = AIServiceConfig()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            import openai
            if self.config.openai_api_key:
                openai.api_key = self.config.openai_api_key
                self.client = openai.OpenAI(api_key=self.config.openai_api_key)
                logger.info("[AI] OpenAI client initialized")
            else:
                logger.warning("[AI] OpenAI API key not found")
        except ImportError:
            logger.warning("[AI] OpenAI library not installed")
        except Exception as e:
            logger.error(f"[AI] Failed to initialize OpenAI: {e}")
    
    def generate_response(self, user_message: str, context: Optional[str] = None, 
                         system_prompt: Optional[str] = None) -> Optional[str]:
        """Generate AI response using OpenAI"""
        if not self.client:
            logger.error("[AI] OpenAI client not available")
            return None
        
        try:
            messages = []
            
            # Add system prompt
            if not system_prompt:
                system_prompt = self.config.system_prompt_base
            messages.append({"role": "system", "content": system_prompt})
            
            # Add context if provided
            if context:
                messages.append({"role": "system", "content": f"Ngữ cảnh bài học: {context}"})
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Try the modern client method first, then fall back to older interfaces
            response = None
            try:
                response = self.client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    top_p=0.95
                )
            except Exception:
                try:
                    # Fallback: openai.ChatCompletion.create
                    import openai as _openai
                    if hasattr(_openai, 'ChatCompletion'):
                        response = _openai.ChatCompletion.create(
                            model=self.config.openai_model,
                            messages=messages,
                            temperature=self.config.temperature,
                            max_tokens=self.config.max_tokens
                        )
                    elif hasattr(_openai, 'Completion'):
                        # Older completion API (may not support messages)
                        response = _openai.Completion.create(
                            model=self.config.openai_model,
                            prompt=messages[-1]['content'],
                            temperature=self.config.temperature,
                            max_tokens=self.config.max_tokens
                        )
                except Exception as e:
                    logger.error(f"[AI] OpenAI call failed: {e}")

            # Extract text from response in a robust way
            def _extract_text(resp):
                if resp is None:
                    return None
                try:
                    # new style: resp.choices[0].message.content
                    if hasattr(resp, 'choices'):
                        choice0 = resp.choices[0]
                        # object with message
                        if hasattr(choice0, 'message') and hasattr(choice0.message, 'content'):
                            return choice0.message.content
                        # object with text
                        if hasattr(choice0, 'text'):
                            return choice0.text
                    # dict-like
                    try:
                        if isinstance(resp, dict):
                            ch = resp.get('choices') and resp['choices'][0]
                            if ch:
                                # message.content
                                if isinstance(ch, dict) and 'message' in ch and 'content' in ch['message']:
                                    return ch['message']['content']
                                if isinstance(ch, dict) and 'text' in ch:
                                    return ch['text']
                    except Exception:
                        pass
                    # generic text attribute
                    if hasattr(resp, 'text'):
                        return resp.text
                except Exception:
                    return None
                return None

            result = _extract_text(response)
            if result:
                logger.info(f"[AI] Generated response from OpenAI")
                return result
            
        except Exception as e:
            logger.error(f"[AI] OpenAI error: {e}")
            return None
    
    def generate_quiz_questions(self, topic: str, lesson_content: str, 
                               num_questions: int = 5, difficulty: int = 2) -> Optional[List[Dict]]:
        """Generate quiz questions based on lesson content"""
        if not self.client:
            return None
        
        try:
            prompt = f"""Hãy tạo {num_questions} câu hỏi trắc nghiệm dựa trên nội dung bài học sau.

Chủ đề: {topic}

Nội dung bài học:
{lesson_content}

Yêu cầu:
- Cấp độ khó: {difficulty}/5
- Mỗi câu hỏi phải có 4 lựa chọn (A, B, C, D)
- Mỗi câu hỏi phải có lời giải thích
- Định dạng JSON: {{"questions": [{{"question": "...", "options": ["A: ...", "B: ...", "C: ...", "D: ..."], "correct_answer": 0, "explanation": "..."}}]}}
"""
            
            response = None
            try:
                response = self.client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[
                        {"role": "system", "content": "Bạn là một giáo viên giỏi tạo câu hỏi trắc nghiệm chất lượng."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=3000
                )
            except Exception:
                try:
                    import openai as _openai
                    if hasattr(_openai, 'ChatCompletion'):
                        response = _openai.ChatCompletion.create(
                            model=self.config.openai_model,
                            messages=[
                                {"role": "system", "content": "Bạn là một giáo viên giỏi tạo câu hỏi trắc nghiệm chất lượng."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.8,
                            max_tokens=3000
                        )
                    else:
                        response = None
                except Exception as e:
                    logger.error(f"[AI] OpenAI question generation fallback failed: {e}")

            # Extract response text robustly
            result_text = None
            try:
                if response is not None:
                    # try same extractor as above
                    if hasattr(response, 'choices'):
                        choice0 = response.choices[0]
                        if hasattr(choice0, 'message') and hasattr(choice0.message, 'content'):
                            result_text = choice0.message.content
                        elif hasattr(choice0, 'text'):
                            result_text = choice0.text
                    elif isinstance(response, dict):
                        ch = response.get('choices') and response['choices'][0]
                        if ch and isinstance(ch, dict):
                            if 'message' in ch and 'content' in ch['message']:
                                result_text = ch['message']['content']
                            elif 'text' in ch:
                                result_text = ch['text']
                    elif hasattr(response, 'text'):
                        result_text = response.text
            except Exception:
                result_text = None
            
            # Extract JSON from response
            try:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group())
                    logger.info(f"[AI] Generated {len(result_json.get('questions', []))} quiz questions")
                    return result_json.get('questions', [])
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"[AI] Failed to parse question JSON: {e}")
                return None
            
        except Exception as e:
            logger.error(f"[AI] Question generation error: {e}")
            return None


class GoogleGeminiService:
    """Service for Google Gemini API interactions"""
    
    def __init__(self):
        self.config = AIServiceConfig()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            api_key = self.config.gemini_api_key
            
            if not api_key:
                logger.warning("[AI] Gemini API key not found in GEMINI_API_KEY or GOOGLE_API_KEY")
                return
            
            genai.configure(api_key=api_key)
            self.client = genai
            logger.info(f"[AI] Google Gemini client initialized with model: {self.config.gemini_model}")
            
        except ImportError:
            logger.warning("[AI] Google Generative AI library not installed. Install: pip install google-generativeai")
        except Exception as e:
            logger.error(f"[AI] Failed to initialize Gemini: {e}")
    
    def generate_response(self, user_message: str, context: Optional[str] = None, 
                         system_prompt: Optional[str] = None) -> Optional[str]:
        """Generate AI response using Google Gemini"""
        if not self.client:
            logger.error("[AI] Gemini client not available")
            return None
        
        try:
            if not system_prompt:
                system_prompt = self.config.system_prompt_base
            
            # For Gemini, combine system prompt with user message
            full_message = f"{system_prompt}\n\n"
            
            if context:
                full_message += f"Ngữ cảnh: {context}\n\n"
            
            full_message += f"Câu hỏi: {user_message}"
            
            model = self.client.GenerativeModel(
                model_name=self.config.gemini_model
            )
            
            response = model.generate_content(
                full_message,
                generation_config={
                    'temperature': self.config.temperature,
                    'max_output_tokens': self.config.max_tokens,
                }
            )
            
            result = response.text
            logger.info("[AI] Generated response from Gemini")
            return result
            
        except Exception as e:
            logger.error(f"[AI] Gemini error: {e}")
            return None
    
    def generate_quiz_questions(self, topic: str, lesson_content: str, 
                               num_questions: int = 5, difficulty: int = 2) -> Optional[List[Dict]]:
        """Generate quiz questions using Gemini"""
        if not self.client:
            return None
        
        try:
            prompt = f"""Hãy tạo {num_questions} câu hỏi trắc nghiệm dựa trên nội dung bài học sau.

Chủ đề: {topic}

Nội dung bài học:
{lesson_content}

Yêu cầu:
- Cấp độ khó: {difficulty}/5
- Mỗi câu hỏi phải có 4 lựa chọn (A, B, C, D)
- Mỗi câu hỏi phải có lời giải thích
- Định dạng JSON: {{"questions": [{{"question": "...", "options": ["A: ...", "B: ...", "C: ...", "D: ..."], "correct_answer": 0, "explanation": "..."}}]}}
"""
            
            model = self.client.GenerativeModel(
                model_name=self.config.gemini_model
            )
            
            response = model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group())
                    logger.info(f"[AI] Generated {len(result_json.get('questions', []))} quiz questions with Gemini")
                    return result_json.get('questions', [])
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"[AI] Failed to parse question JSON: {e}")
                return None
            
        except Exception as e:
            logger.error(f"[AI] Gemini question generation error: {e}")
            return None


class AIServiceFactory:
    """Factory for creating AI service instances"""
    
    _services = {}
    
    @staticmethod
    def get_service(service_type: str = None) -> Optional[Any]:
        """Get AI service instance
        
        Args:
            service_type: 'openai', 'gemini', or None to use AI_PROVIDER from .env
        """
        # If no service type specified, get from config
        if service_type is None:
            config = AIServiceConfig()
            service_type = config.ai_provider
        
        service_type = service_type.lower()
        
        if service_type not in AIServiceFactory._services:
            if service_type == 'openai':
                AIServiceFactory._services[service_type] = OpenAIService()
            elif service_type == 'gemini':
                AIServiceFactory._services[service_type] = GoogleGeminiService()
            else:
                logger.warning(f"[AI] Unknown service type: {service_type}, defaulting to openai")
                AIServiceFactory._services[service_type] = OpenAIService()
        
        return AIServiceFactory._services[service_type]


# Convenience functions
def get_ai_service(service_type: str = None) -> Optional[Any]:
    """Get AI service instance
    
    Args:
        service_type: 'openai', 'gemini', or None to use configured provider
    """
    return AIServiceFactory.get_service(service_type)


def generate_ai_response(user_message: str, context: Optional[str] = None, 
                        service_type: str = None) -> Optional[str]:
    """Generate AI response using configured provider
    
    Args:
        user_message: User query
        context: Optional lesson context
        service_type: 'openai', 'gemini', or None to use configured provider
    """
    service = get_ai_service(service_type)
    if service:
        return service.generate_response(user_message, context)
    return None


def generate_quiz_questions(topic: str, lesson_content: str, 
                           num_questions: int = 5, difficulty: int = 2,
                           service_type: str = None) -> Optional[List[Dict]]:
    """Generate quiz questions using configured provider
    
    Args:
        topic: Quiz topic
        lesson_content: Lesson content to base questions on
        num_questions: Number of questions to generate
        difficulty: Difficulty level (1-5)
        service_type: 'openai', 'gemini', or None to use configured provider
    """
    service = get_ai_service(service_type)
    if service and hasattr(service, 'generate_quiz_questions'):
        return service.generate_quiz_questions(topic, lesson_content, num_questions, difficulty)
    return None
