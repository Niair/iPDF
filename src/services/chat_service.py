"""
Chat Service - Multimodal with Gemini Vision
"""
import sys
import time
from typing import Optional, List

from utils.logger import get_logger
from core.gemini_vision_handler import GeminiVisionHandler
from services.query_service import QueryService
from models.chat import ChatResponse

logger = get_logger(__name__)


class ChatService:
    """Multimodal chat service with vision"""
    
    def __init__(self):
        """Initialize with Gemini Vision"""
        self.llm = GeminiVisionHandler()
        self.query_service = QueryService()
        logger.info("ChatService initialized (multimodal + vision)")
    
    def chat(
        self,
        query: str,
        filename: Optional[str] = None,
        use_rag: bool = True
    ) -> ChatResponse:
        """
        Chat with multimodal support (text + images)
        
        Args:
            query: User question
            filename: Optional filename filter
            use_rag: Whether to use RAG
        
        Returns:
            ChatResponse with answer and sources
        """
        try:
            start_time = time.time()
            
            if use_rag:
                # Search for relevant content
                logger.info(f"Searching for: '{query}'")
                results = self.query_service.search(
                    query,
                    limit=8,  # Get more results for multimodal
                    filename=filename
                )
                
                # Separate text and images
                text_parts = []
                images_base64 = []
                sources = []
                
                for result in results:
                    payload = result['payload']
                    content_type = payload.get('content_type', 'text')
                    
                    if content_type == 'text':
                        text_parts.append(
                            f"[Page {payload['page_number']}]\n{payload['content']}"
                        )
                    
                    elif content_type == 'image' and 'image_base64' in payload:
                        images_base64.append(payload['image_base64'])
                        logger.info(f"Added image from page {payload['page_number']}")
                    
                    sources.append({
                        "filename": payload['filename'],
                        "page": payload['page_number'],
                        "type": content_type,
                        "score": result['score']
                    })
                
                # Build text context
                text_context = "\n\n---\n\n".join(text_parts) if text_parts else ""
                
                logger.info(f"Context: {len(text_parts)} text chunks, {len(images_base64)} images")
                
                # Generate multimodal response
                answer = self.llm.generate_with_multimodal_context(
                    query=query,
                    text_context=text_context,
                    images_base64=images_base64
                )
                
            else:
                # Direct generation
                answer = self.llm.generate_with_multimodal_context(query, "", [])
                sources = []
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Response generated in {processing_time:.2f}s")
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                metadata={
                    "text_chunks": len(text_parts) if use_rag else 0,
                    "images_used": len(images_base64) if use_rag else 0
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
