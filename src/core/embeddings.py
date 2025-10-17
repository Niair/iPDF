"""
Embedding Generation using Ollama (100% FREE)
Uses nomic-embed-text model for semantic embeddings
"""
import sys
from typing import List, Optional
import ollama

from utils.logger import get_logger
from utils.exception import EmbeddingError
from utils.config_loader import get_config

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using Ollama"""
    
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize embedding generator
        
        Args:
            model: Embedding model name (default: nomic-embed-text)
            base_url: Ollama base URL (default: http://localhost:11434)
        """
        config = get_config()
        self.model = model or config.embeddings.model
        self.base_url = base_url or config.embeddings.base_url
        self.dimensions = config.embeddings.dimensions
        
        # Initialize Ollama client
        self.client = ollama.Client(host=self.base_url)
        
        logger.info(f"EmbeddingGenerator initialized with model: {self.model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            List of floats (embedding vector)
        """
        try:
            response = self.client.embeddings(
                model=self.model,
                prompt=text
            )
            
            embedding = response['embedding']
            
            # Validate dimensions
            if len(embedding) != self.dimensions:
                raise EmbeddingError(
                    f"Expected {self.dimensions} dimensions, got {len(embedding)}"
                )
            
            return embedding
        
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}", sys)
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{len(texts)} embeddings")
            
            except Exception as e:
                logger.error(f"Error generating embedding for text {i}: {str(e)}")
                # Add zero vector as placeholder
                embeddings.append([0.0] * self.dimensions)
        
        logger.info(f"Generated {len(embeddings)} embeddings total")
        return embeddings
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama
        
        Returns:
            True if connection successful
        """
        try:
            # Try to generate a test embedding
            test_text = "test connection"
            embedding = self.generate_embedding(test_text)
            logger.info("✅ Ollama embedding service is working")
            return True
        
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {str(e)}")
            return False
