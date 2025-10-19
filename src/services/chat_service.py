"""
Chat Service - FAST responses (1-3 seconds target)
"""
import sys
import time
from typing import Optional

from utils.logger import get_logger
from utils.exception import LLMError
from core.llm_handler import LLMHandler
from services.query_service import QueryService
from models.chat import ChatResponse

logger = get_logger(__name__)


class ChatService:
    """Fast chat service"""
    
    def __init__(self, llm_provider: str = "groq"):
        """Initialize with fast LLM"""
        self.llm = LLMHandler(provider=llm_provider)
        self.query_service = QueryService()
        logger.info(f"ChatService initialized with {llm_provider}")
    
    def chat(self, query: str, filename: Optional[str] = None, use_rag: bool = True) -> ChatResponse:
        """Handle chat - OPTIMIZED for speed"""
        try:
            start_time = time.time()
            
            if use_rag:
                # Fast context retrieval (< 0.2s)
                context = self.query_service.get_context_for_query(
                    query,
                    limit=3,  # Reduced for speed
                    filename=filename
                )
                
                # Fast LLM response (0.5-1.5s with Groq)
                answer = self.llm.generate_with_context(query, context)
                
                # Get sources
                search_results = self.query_service.search(query, limit=3, filename=filename)
                sources = [
                    {
                        "filename": r['payload']['filename'],
                        "page": r['payload']['page_number'],
                        "score": r['score']
                    }
                    for r in search_results
                ]
            else:
                answer = self.llm.generate(query)
                sources = []
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Response in {processing_time:.2f}s")
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                metadata={},
                processing_time=processing_time
            )
        
        except Exception as e:
            raise LLMError(f"Chat failed: {str(e)}", sys)
