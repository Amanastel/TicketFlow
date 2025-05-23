from app import create_app
from app.db import db
from app.models.berth import Berth
from app.config import BerthType, Config

app = create_app()

with app.app_context():
    # Drop and recreate all tables
    db.drop_all()
    db.create_all()
    
    # Initialize berths
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
    
    # Commit the changes
    db.session.commit()
    print("Database tables created successfully")
