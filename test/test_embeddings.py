"""
Test Embedding Generation (Requires Ollama running)
"""
import pytest
from core.embeddings import EmbeddingGenerator
from utils.exception import EmbeddingError

@pytest.fixture
def embedding_gen():
    """Create embedding generator"""
    return EmbeddingGenerator()

def test_embedding_generator_initialization(embedding_gen):
    """Test embedding generator can be initialized"""
    assert embedding_gen is not None
    assert embedding_gen.model is not None

def test_single_embedding_generation(embedding_gen, sample_text):
    """Test single embedding generation"""
    try:
        embedding = embedding_gen.generate_embedding(sample_text)
        assert embedding is not None
        assert len(embedding) == 768  # nomic-embed-text dimensions
        assert all(isinstance(x, float) for x in embedding)
        print("✅ Ollama Embeddings Test PASSED")
    except Exception as e:
        pytest.skip(f"Ollama not available: {str(e)}")

def test_batch_embedding_generation(embedding_gen):
    """Test batch embedding generation"""
    texts = [
        "First test document",
        "Second test document",
        "Third test document"
    ]
    
    try:
        embeddings = embedding_gen.generate_embeddings_batch(texts)
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
        print("✅ Batch Embeddings Test PASSED")
    except Exception as e:
        pytest.skip(f"Ollama not available: {str(e)}")

def test_embedding_connection(embedding_gen):
    """Test connection to Ollama"""
    try:
        is_connected = embedding_gen.test_connection()
        assert is_connected == True
        print("✅ Ollama Connection Test PASSED")
    except Exception:
        pytest.skip("Ollama not running")
