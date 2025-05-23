"""
Logging configuration for the Railway Ticket Reservation System
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure loggers
def setup_logging(app):
    """
    Set up logging for the application
    
    Args:
        app: Flask application instance
    """
    # Configure Flask app logger
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # JSON formatter for structured logging
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            # Create a basic log record with only the essential fields
            log_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Add exception info if available
            if record.exc_info:
                log_record["exception"] = str(self.formatException(record.exc_info))
            
            # Add extra fields safely
            if hasattr(record, 'request_id'):
                log_record["request_id"] = record.request_id
            
            if hasattr(record, 'method'):
                log_record["method"] = record.method
                
            if hasattr(record, 'path'):
                log_record["path"] = record.path
                
            if hasattr(record, 'status_code'):
                log_record["status_code"] = record.status_code
                
            if hasattr(record, 'elapsed_time'):
                log_record["elapsed_time"] = record.elapsed_time
            
            # Use safer JSON encoding with simple error handling
            try:
                return json.dumps(log_record, default=str)
            except Exception:
                # Fallback to a basic log format if JSON encoding fails
                return json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "ERROR",
                    "message": "Failed to encode log record",
                    "original_message": str(record.getMessage())
                })
    
    # Create handlers
    # File handler for all logs
    all_logs_handler = RotatingFileHandler(
        os.path.join(log_dir, 'application.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    all_logs_handler.setLevel(log_level)
    all_logs_handler.setFormatter(formatter)
    
    # File handler for errors only
    error_logs_handler = RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    error_logs_handler.setLevel(logging.ERROR)
    error_logs_handler.setFormatter(formatter)
    
    # JSON handler for structured logging
    json_logs_handler = RotatingFileHandler(
        os.path.join(log_dir, 'application.json.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    json_logs_handler.setLevel(log_level)
    json_logs_handler.setFormatter(JsonFormatter())
    
    # Add handlers to Flask logger
    app.logger.handlers = []
    app.logger.addHandler(all_logs_handler)
    app.logger.addHandler(error_logs_handler)
    app.logger.addHandler(json_logs_handler)
    app.logger.setLevel(log_level)
    
    # Also set up root logger for packages
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(all_logs_handler)
    root_logger.addHandler(error_logs_handler)
    root_logger.addHandler(json_logs_handler)
    root_logger.setLevel(log_level)
    
    # Set SQLAlchemy logging level
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Return logger for convenience
    return app.logger
