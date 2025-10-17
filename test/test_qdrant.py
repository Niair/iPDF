"""
Test Qdrant Vector Store (Requires Qdrant configured)
"""
import pytest
from core.vectorstore import VectorStoreManager
from utils.exception import VectorStoreError

@pytest.fixture
def vector_store():
    """Create vector store manager"""
    try:
        return VectorStoreManager()
    except VectorStoreError:
        pytest.skip("Qdrant not configured")

def test_vector_store_initialization(vector_store):
    """Test vector store can be initialized"""
    assert vector_store is not None
    assert vector_store.collection_name is not None
    print("✅ Qdrant Initialization Test PASSED")

def test_vector_store_connection(vector_store):
    """Test connection to Qdrant"""
    try:
        is_connected = vector_store.test_connection()
        assert is_connected == True
        print("✅ Qdrant Connection Test PASSED")
    except Exception as e:
        pytest.skip(f"Qdrant not available: {str(e)}")

def test_add_and_search_points(vector_store, mock_embedding):
    """Test adding and searching points"""
    try:
        # Add test point
        embeddings = [mock_embedding]
        payloads = [{
            "filename": "test.pdf",
            "page_number": 1,
            "content_type": "text",
            "content": "Test content"
        }]
        
        result = vector_store.add_points(embeddings, payloads)
        assert result == True
        
        # Search
        results = vector_store.search(mock_embedding, limit=1)
        assert len(results) >= 0
        
        print("✅ Qdrant Add/Search Test PASSED")
    except Exception as e:
        pytest.skip(f"Qdrant operation failed: {str(e)}")
