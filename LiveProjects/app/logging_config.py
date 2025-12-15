"""
Structured logging configuration with JSON formatting and observability features.
"""
import logging
import sys
import structlog
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from .config import settings


class ProductionFormatter(logging.Formatter):
    """Custom formatter for production logging with consistent structure."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with additional context."""
        # Add application context
        if not hasattr(record, 'service'):
            record.service = settings.app_name
        if not hasattr(record, 'version'):
            record.version = settings.app_version
        if not hasattr(record, 'environment'):
            record.environment = settings.environment
            
        return super().format(record)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Clear existing handlers
    logging.root.handlers = []
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.root.setLevel(log_level)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    if settings.log_format.lower() == "json":
        # JSON formatter for production
        formatter = jsonlogger.JsonFormatter(
            fmt=(
                "%(asctime)s %(name)s %(levelname)s %(message)s "
                "%(service)s %(version)s %(environment)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(ProductionFormatter())
        handler.setFormatter(formatter)
    else:
        # Plain formatter for development
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
    
    # Add handler to root logger
    logging.root.addHandler(handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer() if settings.log_format.lower() == "json" 
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set specific logger levels
    if settings.is_production:
        # Reduce noise in production
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    else:
        # More verbose in development
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Request ID middleware context
def add_request_context(request_id: str, user_id: str = None) -> Dict[str, Any]:
    """Add request context for logging."""
    context = {"request_id": request_id}
    if user_id:
        context["user_id"] = user_id
    return context