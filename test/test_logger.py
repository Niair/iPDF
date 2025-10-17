"""
Test Logger functionality
"""
import pytest
from utils.logger import get_logger, LoggerSetup

def test_logger_creation():
    """Test logger can be created"""
    logger = get_logger("test_logger")
    assert logger is not None
    assert logger.name == "test_logger"

def test_logger_singleton():
    """Test logger returns same instance"""
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")
    assert logger1 is logger2

def test_logger_logging():
    """Test logger can log messages"""
    logger = get_logger("test_logging")
    try:
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        assert True
    except Exception as e:
        pytest.fail(f"Logging failed: {str(e)}")

def test_logger_with_custom_format():
    """Test logger with custom format"""
    custom_format = "%(levelname)s - %(message)s"
    logger = LoggerSetup.setup_logger(
        "test_custom",
        log_format=custom_format
    )
    assert logger is not None
