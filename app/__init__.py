import os
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from app.config import config
from app.db import init_db
from app.rate_limiter import init_limiter
from app.logging_config import setup_logging
from app.middleware import setup_middleware
from app.routes.ticket_routes import ticket_bp
from app.utils.error_handlers import register_error_handlers

def create_app(config_name=None):
    """Create and configure the Flask application"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database
    db = init_db(app)
    
    # Initialize rate limiter
    limiter = init_limiter(app)
    
    # Set up logging
    logger = setup_logging(app)
    
    # Set up middleware
    app = setup_middleware(app)
    
    # Register blueprints
    app.register_blueprint(ticket_bp)
    
    # Add Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Railway Reservation API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create a route for the index
    @app.route('/')
    def index():
        return {
            "message": "Welcome to Railway Reservation API",
            "docs": f"{SWAGGER_URL}"
        }
    
    return app
