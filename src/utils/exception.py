"""
Custom Exception Classes
Provides detailed error information with context
"""
import sys
import inspect
from typing import Optional


def get_error_details(error: Exception, error_detail: sys) -> str:
    """
    Extract detailed error information including file and line number
    
    Args:
        error: The exception that occurred
        error_detail: sys module for exception info
        
    Returns:
        Formatted error message with details
    """
    try:
        _, _, exc_tb = error_detail.exc_info()
        
        if exc_tb:
            file_name = exc_tb.tb_frame.f_code.co_filename
            line_number = exc_tb.tb_lineno
        else:
            # Fallback to inspect if traceback not available
            frame = inspect.currentframe()
            if frame and frame.f_back:
                file_name = frame.f_back.f_code.co_filename
                line_number = frame.f_back.f_lineno
            else:
                file_name = "unknown"
                line_number = 0
        
        error_message = (
            f"Error occurred in [{file_name}] "
            f"at line [{line_number}]: {str(error)}"
        )
        return error_message
    
    except Exception as e:
        return f"Error details unavailable: {str(e)} | Original error: {str(error)}"


class IPDFException(Exception):
    """Base exception class for iPDF application"""
    
    def __init__(self, error_message: str, error_detail: Optional[sys] = None):
        super().__init__(error_message)
        
        if error_detail:
            self.error_message = get_error_details(error_message, error_detail)
        else:
            self.error_message = str(error_message)
    
    def __str__(self):
        return self.error_message


class DocumentProcessingError(IPDFException):
    """Raised when PDF processing fails"""
    pass


class EmbeddingError(IPDFException):
    """Raised when embedding generation fails"""
    pass


class VectorStoreError(IPDFException):
    """Raised when vector store operations fail"""
    pass


class LLMError(IPDFException):
    """Raised when LLM interaction fails"""
    pass


class ConfigurationError(IPDFException):
    """Raised when configuration is invalid"""
    pass


class ValidationError(IPDFException):
    """Raised when data validation fails"""
    pass

class QueryError(IPDFException):
    """Raised when query or search operations fail"""
    pass

class ChatError(IPDFException):
    """Raised when chat operations fail"""
    pass
