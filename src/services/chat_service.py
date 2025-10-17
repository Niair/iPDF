"""
Chat Service - Handle conversational interactions
"""
import sys
from typing import Optional, Dict, Any
import time

from utils.logger import get_logger
from utils.exception import LLMError
from core.llm_handler import LLMHandler
from services.query_service import QueryService
from models.chat import ChatHistory, MessageRole, ChatResponse

logger = get_logger(__name__)


class ChatService:
    """Service for chat interactions"""
    
    def __init__(self):
        """Initialize chat service"""
        self.llm = LLMHandler()
        self.query_service = QueryService()
        self.chat_history = ChatHistory()
        logger.info("ChatService initialized")
    
    def chat(
        self,
        query: str,
        filename: Optional[str] = None,
        use_rag: bool = True
    ) -> ChatResponse:
        """
        Handle chat query with RAG
        
        Args:
            query: User query
            filename: Optional filter by filename
            use_rag: Use retrieval augmented generation
            
        Returns:
            ChatResponse
        """
        try:
            start_time = time.time()
            
            # Add user message to history
            self.chat_history.add_message(MessageRole.USER, query)
            
            if use_rag:
                # Get context from vector store
                context = self.query_service.get_context_for_query(
                    query,
                    limit=5,
                    filename=filename
                )
                
                # Generate response with context
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
                # Generate without RAG
                answer = self.llm.generate(query)
                sources = []
            
            # Add assistant message to history
            self.chat_history.add_message(MessageRole.ASSISTANT, answer)
            
            processing_time = time.time() - start_time
            
            response = ChatResponse(
                answer=answer,
                sources=sources,
                metadata={"rag_used": use_rag, "filename_filter": filename},
                processing_time=processing_time
            )
            
            logger.info(f"Chat response generated in {processing_time:.2f}s")
            return response
        
        except Exception as e:
            raise LLMError(f"Chat failed: {str(e)}", sys)
    
    def clear_history(self):
        """Clear chat history"""
        self.chat_history = ChatHistory()
        logger.info("Chat history cleared")
