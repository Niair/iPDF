"""
Embedding Generator - Optimized with Batch Processing
"""
import sys
from typing import List
from sentence_transformers import SentenceTransformer

from utils.logger import get_logger
from utils.exception import EmbeddingError

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings with optimized batch processing"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize embedding model"""
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"✅ Embedding model loaded: {model_name} (dim={self.embedding_dim})")
        except Exception as e:
            raise EmbeddingError(f"Failed to load embedding model: {str(e)}", sys)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate single embedding"""
        try:
            if not text or not text.strip():
                raise EmbeddingError("Cannot generate embedding for empty text")
            
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            raise EmbeddingError(f"Embedding generation failed: {str(e)}", sys)
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings in batches (OPTIMIZED)
        
        Args:
            texts: List of texts to embed
            batch_size: Size of each batch (default: 32)
            show_progress: Whether to log progress
        
        Returns:
            List of embeddings
        """
        if not texts:
            raise EmbeddingError("No texts provided for embedding")
        
        all_embeddings = []
        total = len(texts)
        
        logger.info(f"Generating {total} embeddings in batches of {batch_size}")
        
        try:
            for i in range(0, total, batch_size):
                batch = texts[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total + batch_size - 1) // batch_size
                
                try:
                    # Process batch
                    batch_embeddings = self.model.encode(
                        batch,
                        show_progress_bar=False,
                        convert_to_numpy=True
                    )
                    
                    # Convert to list and extend
                    all_embeddings.extend([emb.tolist() for emb in batch_embeddings])
                    
                    if show_progress:
                        processed = min(i + batch_size, total)
                        logger.info(f"Batch {batch_num}/{total_batches}: {processed}/{total} embeddings")
                
                except Exception as e:
                    logger.error(f"Failed to process batch {batch_num}: {str(e)}")
                    raise EmbeddingError(f"Batch {batch_num} failed: {str(e)}", sys)
            
            logger.info(f"✅ Generated {len(all_embeddings)} embeddings successfully")
            return all_embeddings
        
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise EmbeddingError(f"Batch processing failed: {str(e)}", sys)
