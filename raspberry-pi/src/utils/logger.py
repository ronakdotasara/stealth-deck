"""
================================================================================
logger.py - Logging Utilities for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Logging utilities for Stealth Deck with colored output, file rotation,
and structured logging support.

Features:
- Colored console output
- File rotation
- Multiple log levels
- Structured logging
- Performance logging
- Log filtering

================================================================================
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import time


try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


class PerformanceLogger:
    """Context manager for performance logging."""
    
    def __init__(self, logger: logging.Logger, operation: str):
        """
        Initialize performance logger.
        
        Args:
            logger: Logger instance
            operation: Operation description
        """
        self.logger = logger
        self.operation = operation
        self.start_time = 0.0
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log."""
        elapsed = time.time() - self.start_time
        self.logger.debug(f"{self.operation} took {elapsed*1000:.2f}ms")


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10485760,
    backup_count: int = 5,
    console_output: bool = True,
    colored: bool = True
) -> logging.Logger:
    """
    Setup logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Log level
        max_bytes: Max log file size before rotation
        backup_count: Number of backup files to keep
        console_output: Enable console output
        colored: Enable colored console output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if colored and COLORLOG_AVAILABLE:
            console_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s %(message)s',
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            console_formatter = logging.Formatter(
                '%(levelname)-8s %(name)s - %(message)s'
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogFilter(logging.Filter):
    """Custom log filter for excluding specific messages."""
    
    def __init__(self, exclude_patterns: list):
        """
        Initialize filter.
        
        Args:
            exclude_patterns: List of patterns to exclude
        """
        super().__init__()
        self.exclude_patterns = exclude_patterns
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record.
        
        Args:
            record: Log record
            
        Returns:
            True if record should be logged
        """
        message = record.getMessage()
        return not any(pattern in message for pattern in self.exclude_patterns)


if __name__ == '__main__':
    logger = setup_logger(
        'test_logger',
        log_file='/tmp/test.log',
        level=logging.DEBUG,
        colored=True
    )
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    with PerformanceLogger(logger, "Test operation"):
        time.sleep(0.1)

