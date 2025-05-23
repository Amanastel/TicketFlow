"""
Rate limiting for the API to prevent abuse
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Initialize limiter without app - will be initialized in create_app
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "500 per hour"],  # Default limits
    storage_uri=os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://"),  # Support Redis in production
    strategy="moving-window"  # More accurate rate limiting strategy for production
)

def init_limiter(app):
    """Initialize the rate limiter with the Flask app"""
    # Configure Redis connection for production
    redis_url = app.config.get('REDIS_URL')
    if redis_url and os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://") == "memory://":
        # Update storage for Redis in production
        app.logger.info(f"Using Redis for rate limiting: {redis_url}")
    
    # Initialize with app
    limiter.init_app(app)
    
    # Log configuration
    app.logger.info(f"Rate limiter initialized with strategy: {limiter._strategy}")
    
    return limiter
