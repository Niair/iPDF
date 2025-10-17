"""
Vector Store Management using Qdrant (100% FREE Cloud Tier)
"""
import sys
import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
import uuid

from utils.logger import get_logger
from utils.exception import VectorStoreError
from utils.config_loader import get_config
from models.qdrant_schemas import QdrantPayload, QdrantPoint

logger = get_logger(__name__)


class VectorStoreManager:
    """Manage Qdrant vector store operations"""
    
    def __init__(self):
        """Initialize Qdrant client"""
        config = get_config()
        
        # Get Qdrant connection details from environment
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if not qdrant_url or not qdrant_api_key:
            raise VectorStoreError(
                "QDRANT_URL and QDRANT_API_KEY must be set in .env file"
            )
        
        try:
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=60
            )
            
            self.collection_name = config.vectorstore.collection_name
            self.vector_size = config.vectorstore.vector_size
            self.distance_metric = Distance.COSINE
            
            logger.info(f"Connected to Qdrant cloud: {qdrant_url}")
            
            # Ensure collection exists
            self._ensure_collection()
        
        except Exception as e:
            raise VectorStoreError(f"Failed to connect to Qdrant: {str(e)}", sys)
    
    def _ensure_collection(self):
        """Ensure collection exists, create if not"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=self.distance_metric
                    )
                )
                logger.info(f"✅ Collection created: {self.collection_name}")
            else:
                logger.info(f"✅ Collection exists: {self.collection_name}")
        
        except Exception as e:
            raise VectorStoreError(f"Failed to ensure collection: {str(e)}", sys)
    
    def add_points(self, embeddings: List[List[float]], payloads: List[Dict[str, Any]]) -> bool:
        """
        Add points (vectors + payloads) to collection
        
        Args:
            embeddings: List of embedding vectors
            payloads: List of payload dictionaries
            
        Returns:
            True if successful
        """
        try:
            if len(embeddings) != len(payloads):
                raise ValueError("Number of embeddings must match number of payloads")
            
            points = []
            for embedding, payload in zip(embeddings, payloads):
                point_id = str(uuid.uuid4())
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ Added {len(points)} points to Qdrant")
            return True
        
        except Exception as e:
            raise VectorStoreError(f"Failed to add points: {str(e)}", sys)
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            filter_dict: Optional filters (e.g., {"filename": "doc.pdf"})
            
        Returns:
            List of search results with scores
        """
        try:
            # Build filter if provided
            query_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)
            
            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                })
            
            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}", sys)
    
    def delete_by_filename(self, filename: str) -> bool:
        """
        Delete all points for a specific file
        
        Args:
            filename: Filename to delete
            
        Returns:
            True if successful
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="filename",
                            match=MatchValue(value=filename)
                        )
                    ]
                )
            )
            logger.info(f"✅ Deleted points for file: {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete points: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to Qdrant
        
        Returns:
            True if connection successful
        """
        try:
            collections = self.client.get_collections()
            logger.info(f"✅ Qdrant connection successful. Collections: {len(collections.collections)}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {str(e)}")
            return False
