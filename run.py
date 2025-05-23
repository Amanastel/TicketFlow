from app import create_app
from app.db import db
from app.models.berth import Berth
from app.config import BerthType, Config
import os

app = create_app()

# Setup function to initialize berths when needed
def setup_berths():
    """Initialize berths in the database if they don't exist"""
    with app.app_context():
        # Check if berths are already created
        berth_count = Berth.query.count()
        if berth_count == 0:
            print("Initializing berths...")
            
            # Create confirmed berths (63 total)
            # Distribution: 21 lower, 21 middle, 21 upper
            for i in range(1, 22):  # 21 of each type
                # Lower berth
                db.session.add(Berth(berth_type=BerthType.LOWER))
                
                # Middle berth
                db.session.add(Berth(berth_type=BerthType.MIDDLE))
                
                # Upper berth
                db.session.add(Berth(berth_type=BerthType.UPPER))
            
            # Create 9 side-lower berths for RAC (18 passengers, 2 per berth)
            for i in range(1, 10):
                db.session.add(Berth(berth_type=BerthType.SIDE_LOWER))
            
            db.session.commit()
            print(f"Created {Berth.query.count()} berths")
        else:
            print(f"Berths already exist: {berth_count} berths found")

if __name__ == '__main__':
    setup_berths()
    
    # Determine if we're in production mode
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5005))  # Using port 5005
    
    if is_production:
        # In production, the application should be run with Gunicorn
        # This code won't actually run Gunicorn, but it's here to document the command
        print("In production mode, please run with Gunicorn:")
        print(f"gunicorn --bind 0.0.0.0:{port} --workers 4 'run:app'")
    else:
        # In development, use Flask's built-in server
        app.run(host='0.0.0.0', port=port, debug=True)
