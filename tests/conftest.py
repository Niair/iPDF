"""
Pytest configuration and fixtures
"""
import pytest
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def sample_text():
    """Sample text for testing"""
    return "This is a test document about artificial intelligence and machine learning."

@pytest.fixture
def sample_pdf_path():
    """Sample PDF path for testing"""
    return "tests/data/sample.pdf"

@pytest.fixture
def mock_embedding():
    """Mock embedding vector"""
    return [0.1] * 768
