"""Structured logging setup for the Clinical Research Assistant."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record.

        Args:
            record: The log record to format.

        Returns:
            Formatted log string.
        """
        # Base format
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        name = record.name
        message = record.getMessage()

        # Build structured output
        output = f"{timestamp} | {level:8s} | {name} | {message}"

        # Add exception info if present
        if record.exc_info:
            output += f"\n{self.formatException(record.exc_info)}"

        return output


def setup_logging(
    level: str = "INFO",
    log_file: Path | str | None = None,
    structured: bool = True,
) -> logging.Logger:
    """Set up application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file.
        structured: Whether to use structured formatting.

    Returns:
        The root logger instance.
    """
    # Get numeric level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter with context support."""

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None):
        """Initialize the adapter.

        Args:
            logger: The underlying logger.
            context: Optional context dictionary.
        """
        super().__init__(logger, context or {})

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Process the logging call.

        Args:
            msg: The log message.
            kwargs: Additional keyword arguments.

        Returns:
            Tuple of (message, kwargs).
        """
        if self.extra:
            context_str = " ".join(f"{k}={v}" for k, v in self.extra.items())
            msg = f"{msg} | {context_str}"
        return msg, kwargs

    def with_context(self, **kwargs) -> "LoggerAdapter":
        """Create a new adapter with additional context.

        Args:
            **kwargs: Additional context key-value pairs.

        Returns:
            New LoggerAdapter with merged context.
        """
        new_context = {**self.extra, **kwargs}
        return LoggerAdapter(self.logger, new_context)


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """Get a logger with context information.

    Args:
        name: Logger name.
        **context: Context key-value pairs.

    Returns:
        LoggerAdapter with context.
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)
