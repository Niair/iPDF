"""
Fast Embeddings using sentence-transformers
10x faster than Ollama
"""
import sys
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

from utils.logger import get_logger
from utils.exception import EmbeddingError

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings FAST using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with pre-trained model"""
        try:
            self.model = SentenceTransformer(f"sentence-transformers/{model_name}")
            self.dimensions = 384  # MiniLM dimensions
            logger.info(f"Embeddings initialized: {model_name}")
        except Exception as e:
            raise EmbeddingError(f"Failed to load model: {str(e)}", sys)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate single embedding - FAST"""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            raise EmbeddingError(f"Embedding failed: {str(e)}", sys)
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings - PARALLEL PROCESSING"""
        try:
            logger.info(f"Generating {len(texts)} embeddings in parallel...")
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=True,
                batch_size=32  # Process 32 at once
            )
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Batch embedding failed: {str(e)}", sys)
    
    def test_connection(self) -> bool:
        """Test embeddings"""
        try:
            self.generate_embedding("test")
            logger.info("✅ Embeddings working")
            return True
        except:
            return False
