from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models here to ensure they're registered with SQLAlchemy
    from app.models.passenger import Passenger
    from app.models.ticket import Ticket
    from app.models.berth import Berth
    from app.models.berth_allocation_history import BerthAllocationHistory
    
    return db
