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
    
    def _extract_search_terms(self, query: str) -> str:
        """Extract key search terms from user query"""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'create', 'a', 'comprehensive', 'summary', 'of', 'the', 'document', 'including',
            'main', 'topics', 'and', 'themes', 'discussed', 'key', 'findings', 'arguments',
            'or', 'claims', 'important', 'data', 'examples', 'evidence', 'presented',
            'conclusions', 'recommendations', 'organize', 'your', 'with', 'clear', 'headers',
            'bullet', 'points', 'cite', 'page', 'numbers', 'what', 'is', 'about', 'tell', 'me',
            'can', 'you', 'please', 'help', 'me', 'understand', 'explain', 'describe'
        }
        
        # Split query into words and filter
        words = query.lower().split()
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # If no key terms found, try to extract meaningful phrases
        if not key_terms:
            # Look for common patterns
            if 'summary' in query.lower():
                return 'summary overview main topics'
            elif 'about' in query.lower():
                return 'about main topics content'
            elif 'explain' in query.lower():
                return 'explain main concepts'
            else:
                return query
        
        # Return top 5-10 key terms
        return ' '.join(key_terms[:10])
    
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
                # Create a simpler search query for better retrieval
                # Extract key terms from the user query
                search_query = self._extract_search_terms(query)
                logger.info(f"Searching for: '{search_query}' (from: '{query}')")
                results = self.query_service.search(
                    search_query,
                    limit=8,  # Get more results for multimodal
                    filename=filename
                )
                
                # If no results, try a broader search
                if not results:
                    logger.info("No results found, trying broader search...")
                    broader_queries = [
                        "main topics content",
                        "introduction overview",
                        "abstract summary",
                        "key concepts"
                    ]
                    
                    for broader_query in broader_queries:
                        results = self.query_service.search(
                            broader_query,
                            limit=8,
                            filename=filename
                        )
                        if results:
                            logger.info(f"Found results with broader query: '{broader_query}'")
                            break
                
                # Final fallback: get any content from the document
                if not results:
                    logger.info("No results found with any query, getting any content from document...")
                    results = self.query_service.search(
                        "content text",
                        limit=5,
                        filename=filename
                    )
                
                # Separate text and images
                text_parts = []
                images_base64 = []
                sources = []
                
                logger.info(f"Retrieved {len(results)} results from search")
                
                for result in results:
                    payload = result['payload']
                    content_type = payload.get('content_type', 'text')
                    
                    if content_type == 'text':
                        content_preview = payload['content'][:100] + "..." if len(payload['content']) > 100 else payload['content']
                        logger.info(f"Text chunk from {payload['filename']} page {payload['page_number']}: {content_preview}")
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
