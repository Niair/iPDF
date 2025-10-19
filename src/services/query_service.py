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
    
    def search(
        self,
        query: str,
        limit: int = 5,
        filename: Optional[str] = None,
        min_score: float = 0.3  # Minimum relevance threshold
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant content with quality filtering
        
        Args:
            query: User query
            limit: Number of results to return
            filename: Optional filter by specific filename
            min_score: Minimum relevance score (0-1), default 0.3 = 30%
            
        Returns:
            List of relevant search results
        """
        try:
            logger.info(f"Searching for: '{query}'")
            
            # Generate query embedding
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            # Build filename filter if specified
            filter_dict = None
            if filename:
                filter_dict = {"filename": filename}
                logger.info(f"Filtering by filename: {filename}")
            
            # Search vector store (get more results than needed for filtering)
            all_results = self.vector_store.search(
                query_embedding=query_embedding,
                limit=limit * 3,  # Get 3x more to filter out low-quality results
                filter_dict=filter_dict
            )
            
            # Filter by minimum relevance score
            filtered_results = [
                result for result in all_results 
                if result['score'] >= min_score
            ][:limit]  # Take top N after filtering
            
            logger.info(
                f"Found {len(filtered_results)} high-quality results "
                f"(filtered from {len(all_results)} total)"
            )
            
            return filtered_results
        
        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}", sys)
    
    def get_context_for_query(
        self,
        query: str,
        limit: int = 5,
        filename: Optional[str] = None
    ) -> str:
        """
        Get formatted context string for RAG with improved formatting
        
        Args:
            query: User query
            limit: Number of context chunks to retrieve
            filename: Optional filter by filename
            
        Returns:
            Formatted context string ready for LLM
        """
        results = self.search(query, limit, filename)
        
        if not results:
            return "No relevant information found in the documents."
        
        # Build formatted context with clear structure
        context_parts = []
        
        for i, result in enumerate(results, 1):
            payload = result['payload']
            score = result['score']
            
            # Format each source clearly
            context_parts.append(
                f"--- SOURCE {i} ---\n"
                f"Document: {payload['filename']}\n"
                f"Page: {payload['page_number']}\n"
                f"Relevance: {score:.1%}\n"
                f"Content:\n{payload['content']}\n"
            )
        
        full_context = "\n" + "\n".join(context_parts)
        
        logger.info(f"Generated context from {len(results)} sources")
        return full_context
