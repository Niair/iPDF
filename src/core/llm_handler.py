"""
LLM Handler using Ollama (100% FREE)
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
        Generate response with context (for RAG)
        
        Args:
            query: User query
            context: Retrieved context from vector store
            chat_history: Optional chat history
            
        Returns:
            Generated response
        """
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided context from PDF documents.

Guidelines:
1. Answer based ONLY on the provided context
2. If the answer is not in the context, say "I don't have enough information to answer that"
3. Preserve formatting for tables, formulas, and lists
4. Cite specific parts of the context when relevant
5. Be concise but thorough"""
        
        prompt = f"""Context from documents:
{context}

User Question: {query}

Please provide a detailed answer based on the context above."""
        
        return self.generate(prompt, system_prompt)
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama
        
        Returns:
            True if connection successful
        """
        try:
            response = self.generate("Hello, test message")
            logger.info("✅ Ollama LLM service is working")
            return True
        
        except Exception as e:
            logger.error(f"❌ Ollama LLM connection failed: {str(e)}")
            return False
