"""
Query Service - Handle vector search with relevance filtering
UPDATED with better filtering and formatting
"""
import sys
from typing import List, Dict, Any, Optional

from utils.logger import get_logger
from utils.exception import VectorStoreError
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager

logger = get_logger(__name__)


class QueryService:
    """Service for querying vector store with improved relevance filtering"""
    
    def __init__(self):
        """Initialize query service"""
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        logger.info("QueryService initialized")
    
    def enhance_query(self, query: str) -> str:
        """Enhance vague queries to get better search results"""
        
        # Map vague queries to retrieval-friendly scientific-paper sections
        # Keep enhancements specific enough to hit real sections across most PDFs
        query_enhancements = {
            # Summaries
            "provide a comprehensive summary": "abstract introduction conclusion",
            "summarize": "abstract introduction conclusion",
            "summary": "abstract introduction conclusion",
            
            # Key points / topics
            "what are the key points": "conclusion key findings",
            "key points": "conclusion key findings",
            "what are the main topics": "introduction overview",
            "main topics": "introduction overview",
            
            # Details  
            "give detailed information": "method methodology results",
            "details": "method methodology results",
            
            # Tables/Figures
            "explain table": "table",
            "explain figure": "figure",
            "explain diagram": "figure diagram",
            "table 1": "table 1",
            "figure 1": "figure 1",
        }
        
        query_lower = query.lower().strip()
        
        # Check for enhanced queries
        for pattern, enhancement in query_enhancements.items():
            if pattern in query_lower:
                logger.info(f"Enhancing query: '{query}' -> '{enhancement}'")
                return enhancement
        
        return query


    def search(self, query: str, limit: int = 5, filename: Optional[str] = None, min_score: float = 0.3 ) -> List[Dict[str, Any]]: # LOWERED from 0.5 for better recall
        """Search with improved parameters"""
        try:
            logger.info(f"Searching for: '{query}' (limit={limit}, min_score={min_score})")
            
            # Generate query embedding
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            # Build filter (pass through to vectorstore which turns this into a Qdrant Filter)
            filter_dict = None
            if filename:
                filter_dict = {"filename": filename}
                logger.info(f"Filtering by filename: {filename}")
            
            # IMPROVED: Get more results initially for filtering
            all_results = self.vector_store.search(
                query_embedding=query_embedding,
                limit=limit * 3,  # Get 3x for filtering
                filter_dict=filter_dict
            )
            
            logger.info(f"Vector search returned {len(all_results)} results")
            
            # Filter by score and deduplicate
            seen_content = set()
            filtered_results = []
            
            for result in all_results:
                content = result['payload']['content']
                score = result['score']
                
                # Skip if score too low
                if score < min_score:
                    continue
                
                # Skip similar/duplicate content  
                content_hash = content[:100]  # First 100 chars as hash
                if content_hash in seen_content:
                    logger.debug(f"Skipping duplicate content (score: {score:.3f})")
                    continue
                
                seen_content.add(content_hash)
                filtered_results.append(result)
                
                logger.debug(f"Added result: {result['payload']['filename']} p{result['payload']['page_number']} (score: {score:.3f})")
                
                if len(filtered_results) >= limit:
                    break
            
            logger.info(f"Final filtered results: {len(filtered_results)}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise VectorStoreError(f"Search failed: {str(e)}", sys)

    
    def get_context_for_query(self, query: str, limit: int = 5,filename: Optional[str] = None) -> str:
        """Get context with query enhancement"""
        
        # ENHANCED: Boost search for broad questions
        enhanced_query = self.enhance_query(query)
        
        # For broad questions, get more results
        search_limit = limit
        if enhanced_query != query:
            search_limit = min(limit * 2, 10)  # Double the results for enhanced queries
            logger.info(f"Using enhanced search with limit: {search_limit}")
        
        results = self.search(enhanced_query, limit=search_limit, filename=filename)
        
        if not results:
            # Try original query if enhanced didn't work
            if enhanced_query != query:
                logger.info("Enhanced search failed, trying original query")
                results = self.search(query, limit=limit, filename=filename)
            
            if not results:
                return "No relevant context found in the documents."
        
        # Build context with better structure
        context_parts = []
        
        for idx, result in enumerate(results):
            payload = result['payload']
            
            context_parts.append(
                f"[Source {idx + 1} - {payload['filename']}, Page {payload['page_number']}]\n"
                f"{payload['content']}\n"
            )
        
        full_context = "\n---\n\n".join(context_parts)
        logger.info(f"Built context from {len(results)} sources, {len(full_context)} chars")
        
        return full_context

