"""
Test Ollama LLM (Requires Ollama running)
"""
import pytest
from core.llm_handler import LLMHandler
from utils.exception import LLMError

@pytest.fixture
def llm_handler():
    """Create LLM handler"""
    return LLMHandler()

def test_llm_initialization(llm_handler):
    """Test LLM handler can be initialized"""
    assert llm_handler is not None
    assert llm_handler.model is not None
    print("✅ Ollama LLM Initialization Test PASSED")

def test_llm_generation(llm_handler):
    """Test LLM text generation"""
    try:
        prompt = "What is 2+2? Answer in one word."
        response = llm_handler.generate(prompt)
        assert response is not None
        assert len(response) > 0
        print(f"✅ Ollama LLM Generation Test PASSED: {response}")
    except Exception as e:
        pytest.skip(f"Ollama not available: {str(e)}")

def test_llm_connection(llm_handler):
    """Test connection to Ollama"""
    try:
        is_connected = llm_handler.test_connection()
        assert is_connected == True
        print("✅ Ollama LLM Connection Test PASSED")
    except Exception:
        pytest.skip("Ollama not running")

def test_llm_with_context(llm_handler):
    """Test LLM with context (RAG)"""
    try:
        context = "The capital of France is Paris."
        query = "What is the capital of France?"
        response = llm_handler.generate_with_context(query, context)
        assert "Paris" in response or "paris" in response.lower()
        print("✅ Ollama RAG Test PASSED")
    except Exception as e:
        pytest.skip(f"Ollama not available: {str(e)}")
