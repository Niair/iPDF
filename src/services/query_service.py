"""
Query Service - With Relevance Filtering
"""
import sys
from typing import List, Dict, Any, Optional, Tuple

from utils.logger import get_logger
from utils.exception import QueryError
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager

logger = get_logger(__name__)


class QueryService:
    """Query service with relevance filtering"""
    
    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        logger.info("QueryService initialized (with relevance filtering)")
    
    def search(
        self,
        query: str,
        limit: int = 5,
        filename: Optional[str] = None,
        min_score: float = 0.1  # Relevance threshold (lowered for better retrieval)
    ) -> List[Dict[str, Any]]:
        """
        Search with relevance filtering
        
        Args:
            query: Search query
            limit: Max results to return
            filename: Optional filename filter
            min_score: Minimum relevance score (0.0-1.0)
        
        Returns:
            Filtered list of relevant results
        """
        try:
            logger.info(f"Searching: '{query}' (min_score={min_score})")
            
            # Generate embedding
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            # Build filter
            filter_dict = None
            if filename:
                filter_dict = {"filename": filename}
                logger.info(f"Filtering by filename: {filename}")
            
            # Search with 3x results for filtering
            all_results = self.vector_store.search(
                query_embedding=query_embedding,
                limit=limit * 3,
                filter_dict=filter_dict
            )
            
            logger.info(f"Initial results: {len(all_results)}")
            
            # Log actual scores for debugging
            if all_results:
                scores = [r['score'] for r in all_results]
                logger.info(f"Score range: {min(scores):.4f} - {max(scores):.4f}")
                logger.info(f"Top 5 scores: {[f'{s:.4f}' for s in sorted(scores, reverse=True)[:5]]}")
            
            # Filter by relevance score
            filtered_results = [
                r for r in all_results 
                if r['score'] >= min_score
            ][:limit]
            
            if not filtered_results:
                logger.warning(f"No results above threshold {min_score}")
                # Return top results even if below threshold for debugging
                logger.info("Returning top results below threshold for debugging")
                return all_results[:limit]
            
            logger.info(f"Filtered to {len(filtered_results)} relevant results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise QueryError(f"Search failed: {str(e)}", sys)
    
    def get_context_for_query(
        self,
        query: str,
        limit: int = 5,
        filename: Optional[str] = None,
        min_score: float = 0.1
    ) -> str:
        """Get context with relevance filtering"""
        try:
            results = self.search(query, limit=limit, filename=filename, min_score=min_score)
            
            if not results:
                return "No relevant context found in the documents."
            
            # Build context
            context_parts = []
            for idx, result in enumerate(results):
                payload = result['payload']
                context_parts.append(
                    f"[Source {idx + 1} - {payload['filename']}, Page {payload['page_number']}]\n"
                    f"{payload['content']}\n"
                )
            
            context = "\n---\n\n".join(context_parts)
            logger.info(f"Built context: {len(context)} chars from {len(results)} sources")
            
            return context
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {str(e)}")
            raise QueryError(f"Failed to get context: {str(e)}", sys)
