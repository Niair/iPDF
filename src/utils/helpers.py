"""
Helper Utility Functions
Common utility functions used across the application
"""
import hashlib
import os
import sys
from pathlib import Path
from typing import Union, Any
import dill
import pickle

from utils.logger import get_logger
from utils.exception import IPDFException

logger = get_logger(__name__)


def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory: Directory path
        
    Returns:
        Path object
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_hash(file_content: bytes) -> str:
    """
    Generate SHA256 hash of file content
    
    Args:
        file_content: File content as bytes
        
    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(file_content).hexdigest()


def save_object(obj: Any, file_path: Union[str, Path]) -> None:
    """
    Save Python object to file using dill
    
    Args:
        obj: Object to save
        file_path: Path to save file
    """
    try:
        file_path = Path(file_path)
        ensure_dir(file_path.parent)
        
        with open(file_path, 'wb') as f:
            dill.dump(obj, f)
        
        logger.info(f"Object saved to {file_path}")
    
    except Exception as e:
        raise IPDFException(f"Failed to save object: {str(e)}", sys)


def load_object(file_path: Union[str, Path]) -> Any:
    """
    Load Python object from file
    
    Args:
        file_path: Path to file
        
    Returns:
        Loaded object
    """
    try:
        with open(file_path, 'rb') as f:
            obj = pickle.load(f)
        
        logger.info(f"Object loaded from {file_path}")
        return obj
    
    except Exception as e:
        raise IPDFException(f"Failed to load object: {str(e)}", sys)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
