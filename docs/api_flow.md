# Railway Reservation System API Flow

## Overview

This document describes the flow of operations in the Railway Reservation System API, specifically focusing on the ticket booking, cancellation, and berth allocation processes.

## API Endpoints

The Railway Reservation System exposes the following endpoints:

1. **Health Check**: `GET /api/v1/tickets/health`
   - Checks the health of the API and database connection
   - Returns status code 200 if everything is healthy
   - Used by monitoring systems to ensure the application is running correctly

2. **Book Ticket**: `POST /api/v1/tickets/book`
   - Books tickets for one or more passengers
   - Allocates berths based on availability and passenger priority

3. **Cancel Ticket**: `POST /api/v1/tickets/cancel/{ticket_id}`
   - Cancels a specific ticket
   - Promotes passengers from RAC and waiting list

4. **Get Booked Tickets**: `GET /api/v1/tickets/booked`
   - Retrieves all booked tickets
   - Groups tickets by status (confirmed, RAC, waiting)

5. **Get Available Tickets**: `GET /api/v1/tickets/available`
   - Retrieves information about available tickets
   - Shows available berths by type (lower, middle, upper, side-lower)

## API Flow Diagram

```
+---------------------+          +----------------------+
| Book Ticket Request |--------->| Validate Input Data  |
+---------------------+          +----------------------+
                                            |
                                            v
                                 +----------------------+
                                 | Check Availability   |
                                 +----------------------+
                                            |
                                            v
                              +-------------------------+
                              | Priority-Based          |
                              | Berth Allocation        |
                              +-------------------------+
                                            |
                                            v
                      +-------------------------------------------+
                      |                                           |
                      v                                           v
          +----------------------+                    +----------------------+
          | Allocate Confirmed   |                    | No Confirmed Berths  |
          | Berths               |                    | Available            |
          +----------------------+                    +----------------------+
                      |                                           |
                      v                                           v
          +----------------------+                    +----------------------+
          | Return Ticket with   |                    | Check RAC            |
          | Confirmed Status     |                    | Availability         |
          +----------------------+                    +----------------------+
                                                                  |
                                                                  v
                                                      +----------------------+
                                                      | RAC Available?       |
                                                      +----------------------+
                                                                  |
                                           +--------------------+ | +-------------------+
                                           |                    | | |                   |
                                           v                    | v                     v
                                +--------------------+          |          +--------------------+
                                | Allocate RAC       |<---------+          | Check Waiting List |
                                +--------------------+                     +--------------------+
                                           |                                          |
                                           v                                          v
                                +--------------------+                     +--------------------+
                                | Return Ticket with |                     | Waiting Available? |
                                | RAC Status         |                     +--------------------+
                                +--------------------+                                |
                                                                   +-----------------+ | +-----------------+
                                                                   |                 | | |                 |
                                                                   v                 | v                   v
                                                        +--------------------+       |       +--------------------+
                                                        | Allocate Waiting   |<------+       | Return Error:      |
                                                        | List Position      |               | No Tickets Available|
                                                        +--------------------+               +--------------------+
                                                                   |
                                                                   v
                                                        +--------------------+
                                                        | Return Ticket with |
                                                        | Waiting Status     |
                                                        +--------------------+

+---------------------+          +----------------------+          +------------------------+
| Cancel Ticket       |--------->| Validate Ticket ID   |--------->| Mark Ticket Cancelled  |
| Request             |          |                      |          |                        |
+---------------------+          +----------------------+          +------------------------+
                                                                              |
                                                                              v
                                                                  +------------------------+
                                                                  | Release Allocated      |
                                                                  | Berths                 |
                                                                  +------------------------+
                                                                              |
                                                                              v
                                                                  +------------------------+
                                                                  | Promote RAC to         |
                                                                  | Confirmed              |
                                                                  +------------------------+
                                                                              |
                                                                              v
                                                                  +------------------------+
                                                                  | Promote Waiting to     |
                                                                  | RAC                    |
                                                                  +------------------------+
                                                                              |
                                                                              v
                                                                  +------------------------+
                                                                  | Return Success         |
                                                                  | Response               |
                                                                  +------------------------+
```

## Detailed Process Flows

### Ticket Booking Process

1. **Validate Input Data**
   - Ensure all required passenger fields are present (name, age, gender)
   - Validate parent-child relationships if present
   - Check for maximum passengers per ticket (6)

2. **Check Availability**
   - Count available confirmed berths, RAC positions, and waiting list positions
   - Determine if booking is possible based on number of passengers

3. **Priority-Based Berth Allocation**
   - Identify passengers requiring priority allocation:
     - Seniors (age ≥ 60)
     - Ladies traveling with children
   - Sort passengers by priority

4. **Berth Allocation Decision Process**
   - If confirmed berths available for all passengers:
     - Allocate confirmed berths based on priority
     - Return ticket with confirmed status
   - Else if RAC positions available:
     - Allocate RAC positions
     - Return ticket with RAC status
   - Else if waiting list positions available:
     - Allocate waiting list positions
     - Return ticket with waiting status
   - Else:
     - Return error: no tickets available

5. **Database Transaction**
   - Create ticket record
   - Create passenger records
   - Update berth allocation status
   - Create berth allocation history records
   - Commit transaction (or rollback on error)

### Ticket Cancellation Process

1. **Validate Ticket ID**
   - Check if ticket exists
   - Check if ticket is not already cancelled

2. **Mark Ticket Cancelled**
   - Update ticket status to cancelled
   - Record cancellation time

3. **Release Allocated Berths**
   - Identify all berths allocated to passengers on this ticket
   - Set berth allocation status to false
   - Update berth allocation history

