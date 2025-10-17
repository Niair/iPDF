"""
Query Service - Handle vector search and retrieval
"""
import sys
from typing import List, Dict, Any, Optional

from utils.logger import get_logger
from utils.exception import VectorStoreError
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager

logger = get_logger(__name__)


class QueryService:
    """Service for querying vector store"""
    
    def __init__(self):
        """Initialize query service"""
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        logger.info("QueryService initialized")
    
    def search(
        self,
        query: str,
        limit: int = 5,
        filename: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant content
        
        Args:
            query: User query
            limit: Number of results
            filename: Optional filter by filename
            
        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            logger.info(f"Searching for: {query}")
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            # Build filter
            filter_dict = None
            if filename:
                filter_dict = {"filename": filename}
            
            # Search vector store
            results = self.vector_store.search(
                query_vector=query_embedding,
                limit=limit,
                filter_dict=filter_dict
            )
            
            logger.info(f"Found {len(results)} results")
            return results
        
        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}", sys)
    
    def get_context_for_query(
        self,
        query: str,
        limit: int = 5,
        filename: Optional[str] = None
    ) -> str:
        """
        Get formatted context for RAG
        
        Args:
            query: User query
            limit: Number of results
            filename: Optional filter by filename
            
        Returns:
            Formatted context string
        """
        results = self.search(query, limit, filename)
        
        if not results:
            return "No relevant context found."
        
        # Format context
        context_parts = []
        for i, result in enumerate(results, 1):
            payload = result['payload']
            context_parts.append(
                f"[Source {i}] From {payload['filename']}, Page {payload['page_number']}:\n"
                f"{payload['content']}\n"
            )
        
        return "\n---\n".join(context_parts)
