import anthropic
import os
from typing import Optional, List, Dict
import json
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # FIX: Corrected model name to match Anthropic's naming convention
        self.model = "claude-3-5-haiku-20241022"
        self.max_tokens = 4096
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using Claude API"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            raise
    
    def generate_questions(self, topic: str, difficulty: int = 1, num_questions: int = 5) -> List[Dict]:
        """Generate quiz questions for a topic"""
        prompt = f"""Generate {num_questions} multiple-choice questions about: {topic}
        
Difficulty level: {difficulty}/5

Return ONLY a JSON array with this exact format:
[
    {{
        "question_text": "Question here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "Why this answer is correct"
    }}
]

Requirements:
- Each question must have exactly 4 options
- correct_answer must be an integer index (0-3)
- Questions should be clear and unambiguous
- Explanations should be educational
"""
        
        response = self.generate_response(prompt)
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                return questions[:num_questions]
            else:
                raise ValueError("No valid JSON found in response")
        except Exception as e:
            logger.error(f"Error parsing questions: {str(e)}")
            logger.error(f"Raw response: {response}")
            raise
    
    def generate_explanation(self, question: str, user_answer: str, correct_answer: str) -> str:
        """Generate an explanation for why an answer is correct/incorrect"""
        prompt = f"""Explain why the answer is correct or incorrect:

Question: {question}
User's Answer: {user_answer}
Correct Answer: {correct_answer}

Provide a clear, educational explanation in Vietnamese. Be encouraging if the answer was wrong."""
        
        return self.generate_response(prompt)
    
    def generate_recommendations(self, user_history: List[Dict], course_content: List[Dict]) -> List[Dict]:
        """Generate personalized learning recommendations"""
        history_text = "\n".join([
            f"- {h.get('lesson_title', 'Unknown')}: Score {h.get('score', 0)}%"
            for h in user_history
        ])
        
        content_text = "\n".join([
            f"- {c.get('lesson_title', 'Unknown')} (ID: {c.get('lesson_id')})"
            for c in course_content
        ])
        
        prompt = f"""Based on this learning history:
{history_text}

Available lessons:
{content_text}

Recommend 3-5 lessons the student should focus on next. Consider:
- Topics where they struggled
- Natural progression of difficulty
- Building on strong areas

Return ONLY a JSON array with this format:
[
    {{
        "lesson_id": 123,
        "lesson_title": "Lesson name",
        "reason": "Why this lesson is recommended"
    }}
]
"""
        
        response = self.generate_response(prompt)
        
        try:
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            logger.error(f"Error parsing recommendations: {str(e)}")
            return []
    
    def chat(self, message: str, context: Optional[str] = None) -> str:
        """Handle general chat queries about course content"""
        system_prompt = """You are a helpful AI tutor for an online learning platform. 
Answer questions about course content, provide study tips, and encourage learning.
Always respond in Vietnamese unless asked otherwise."""
        
        if context:
            full_prompt = f"Context: {context}\n\nQuestion: {message}"
        else:
            full_prompt = message
        
        return self.generate_response(full_prompt, system_prompt)


# Singleton instance
_ai_service_instance = None

def get_ai_service() -> AIService:
    """Get or create AIService singleton instance"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance