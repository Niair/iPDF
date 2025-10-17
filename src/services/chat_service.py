"""Chat Service - Simplified"""
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
    """Service for chat interactions"""
    
    def __init__(self):
        """Initialize chat service"""
        self.llm = LLMHandler()
        self.query_service = QueryService()
        logger.info("ChatService initialized")
    
    def chat(self, query: str, filename: Optional[str] = None, use_rag: bool = True) -> ChatResponse:
        """Handle chat query"""
        try:
            start_time = time.time()
            
            if use_rag:
                # Get context
                context = self.query_service.get_context_for_query(
                    query,
                    limit=5,
                    filename=filename
                )
                
                # Generate response
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
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                metadata={},
                processing_time=processing_time
            )
        
        except Exception as e:
            raise LLMError(f"Chat failed: {str(e)}", sys)
