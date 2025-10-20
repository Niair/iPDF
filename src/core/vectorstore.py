"""
Vector Store Manager - With Auto-Fix for Dimension Mismatch and Enhanced Search
"""
import sys
import os
import uuid
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)

from utils.logger import get_logger
from utils.exception import VectorStoreError
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


class VectorStoreManager:
    """Qdrant vector store manager with auto-fix and enhanced search"""

    def __init__(self):
        """Initialize Qdrant client"""
        try:
            # Get configuration
            qdrant_url = os.getenv("QDRANT_URL")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            self.collection_name = os.getenv("QDRANT_COLLECTION", "iPDF")

            if not qdrant_url or not qdrant_api_key:
                raise VectorStoreError("QDRANT_URL or QDRANT_API_KEY not set in .env", sys)

            # Connect to Qdrant
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=60
            )

            logger.info(f"Connected to Qdrant cloud: {qdrant_url}")

            # Ensure collection exists with correct dimensions
            self._ensure_collection()
            # Ensure payload indexes used by filters exist
            self._ensure_payload_indexes()

        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Qdrant: {str(e)}", sys)

    def _ensure_collection(self):
        """Ensure collection exists with correct dimensions (AUTO-FIX)"""
        expected_dim = 384  # Match your embedding model

        try:
            # Try to get existing collection info (robust to client typing)
            info = self.client.get_collection(self.collection_name)
            vectors_obj = getattr(getattr(getattr(info, "config", None), "params", None), "vectors", None)
            existing_dim = getattr(vectors_obj, "size", None)
            logger.info(f"Existing collection: {self.collection_name} ({existing_dim} dimensions)")

            if existing_dim != expected_dim:
                logger.warning("=" * 60)
                logger.warning("⚠️ DIMENSION MISMATCH DETECTED!")
                logger.warning(f"Existing: {existing_dim} dimensions")
                logger.warning(f"Expected: {expected_dim} dimensions")
                logger.warning("Recreating collection...")
                logger.warning("=" * 60)

                # Delete and recreate
                self.client.delete_collection(self.collection_name)
                logger.info("✅ Deleted old collection")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=expected_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created new collection ({expected_dim} dimensions)")
            else:
                logger.info(f"✅ Collection dimensions correct ({expected_dim})")

        except Exception:
            # Collection doesn't exist - create it
            logger.info(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=expected_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created collection ({expected_dim} dimensions)")

    def _ensure_payload_indexes(self) -> None:
        """Create payload indexes required for filtering (idempotent)."""
        try:
            # filename: keyword index
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="filename",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                logger.info("✅ Created payload index for 'filename' (KEYWORD)")
            except Exception:
                # Index may already exist; avoid noisy logs
                logger.debug("Payload index for 'filename' already exists")

            # page_number: integer index (optional, helps sorting/filtering later)
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="page_number",
                    field_schema=PayloadSchemaType.INTEGER,
                )
                logger.info("✅ Created payload index for 'page_number' (INTEGER)")
            except Exception:
                logger.debug("Payload index for 'page_number' already exists")

        except Exception as e:
            # Do not hard-fail app launch; searching without index still works except for filtered queries
            logger.warning(f"⚠️ Failed to ensure payload indexes: {str(e)}")

    def add_points(self, embeddings: List[List[float]], payloads: List[Dict[str, Any]]) -> bool:
        """Add vectors to Qdrant"""
        try:
            if not embeddings or not payloads:
                logger.error("No embeddings or payloads to add")
                return False

            if len(embeddings) != len(payloads):
                logger.error(f"Mismatch: {len(embeddings)} embeddings, {len(payloads)} payloads")
                return False

            points = []
            for embedding, payload in zip(embeddings, payloads):
                point_id = str(uuid.uuid4())
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))

            logger.info(f"Upserting {len(points)} points to Qdrant...")
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"✅ Added {len(points)} points to {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add points: {str(e)}")
            raise VectorStoreError(f"Failed to add points: {str(e)}", sys)

    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional metadata filter"""
        try:
            params = {
                "collection_name": self.collection_name,
                "query_vector": query_embedding,
                "limit": limit,
            }

            # Build a proper Qdrant filter if filename is provided
            if filter_dict and "filename" in filter_dict:
                filename_value = filter_dict["filename"]
                params["query_filter"] = Filter(
                    must=[
                        FieldCondition(
                            key="filename",
                            match=MatchValue(value=filename_value),
                        )
                    ]
                )

            results = self.client.search(**params)
            return [
                {"score": r.score, "payload": r.payload}
                for r in results
            ]

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise VectorStoreError(f"Search failed: {str(e)}", sys)

    def test_connection(self) -> bool:
        """Test Qdrant connection"""
        try:
            cols = self.client.get_collections()
            logger.info(f"✅ Qdrant connected. Collections: {len(cols.collections)}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
