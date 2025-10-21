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
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate batch embeddings - PARALLEL PROCESSING"""
        all_embeddings = []
        total = len(texts)
        
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_embeddings = self.model.encode(batch)
                all_embeddings.extend(batch_embeddings)
                logger.info(f"Processed {min(i + batch_size, total)}/{total} embeddings")
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size}: {str(e)}")
                raise EmbeddingError(f"Batch processing failed at {i}: {str(e)}")
        
        return all_embeddings
    
    def test_connection(self) -> bool:
        """Test embeddings"""
        try:
            self.generate_embedding("test")
            logger.info("✅ Embeddings working")
            return True
        except:
            return False
