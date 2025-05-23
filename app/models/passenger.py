from app.db import db

class Passenger(db.Model):
    __tablename__ = 'passengers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    child = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    parent_id = db.Column(db.Integer, db.ForeignKey('passengers.id'), nullable=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    
    # Self-referential relationship for parent-child
    children = db.relationship('Passenger', 
                             backref=db.backref('parent', remote_side=[id]),
                             cascade="all, delete-orphan")
    
    # Relationship with berths
    berth = db.relationship('Berth', backref='passenger', uselist=False)
    
    def __repr__(self):
        return f"<Passenger {self.id} - {self.name}>"
        
    @property
    def needs_berth(self):
        """Check if passenger needs a berth (age >= 5)"""
        return self.age >= 5
        
    @property
    def is_senior(self):
        """Check if passenger is a senior citizen (age >= 60)"""
        return self.age >= 60
        
    @property
    def is_lady_with_child(self):
        """Check if passenger is a lady with children"""
        return self.gender.lower() == 'female' and any(child.age < 5 for child in self.children)
