"""
Test Configuration Loader
"""
import pytest
from utils.config_loader import ConfigLoader, get_config
from utils.exception import ConfigurationError

def test_config_loader_initialization():
    """Test config loader can be initialized"""
    loader = ConfigLoader()
    assert loader is not None

def test_config_loading():
    """Test configuration can be loaded"""
    try:
        config = get_config()
        assert config is not None
        assert config.app.name is not None
        assert config.embeddings.model is not None
    except ConfigurationError as e:
        pytest.skip(f"Config file not found: {str(e)}")

def test_config_structure():
    """Test configuration structure"""
    try:
        config = get_config()
        assert hasattr(config, 'app')
        assert hasattr(config, 'logging')
        assert hasattr(config, 'document')
        assert hasattr(config, 'embeddings')
        assert hasattr(config, 'vectorstore')
        assert hasattr(config, 'llm')
    except ConfigurationError:
        pytest.skip("Config file not found")
