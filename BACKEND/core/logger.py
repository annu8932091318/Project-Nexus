"""
JSON Logger configuration for Project Nexus backend.
Provides structured logging with file, function, and line number tracking.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger


class ContextFilter(logging.Filter):
    """Add context information (file, function, line) to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Enhance log record with context information."""
        record.filename = record.filename
        record.funcName = record.funcName
        record.lineno = record.lineno
        record.module = record.module
        return True


def setup_logger(
    name: Optional[str] = None,
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = True,
) -> logging.Logger:
    """
    Set up a JSON logger with file and console handlers.

    Args:
        name: Logger name (defaults to root logger if None)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console_output: Whether to log to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.propagate = False  # Prevent propagation to root logger

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # JSON formatter with all useful fields
    json_format = (
        "%(timestamp)s %(levelname)s %(name)s %(filename)s %(funcName)s %(lineno)d %(message)s"
    )
    json_formatter = jsonlogger.JsonFormatter(
        json_format,
        timestamp=True,
        rename_fields={
            "timestamp": "timestamp",
            "levelname": "level",
            "name": "logger_name",
            "filename": "file",
            "funcName": "function",
            "lineno": "line",
            "message": "message"
        },
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        console_handler.addFilter(ContextFilter())
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setFormatter(json_formatter)
        file_handler.addFilter(ContextFilter())
        logger.addHandler(file_handler)

    return logger


# Global logger instance
_root_logger: Optional[logging.Logger] = None
_initialized = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Logger instance
    """
    global _root_logger
    if _root_logger is None:
        from pathlib import Path
        import os

        log_dir = Path(os.getenv("NEXUS_LOG_DIR", "logs"))
        log_file = log_dir / "nexus.log"
        log_level = os.getenv("NEXUS_LOG_LEVEL", "INFO")

        _root_logger = setup_logger(
            name="nexus",
            log_level=log_level,
            log_file=log_file,
            console_output=True,
        )

    if name and name != "nexus":
        # For child loggers, use the root logger's handlers
        child_logger = logging.getLogger(name)
        child_logger.setLevel(logging.INFO)
        if not child_logger.handlers:
            child_logger.handlers = _root_logger.handlers
        child_logger.propagate = False
        return child_logger
    
    return _root_logger


def init_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """
    Initialize logging system for the application.

    Args:
        log_level: Logging level
        log_dir: Directory for log files
    """
    global _root_logger, _initialized
    
    if _initialized:
        return
    
    log_file = Path(log_dir) / "nexus.log"
    _root_logger = setup_logger(
        name="nexus",
        log_level=log_level,
        log_file=log_file,
        console_output=True,
    )
    logger = get_logger("nexus.init")
    logger.info("Logging system initialized", extra={"log_dir": str(log_file), "log_level": log_level})
    _initialized = True
    
    # Force flush
    for handler in _root_logger.handlers:
        handler.flush()
