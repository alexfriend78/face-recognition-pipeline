# logging_config.py
import structlog
import logging
import sys
import os
from datetime import datetime
from structlog.stdlib import LoggerFactory


def configure_logging():
    """Configure structured logging with structlog"""
    
    # Configure timestamper
    timestamper = structlog.processors.TimeStamper(fmt="ISO", utc=True)
    
    # Configure shared processors
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Configure for development vs production
    if os.getenv('ENVIRONMENT', 'development') == 'production':
        # Production: JSON formatting
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        # Development: Colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Set specific log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    return structlog.get_logger()


def get_logger(name: str = None):
    """Get a structured logger instance"""
    return structlog.get_logger(name)


# Custom context processors
def add_service_context(logger, name, event_dict):
    """Add service context to log entries"""
    event_dict['service'] = 'face-recognition-pipeline'
    event_dict['version'] = os.getenv('SERVICE_VERSION', '1.0.0')
    return event_dict


def add_request_context(logger, name, event_dict):
    """Add request context to log entries (for Flask)"""
    try:
        from flask import request, g
        if request:
            event_dict['request_id'] = getattr(g, 'request_id', 'unknown')
            event_dict['method'] = request.method
            event_dict['path'] = request.path
            event_dict['remote_addr'] = request.remote_addr
    except (ImportError, RuntimeError):
        # Not in Flask context or Flask not available
        pass
    return event_dict


def add_task_context(logger, name, event_dict):
    """Add Celery task context to log entries"""
    try:
        from celery import current_task
        if current_task and current_task.request:
            event_dict['task_id'] = current_task.request.id
            event_dict['task_name'] = current_task.name
            event_dict['task_retries'] = current_task.request.retries
    except (ImportError, RuntimeError):
        # Not in Celery context or Celery not available
        pass
    return event_dict


# Performance logging utilities
class LogExecutionTime:
    """Context manager for logging execution time"""
    
    def __init__(self, logger, operation_name: str, **context):
        self.logger = logger
        self.operation_name = operation_name
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info("Operation started", 
                        operation=self.operation_name, 
                        **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info("Operation completed successfully",
                           operation=self.operation_name,
                           duration_seconds=duration,
                           **self.context)
        else:
            self.logger.error("Operation failed",
                            operation=self.operation_name,
                            duration_seconds=duration,
                            error_type=exc_type.__name__,
                            error_message=str(exc_val),
                            **self.context)


def log_function_calls(logger):
    """Decorator to log function entry and exit"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            logger.debug("Function called", function=func_name, args_count=len(args), kwargs_count=len(kwargs))
            
            try:
                result = func(*args, **kwargs)
                logger.debug("Function completed", function=func_name)
                return result
            except Exception as e:
                logger.error("Function failed", function=func_name, error=str(e))
                raise
        return wrapper
    return decorator

