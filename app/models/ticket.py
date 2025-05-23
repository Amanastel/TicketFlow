from datetime import datetime
from app.db import db
from app.config import TicketStatus

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default=TicketStatus.CONFIRMED)
    booking_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    passengers = db.relationship('Passenger', backref='ticket', lazy=True, cascade="all, delete-orphan")
    berth_allocation_history = db.relationship('BerthAllocationHistory', backref='ticket', lazy=True, cascade="all, delete-orphan")
    
    # Add RAC and Waiting List position tracking
    rac_position = db.Column(db.Integer, nullable=True)
    waiting_position = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f"<Ticket {self.id} - {self.status}>"
