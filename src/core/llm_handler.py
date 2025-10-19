"""
LLM Handler - Switchable between Google Gemini and Groq
"""
import sys
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from utils.logger import get_logger
from utils.exception import LLMError

logger = get_logger(__name__)


class LLMHandler:
    """LLM Handler supporting multiple providers"""
    
    def __init__(self, provider: str = "google"):
        """
        Initialize LLM handler
        
        Args:
            provider: "google" or "groq"
        """
        self.provider = provider
        self.client = None
        self.model = None
        
        logger.info(f"Initializing LLMHandler with provider: {provider}")
        
        if provider == "google":
            if not self._init_google():
                raise LLMError("Google Gemini initialization failed")
        elif provider == "groq":
            if not self._init_groq():
                raise LLMError("Groq initialization failed")
        else:
            raise LLMError(f"Unknown provider: {provider}")
        
        logger.info(f"✅ LLMHandler ready with {provider}")
    
    def _init_google(self) -> bool:
        """Initialize Google Gemini"""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY not set")
                return False
            
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            self.model = genai.GenerativeModel(model_name)
            
            # Test
            response = self.model.generate_content("test")
            logger.info(f"✅ Google Gemini ({model_name}) connected")
            return True
        
        except Exception as e:
            logger.error(f"Google init failed: {str(e)}")
            return False
    
    def _init_groq(self) -> bool:
        """Initialize Groq"""
        try:
            from groq import Groq
            
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.error("GROQ_API_KEY not set")
                return False
            
            self.client = Groq(api_key=api_key)
            self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
            
            # Test
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            logger.info(f"✅ Groq ({self.model}) connected")
            return True
        
        except Exception as e:
            logger.error(f"Groq init failed: {str(e)}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response"""
        try:
            if self.provider == "google":
                return self._generate_google(prompt, system_prompt)
            else:  # groq
                return self._generate_groq(prompt, system_prompt)
        except Exception as e:
            raise LLMError(f"Generation failed: {str(e)}", sys)
    
    def _generate_google(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate with Google Gemini"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self.model.generate_content(full_prompt)
        return response.text
    
    def _generate_groq(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate with Groq"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=2048
        )
        # FIX: choices is a LIST, need [0] to get first choice
        return response.choices[0].message.content


    
    def generate_with_context(self, query: str, context: str) -> str:
        """Generate with RAG context"""
        
        # Handle greetings
        greetings = ['hi', 'hello', 'hey', 'yo', 'sup']
        if query.lower().strip() in greetings:
            return "👋 **Hello!** I'm your PDF assistant. Ask me anything about your documents!"
        
        system_prompt = """You are an expert PDF assistant. Provide clear, well-formatted responses.

**Formatting Rules:**
- Use **bold** for important terms
- Use bullet points (•) for lists
- Add proper spacing between sections
- Keep paragraphs short (2-3 sentences)
- Use headers (##) for main sections

**Response Guidelines:**
- Answer based ONLY on provided context
- Be specific and cite page numbers when possible
- If answer not in context: "I couldn't find that information in your documents."
- Format all responses in clean Markdown"""
        
        prompt = f"""**Context from Documents:**
{context}

---

**User Question:** {query}

**Instructions:** Provide a well-formatted, structured answer based on the context above."""
        
        return self.generate(prompt, system_prompt)
    
    def test_connection(self) -> bool:
        """Test connection"""
        try:
            self.generate("test")
            return True
        except:
            return False
    
    def get_provider(self) -> str:
        """Get current provider"""
        return self.provider
