"""
Chat Service - Handle conversational interactions
UPDATED with better error handling and response quality
"""
import sys
from typing import Optional, Dict, Any
import time

from utils.logger import get_logger
from utils.exception import LLMError
from core.llm_handler import LLMHandler
from services.query_service import QueryService
from models.chat import ChatResponse

logger = get_logger(__name__)


class ChatService:
    """Service for chat interactions with improved response quality"""
    
    def __init__(self):
        """Initialize chat service"""
        self.llm = LLMHandler()
        self.query_service = QueryService()
        logger.info("ChatService initialized")
    
    def chat(
        self, 
        query: str, 
        filename: Optional[str] = None, 
        use_rag: bool = True
    ) -> ChatResponse:
        """
        Handle chat query with RAG and improved responses
        
        Args:
            query: User query
            filename: Optional filter by specific filename
            use_rag: Whether to use retrieval augmented generation
            
        Returns:
            ChatResponse with answer and sources
        """
        try:
            start_time = time.time()
            
            logger.info(f"Processing query: '{query}' (RAG: {use_rag})")
            
            if use_rag:
                # Retrieve relevant context from documents
                context = self.query_service.get_context_for_query(
                    query,
                    limit=5,  # Get top 5 most relevant chunks
                    filename=filename
                )
                
                # Generate response with context
                answer = self.llm.generate_with_context(query, context)
                
                # Get sources for citation
                search_results = self.query_service.search(
                    query, 
                    limit=3,  # Show top 3 sources
                    filename=filename
                )
                
                sources = [
                    {
                        "filename": result['payload']['filename'],
                        "page": result['payload']['page_number'],
                        "score": result['score']
                    }
                    for result in search_results
                ]
            else:
                # Generate without RAG (direct LLM response)
                answer = self.llm.generate(query)
                sources = []
            
            processing_time = time.time() - start_time
            
            logger.info(f"Response generated in {processing_time:.2f}s")
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                metadata={
                    "rag_used": use_rag, 
                    "filename_filter": filename,
                    "num_sources": len(sources)
                },
                processing_time=processing_time
            )
        
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise LLMError(f"Chat failed: {str(e)}", sys)
