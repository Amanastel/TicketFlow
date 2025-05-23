from app.db import db
from app.config import BerthType

class Berth(db.Model):
    __tablename__ = 'berths'
    
    id = db.Column(db.Integer, primary_key=True)
    berth_type = db.Column(db.String(20), nullable=False)
    is_allocated = db.Column(db.Boolean, default=False)
    
    # Foreign key
    passenger_id = db.Column(db.Integer, db.ForeignKey('passengers.id'), nullable=True)
    
    # History relationship
    allocation_history = db.relationship('BerthAllocationHistory', backref='berth', lazy=True)
    
    def __repr__(self):
        return f"<Berth {self.id} - {self.berth_type} - {'Allocated' if self.is_allocated else 'Free'}>"
