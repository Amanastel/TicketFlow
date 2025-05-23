"""
Middleware for the Railway Ticket Reservation System
"""
import time
import uuid
from flask import request, g, current_app

class RequestLoggingMiddleware:
    """Middleware for logging all requests"""
    
    def __init__(self, app, wsgi_app):
        self.app = app
        self.wsgi_app = wsgi_app
        
    def __call__(self, environ, start_response):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Record start time
        start_time = time.time()
        
        # Extract simple request data
        path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', '')
        remote_addr = environ.get('REMOTE_ADDR', '')
        query_string = environ.get('QUERY_STRING', '')
        
        # Log the request with only the essential information
        with self.app.app_context():
            self.app.logger.info(
                f"Request started: {method} {path}",
                extra={
                    'request_id': request_id,
                    'method': method,
                    'path': path,
                    'remote_addr': remote_addr,
                    'query_string': query_string
                }
            )
        
        # Process the request
        def custom_start_response(status, headers, exc_info=None):
            # Log the response with only the essential information
            status_code = status.split(' ')[0]
            elapsed_time = time.time() - start_time
            
            with self.app.app_context():
                self.app.logger.info(
                    f"Request completed: {method} {path} - Status: {status_code} - Time: {elapsed_time:.3f}s",
                    extra={
                        'request_id': request_id,
                        'method': method,
                        'path': path,
                        'status_code': status_code,
                        'elapsed_time': elapsed_time
                    }
                )
            
            # Call the original start_response
            return start_response(status, headers, exc_info)
            
        try:
            # Call the original WSGI app to avoid recursion
            return self.wsgi_app(environ, custom_start_response)
        except Exception as e:
            with self.app.app_context():
                self.app.logger.error(
                    f"Request failed: {method} {path}",
                    extra={
                        'request_id': request_id,
                        'method': method,
                        'path': path,
                        'error': str(e)
                    },
                    exc_info=True
                )
            raise

def setup_middleware(app):
    """Set up middleware for the application"""
    # Correct: wrap the original wsgi_app, not the Flask app itself
    app.wsgi_app = RequestLoggingMiddleware(app, app.wsgi_app)
    return app
