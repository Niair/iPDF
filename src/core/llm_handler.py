"""
LLM Handler using Ollama (100% FREE)
UPDATED with better prompts and greeting handling
"""
import sys
from typing import Optional, Dict, Any, Generator
import ollama

from utils.logger import get_logger
from utils.exception import LLMError
from utils.config_loader import get_config

logger = get_logger(__name__)


class LLMHandler:
    """Handle LLM interactions using Ollama"""
    
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LLM handler
        
        Args:
            model: LLM model name (default: llama3.2)
            base_url: Ollama base URL
        """
        config = get_config()
        self.model = model or config.llm.model
        self.base_url = base_url or config.llm.base_url
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens
        
        # Initialize Ollama client
        self.client = ollama.Client(host=self.base_url)
        
        logger.info(f"LLMHandler initialized with model: {self.model}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated response text
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )
            
            return response['message']['content']
        
        except Exception as e:
            raise LLMError(f"Failed to generate response: {str(e)}", sys)
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate streaming response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Yields:
            Response chunks
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        
        except Exception as e:
            raise LLMError(f"Failed to generate streaming response: {str(e)}", sys)
    
    def generate_with_context(
        self,
        query: str,
        context: str,
        chat_history: Optional[list] = None
    ) -> str:
        """
        Generate response with context (for RAG) - IMPROVED VERSION
        
        Args:
            query: User query
            context: Retrieved context from vector store
            chat_history: Optional chat history
            
        Returns:
            Generated response
        """
        # Handle greetings and casual queries
        casual_queries = ['hi', 'hello', 'hey', 'yo', 'sup', 'greetings', 'howdy']
        if query.lower().strip() in casual_queries:
            return "Hello! 👋 I'm your PDF assistant. I can help you find information from your uploaded documents. What would you like to know?"
        
        system_prompt = """You are an intelligent PDF assistant helping users understand their documents.

**Your Role:**
- Answer questions based ONLY on the provided context from documents
- Be specific and cite relevant details
- Use clear formatting with bullet points for lists
- Mention page numbers when relevant

**Response Guidelines:**
1. If the answer is in the context: Provide a detailed, well-structured answer
2. If the answer is NOT in the context: Say "I couldn't find information about that in your documents."
3. For general questions about the document: Provide a comprehensive summary
4. Always be helpful and professional

**Formatting:**
- Use **bold** for important terms
- Use bullet points (•) for lists
- Keep answers concise but thorough
- Add spacing between sections for readability"""
        
        prompt = f"""**Context from Documents:**
{context}

---

**User Question:** {query}

**Instructions:** Based on the context above, provide a clear and helpful answer. If the information isn't in the context, say so politely."""
        
        return self.generate(prompt, system_prompt)
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama
        
        Returns:
            True if connection successful
        """
        try:
            response = self.generate("Hello")
            logger.info("✅ Ollama LLM service is working")
            return True
        
        except Exception as e:
            logger.error(f"❌ Ollama LLM connection failed: {str(e)}")
            return False
