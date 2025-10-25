"""
Logger utility for the FastAPI agent application.

This module provides a centralized logging configuration with structured logging,
proper formatting, and different log levels for development and production environments.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


class LoggerConfig:
    """Configuration class for application logging."""

    # Log levels mapping
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Default log format for development
    DEV_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # JSON format for production (structured logging)
    PROD_FORMAT = "%(message)s"


def configure_logging() -> None:
    """
    Configure application-wide logging settings.

    Sets up structured logging with appropriate formatters based on environment.
    Development: Human-readable console output
    Production: JSON structured logs for better parsing and monitoring
    """
    # Determine log level based on environment
    log_level = "DEBUG" if settings.DEBUG else "INFO"

    # Configure structlog
    if settings.APP_ENV == "production":
        # Production: JSON structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        formatter = logging.Formatter(LoggerConfig.PROD_FORMAT)
    else:
        # Development: Human-readable console logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        formatter = logging.Formatter(LoggerConfig.DEV_FORMAT)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LoggerConfig.LOG_LEVELS[log_level])

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LoggerConfig.LOG_LEVELS[log_level])
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for production (optional)
    if settings.APP_ENV == "production":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "agent.log")
        file_handler.setLevel(LoggerConfig.LOG_LEVELS[log_level])
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
    logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
    logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
    # AWS SDK loggers
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("botocore.auth").setLevel(logging.WARNING)
    logging.getLogger("botocore.hooks").setLevel(logging.WARNING)
    logging.getLogger("botocore.endpoint").setLevel(logging.WARNING)
    logging.getLogger("botocore.parsers").setLevel(logging.WARNING)
    logging.getLogger("botocore.retryhandler").setLevel(logging.WARNING)
    logging.getLogger("s3transfer").setLevel(logging.WARNING)
    # FastAPI/Starlette loggers
    logging.getLogger("python_multipart").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Configured structlog logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started", version="1.0.0")
        >>> logger.error("Database connection failed", error=str(e), retry_count=3)
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.

    Usage:
        class MyService(LoggerMixin):
            def process_data(self):
                self.logger.info("Processing data started")
                # ... processing logic ...
                self.logger.info("Processing data completed", records_processed=100)
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance for this class."""
        if not hasattr(self, "_logger"):
            logger_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
            self._logger = get_logger(logger_name)
        return self._logger


def log_request_response(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log HTTP request/response information.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID for request context
        **kwargs: Additional context to log
    """
    logger = get_logger("http")

    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        **kwargs,
    }

    if user_id:
        log_data["user_id"] = user_id

    if status_code >= 500:
        logger.error("HTTP request failed", **log_data)
    elif status_code >= 400:
        logger.warning("HTTP request error", **log_data)
    else:
        logger.info("HTTP request completed", **log_data)


def log_exception(
    exc: Exception,
    context: Dict[str, Any] | None = None,
    logger_name: str = "exception",
) -> None:
    """
    Log exception with context information.

    Args:
        exc: Exception instance
        context: Optional context dictionary
        logger_name: Logger name to use
    """
    logger = get_logger(logger_name)

    log_data = {
        "exception_type": exc.__class__.__name__,
        "exception_message": str(exc),
    }

    if context:
        log_data.update(context)

    logger.error("Exception occurred", **log_data, exc_info=True)


# Initialize logging when module is imported
configure_logging()

# Export main components
__all__ = [
    "configure_logging",
    "get_logger",
    "LoggerMixin",
    "log_request_response",
    "log_exception",
]
