import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures application-wide logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(log_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if already attached
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)

    # Suppress overly chatty 3rd party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return logging.getLogger("civicpulse")
