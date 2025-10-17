"""
Centralized Logging Configuration
Production-ready logging with rotation and multiple handlers
"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggerSetup:
    """Setup and configure application logging"""
    
    _loggers = {}
    
    @classmethod
    def setup_logger(
        cls,
        name: str,
        log_dir: str = "logs",
        level: int = logging.INFO,
        log_format: Optional[str] = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Create and configure a logger with file and console handlers
        
        Args:
            name: Logger name (typically __name__)
            log_dir: Directory to store log files
            level: Logging level
            log_format: Custom log format string
            max_bytes: Max size before rotation
            backup_count: Number of backup files to keep
            
        Returns:
            Configured logger instance
        """
        # Return existing logger if already configured
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create logs directory
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Prevent duplicate handlers
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # Default format
        if log_format is None:
            log_format = (
                "[%(asctime)s] %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        
        formatter = logging.Formatter(
            log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler with Rotation
        log_file = log_path / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Cache logger
        cls._loggers[name] = logger
        
        logger.info(f"Logger initialized: {name}")
        return logger
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get existing logger or create new one with defaults"""
        if name not in cls._loggers:
            return cls.setup_logger(name)
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger instance"""
    return LoggerSetup.get_logger(name)
