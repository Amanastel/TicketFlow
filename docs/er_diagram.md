# Railway Reservation System ER Diagram

## Entity Relationship Diagram

```
+----------------+       +----------------+       +----------------+
|   passengers   |       |     tickets    |       |     berths     |
+----------------+       +----------------+       +----------------+
| id (PK)        |       | id (PK)        |       | id (PK)        |
| name           |       | status         |       | berth_type     |
| age            |       | booking_time   |       | is_allocated   |
| gender         |<----->| rac_position   |       | passenger_id   |
| child          |       | waiting_position|      +----------------+
| parent_id (FK) |       +----------------+              ^
| ticket_id (FK) |               ^                       |
+----------------+               |                       |
                                 |                       |
                                 |                       |
                            +-----------------------------+
                            | berth_allocation_history    |
                            +-----------------------------+
                            | id (PK)                     |
                            | ticket_id (FK)              |
                            | berth_id (FK)               |
                            | rac_position                |
                            | waiting_position            |
                            | created_at                  |
                            +-----------------------------+
```

## Detailed Entity Description

### Passenger Entity

The `Passenger` entity represents a traveler in the railway reservation system.

**Attributes:**
- `id`: Primary key, unique identifier for the passenger
- `name`: Full name of the passenger
- `age`: Age of the passenger in years
- `gender`: Gender of the passenger ('male', 'female', 'other')
- `child`: Boolean flag indicating if passenger is a child (under 5 years)
- `parent_id`: Foreign key referencing another passenger who is the parent
- `ticket_id`: Foreign key referencing the ticket this passenger belongs to

**Business Rules:**
- Passengers over 60 years of age are considered senior citizens and get priority for lower berths
- Children under 5 years of age don't get allocated berths
- Females traveling with children get priority for lower berths

### Ticket Entity

The `Ticket` entity represents a booking in the system that may contain multiple passengers.

**Attributes:**
- `id`: Primary key, unique identifier for the ticket
- `status`: Current status of the ticket ('confirmed', 'rac', 'waiting', 'cancelled')
- `booking_time`: Timestamp when the ticket was booked
- `rac_position`: Position in the RAC queue (null if not in RAC)
- `waiting_position`: Position in the waiting list (null if not in waiting list)

**Business Rules:**
- A ticket can have a maximum of 6 passengers
- Ticket status is determined by the highest priority passenger in the group
- When a ticket is cancelled, all berths allocated to its passengers are released

### Berth Entity

The `Berth` entity represents a specific berth in a train that can be allocated to a passenger.

**Attributes:**
- `id`: Primary key, unique identifier for the berth
- `berth_type`: Type of berth ('lower', 'middle', 'upper', 'side-lower')
- `is_allocated`: Boolean flag indicating if berth is currently allocated
- `passenger_id`: Foreign key referencing the passenger to whom the berth is allocated

**Business Rules:**
- The system has 63 confirmed berths (21 lower, 21 middle, 21 upper)
- There are 9 side-lower berths for RAC (accommodating 18 passengers, 2 per berth)
- Lower berths are prioritized for senior citizens and ladies with children

### Berth Allocation History Entity

The `BerthAllocationHistory` entity tracks the history of berth allocations, which is useful for auditing and troubleshooting.

**Attributes:**
- `id`: Primary key, unique identifier for the allocation history record
- `ticket_id`: Foreign key referencing the ticket involved
- `berth_id`: Foreign key referencing the berth involved
- `rac_position`: RAC position (if applicable)
- `waiting_position`: Waiting list position (if applicable)
- `created_at`: Timestamp when the allocation was made

**Business Rules:**
- A new record is created whenever a berth is allocated or deallocated
- Records are never deleted, providing a complete audit trail

## Entity Relationships

1. **Passenger to Ticket**: Many-to-One
   - Many passengers can belong to one ticket
   - Each passenger has a ticket_id foreign key

2. **Passenger to Passenger (Self-Reference)**: One-to-Many
   - A passenger can be a parent to multiple child passengers
   - Child passengers have a parent_id foreign key

3. **Passenger to Berth**: One-to-One
   - A passenger can be assigned to at most one berth
   - A berth can be assigned to at most one passenger

4. **Ticket to BerthAllocationHistory**: One-to-Many
   - A ticket can have multiple allocation history records
   - Each history record has a ticket_id foreign key

5. **Berth to BerthAllocationHistory**: One-to-Many
   - A berth can appear in multiple allocation history records
   - Each history record has a berth_id foreign key

## Key Constraints

- Each passenger must be associated with exactly one ticket
- A berth can be allocated to at most one passenger at a time
- A passenger can have at most one berth allocated to them
- Child passengers (under 5) must be linked to a parent passenger

## Database Implementation

The system uses SQLAlchemy ORM to map these entities to database tables:

```python
class Passenger(db.Model):
    __tablename__ = 'passengers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    # Other fields...

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
    # Other fields...

class Berth(db.Model):
    __tablename__ = 'berths'
    id = db.Column(db.Integer, primary_key=True)
    berth_type = db.Column(db.String(20), nullable=False)
    is_allocated = db.Column(db.Boolean, default=False)
    # Other fields...

class BerthAllocationHistory(db.Model):
    __tablename__ = 'berth_allocation_history'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    berth_id = db.Column(db.Integer, db.ForeignKey('berths.id'))
    # Other fields...
```

- Maximum 63 confirmed berths (21 lower, 21 middle, 21 upper)
- Maximum 18 RAC positions (9 side-lower berths)
- Maximum 10 waiting list positions