4. **Promote RAC to Confirmed**
   - Identify passengers in RAC with highest priority
   - Allocate released berths to these passengers
   - Update their ticket status to confirmed
   - Create berth allocation history records

5. **Promote Waiting to RAC**
   - Identify passengers in waiting list with highest priority
   - Allocate released RAC positions to these passengers
   - Update their ticket status to RAC
   - Create berth allocation history records

6. **Response**
   - Return success message with cancellation details

## API Endpoint Implementation Details

### 1. Book Ticket (`POST /api/v1/tickets/book`)

**Controller Logic:**
```python
@ticket_bp.route('/book', methods=['POST'])
def book_ticket():
    # Get JSON data
    data = request.get_json()
    
    # Validate input
    passengers_data = data.get('passengers', [])
    if not passengers_data:
        return jsonify({'error': 'No passengers provided'}), 400
    
    # Call service to book ticket
    result = ticket_service.book_ticket(passengers_data)
    
    # Return response
    return jsonify(result), 201
```

**Service Logic (Simplified):**
```python
def book_ticket(passengers_data):
    # Start database transaction
    with db.session.begin():
        # Create ticket
        ticket = Ticket(status=TicketStatus.CONFIRMED)
        db.session.add(ticket)
        db.session.flush()  # Get ticket ID
        
        # Process passengers
        passengers = []
        for passenger_data in passengers_data:
            passenger = Passenger(
                name=passenger_data['name'],
                age=passenger_data['age'],
                gender=passenger_data['gender'],
                ticket_id=ticket.id
            )
            passengers.append(passenger)
            db.session.add(passenger)
        
        # Allocate berths
        allocation_result = allocate_berths(ticket, passengers)
        
        # Update ticket status based on allocation
        ticket.status = allocation_result['status']
        
        # Return result
        return {
            'ticket_id': ticket.id,
            'status': ticket.status,
            'passengers': allocation_result['passengers']
        }
```

### 2. Cancel Ticket (`POST /api/v1/tickets/cancel/{ticket_id}`)

**Controller Logic:**
```python
@ticket_bp.route('/cancel/<int:ticket_id>', methods=['POST'])
def cancel_ticket(ticket_id):
    # Call service to cancel ticket
    result = ticket_service.cancel_ticket(ticket_id)
    
    # Return response
    if 'error' in result:
        return jsonify(result), 404
    return jsonify(result), 200
```

**Service Logic (Simplified):**
```python
def cancel_ticket(ticket_id):
    # Start database transaction
    with db.session.begin():
        # Get ticket with lock
        ticket = Ticket.query.with_for_update().get(ticket_id)
        if not ticket:
            return {'error': 'Ticket not found'}
        
        if ticket.status == TicketStatus.CANCELLED:
            return {'error': 'Ticket already cancelled'}
        
        # Release berths
        released_berths = release_berths(ticket)
        
        # Mark ticket as cancelled
        ticket.status = TicketStatus.CANCELLED
        
        # Promote RAC and waiting list
        promotions = promote_tickets(released_berths)
        
        # Return result
        return {
            'message': f'Ticket {ticket_id} has been cancelled successfully',
            'promotions': promotions
        }
```

## Error Handling

The API includes comprehensive error handling for various scenarios:

- **Input Validation Errors**: Return 400 Bad Request with specific validation error messages
- **Resource Not Found**: Return 404 Not Found when ticket ID doesn't exist
- **Database Errors**: Return 500 Internal Server Error with generic error message
- **Availability Errors**: Return 400 Bad Request when no tickets are available

Each error response follows a consistent format:

```json
{
  "error": "Error message describing the issue",
  "code": "ERROR_CODE"
}
```

## Concurrency Control

The system uses database-level locking to prevent race conditions:

- Row-level locks with `with_for_update()` when updating ticket or berth records
- Transaction isolation level set to `SERIALIZABLE` for critical operations
- Retry logic for handling deadlocks or serialization failures

This ensures that two concurrent operations (e.g., two users trying to book the last available berth) are processed safely and consistently.
                                           |                                          |
                                           v                                          v
                                +--------------------+                     +--------------------+
                                | Return Ticket with |                     | Waiting Available? |
                                | RAC Status         |                     +--------------------+
                                +--------------------+                                |
                                                                   +-----------------+ | +-----------------+
                                                                   |                 | | |                 |
                                                                   v                 | v                   v
                                                       +--------------------+        |        +--------------------+
                                                       | Allocate Waiting   |<-------+        | Return "No Tickets |
                                                       | List Position       |                 | Available" Error   |
                                                       +--------------------+                 +--------------------+
                                                                   |
                                                                   v
                                                       +--------------------+
                                                       | Return Ticket with |
                                                       | Waiting Status     |
                                                       +--------------------+
```

### Cancellation Flow

```
+-------------------------+          +----------------------+
| Cancel Ticket Request   |--------->| Find Ticket          |
+-------------------------+          +----------------------+
                                                |
                                                v
                                     +----------------------+
                                     | Ticket Found?       |
                                     +----------------------+
                                                |
                                    +-----------+-----------+
                                    |                       |
                                    v                       v
                         +--------------------+    +--------------------+
                         | Mark as Cancelled  |    | Return Not Found   |
                         +--------------------+    | Error              |
                                    |             +--------------------+
                                    v
                         +--------------------+
                         | Free Allocated     |
                         | Berths             |
                         +--------------------+
                                    |
                                    v
                         +--------------------+
                         | Promote RAC        |
                         | Passengers         |
                         +--------------------+
                                    |
                                    v
                         +--------------------+
                         | Promote Waiting    |
                         | List to RAC        |
                         +--------------------+
                                    |
                                    v
                         +--------------------+
                         | Return Success     |
                         | Response           |
                         +--------------------+
```
