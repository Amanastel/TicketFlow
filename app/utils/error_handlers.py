"""
Error handling utilities for the application
"""
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

class TicketSystemError(Exception):
    """Base exception class for ticket system errors"""
    def __init__(self, message, code=None, status_code=400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFoundError(TicketSystemError):
    """Exception raised when a requested resource is not found"""
    def __init__(self, resource_type, resource_id):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, code="RESOURCE_NOT_FOUND", status_code=404)

class NoAvailabilityError(TicketSystemError):
    """Exception raised when there are no tickets available"""
    def __init__(self, message="No tickets available"):
        super().__init__(message, code="NO_AVAILABILITY", status_code=400)

class ValidationError(TicketSystemError):
    """Exception raised when input validation fails"""
    def __init__(self, message, field=None):
        code = f"INVALID_{field.upper()}" if field else "VALIDATION_ERROR"
        super().__init__(message, code=code, status_code=400)

class ConcurrencyError(TicketSystemError):
    """Exception raised when a concurrency issue occurs"""
    def __init__(self, message="Operation could not be completed due to concurrent access"):
        super().__init__(message, code="CONCURRENCY_ERROR", status_code=409)

class DatabaseError(TicketSystemError):
    """Exception raised when a database error occurs"""
    def __init__(self, original_exception=None):
        message = "A database error occurred"
        if original_exception:
            message = f"{message}: {str(original_exception)}"
        super().__init__(message, code="DATABASE_ERROR", status_code=500)

def register_error_handlers(app):
    """Register error handlers with the Flask application"""
    
    @app.errorhandler(TicketSystemError)
    def handle_ticket_system_error(error):
        """Handle custom ticket system errors"""
        response = {
            'error': error.message
        }
        if error.code:
            response['code'] = error.code
            
        return jsonify(response), error.status_code
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions"""
        response = {
            'error': error.description,
            'code': error.name
        }
        return jsonify(response), error.code
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """Handle SQLAlchemy errors"""
        # Log the full error for debugging
        current_app.logger.error(f"Database error: {str(error)}")
        
        # Provide appropriate user-facing message based on error type
        if isinstance(error, IntegrityError):
            message = "Data integrity error occurred"
            code = "INTEGRITY_ERROR"
        elif isinstance(error, OperationalError):
            message = "Database operation error occurred"
            code = "OPERATIONAL_ERROR"
        else:
            message = "A database error occurred"
            code = "DATABASE_ERROR"
            
        return jsonify({
            'error': message,
            'code': code
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle all other exceptions"""
        # Log the full error
        current_app.logger.exception("Unhandled exception occurred")
        
        # In production, don't expose error details
        if app.config.get('DEBUG', False):
            message = str(error)
        else:
            message = "An unexpected error occurred"
            
        return jsonify({
            'error': message,
            'code': 'INTERNAL_SERVER_ERROR'
        }), 500
