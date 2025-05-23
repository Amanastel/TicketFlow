from datetime import datetime
from app.db import db

class BerthAllocationHistory(db.Model):
    __tablename__ = 'berth_allocation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    berth_id = db.Column(db.Integer, db.ForeignKey('berths.id'), nullable=True)  # Can be null for waiting list
    rac_position = db.Column(db.Integer, nullable=True)
    waiting_position = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BerthAllocationHistory {self.id} - Ticket: {self.ticket_id}, Berth: {self.berth_id}>"
