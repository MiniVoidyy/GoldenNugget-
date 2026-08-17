import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """Configure application-wide logging."""
    logger = logging.getLogger("GoldenNugget")
    logger.setLevel(level)
    logger.propagate = False

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass  # Fail silently if file logging fails

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging.getLogger(f"GoldenNugget.{name}")
    return logging.getLogger("GoldenNugget")


# Initialize default logger
_log_file = os.environ.get("GOLDENNUGGET_LOG_FILE")
if _log_file:
    _logger = setup_logging(_log_file)
else:
    # Only console logging by default
    _logger = setup_logging(level=logging.WARNING)  # Quiet by default


# Context manager for operation logging
class LoggedOperation:
    """Context manager for logging operation start/end/errors."""

    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context

    def __enter__(self):
        self.logger.info("Starting %s | %s", self.operation, self._fmt_context())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                "Failed %s | %s | error=%s",
                self.operation,
                self._fmt_context(),
                exc_val,
                exc_info=(exc_type, exc_val, None)
            )
        else:
            self.logger.info("Completed %s | %s", self.operation, self._fmt_context())
        return False  # Don't suppress exceptions

    def _fmt_context(self) -> str:
        return " | ".join(f"{k}={v}" for k, v in self.context.items())


# Convenience function
def log_exception(logger: logging.Logger, msg: str, *args, **kwargs):
    """Log an exception with full traceback."""
    logger.exception(msg, *args, **kwargs)