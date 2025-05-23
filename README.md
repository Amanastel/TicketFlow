# Railway Ticket Reservation System

A comprehensive API for managing railway ticket reservations, including booking, cancellation, and status tracking.

## System Features

- Book tickets with priority allocation for seniors and ladies with children
- Cancel tickets with automatic promotion from RAC and waiting list
- Track ticket status (confirmed, RAC, waiting)
- View available tickets and berths

## Constraints and Rules

- 63 confirmed berths (21 lower, 21 middle, 21 upper)
- 18 RAC positions (9 side-lower berths, 2 passengers per berth)
- 10 waiting list positions maximum
- Priority allocation of lower berths to:
  - Passengers aged 60+
  - Ladies with children
- Children under 5 years don't get berths but are recorded in the system

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tickets/health` | GET | Health check endpoint |
| `/api/v1/tickets/book` | POST | Book a ticket for one or more passengers |
| `/api/v1/tickets/cancel/{ticket_id}` | POST | Cancel a ticket |
| `/api/v1/tickets/booked` | GET | Get all booked tickets |
| `/api/v1/tickets/available` | GET | Get available ticket information |

## Tech Stack

- **Backend**: Python with Flask
- **Database**: SQLite (can be replaced with PostgreSQL)
- **API Documentation**: Swagger/OpenAPI
- **Containerization**: Docker

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker

1. Clone the repository:
   ```
   git clone https://github.com/Amanastel/TicketFlow
   cd ticketFlow
   ```

2. Run the application:
   
   **Development Mode**:
   ```
   ./run.sh --dev
   ```
   
   **Production Mode**:
   ```
   ./run.sh --prod
   ```
   
   **Rebuilding Containers**:
   ```
   ./run.sh --rebuild
   ```
   
   **Stopping Containers**:
   ```
   ./run.sh --stop
   ```

3. Access the API at `http://localhost:5000`
4. Access the Swagger documentation at `http://localhost:5000/api/docs`

### Running Locally

1. Clone the repository:
   ```
   git clone https://github.com/Amanastel/TicketFlow
   cd ticketFlow
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python run.py
   ```

5. Access the API at `http://localhost:5000`
6. Access the Swagger documentation at `http://localhost:5000/api/docs`

### Production Deployment

The system includes a production-ready configuration with:

1. **PostgreSQL Database**: Persistent storage with transaction support
2. **Nginx Load Balancer**: For handling high traffic and SSL termination
3. **Gunicorn WSGI Server**: Multi-worker setup for better performance
4. **Rate Limiting**: Protection against API abuse
5. **Health Checks**: For monitoring system status

To deploy in production mode:

```
./run.sh --prod
```

For a production deployment, you should modify the following:

1. Set secure passwords in environment variables:
   ```
   export DB_PASSWORD="your-secure-password"
   export SECRET_KEY="your-secure-secret-key"
   ```

2. Configure SSL certificates in Nginx for HTTPS
3. Set up proper logging and monitoring
4. Configure backups for the PostgreSQL database

## Testing

The project includes comprehensive unit and integration tests:

1. Run unit tests:
   ```
   python -m unittest tests.py
   ```

2. Run the automated test script (includes Docker container testing):
   ```
   ./run_tests.sh
   ```

## Database Schema


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

The system uses a relational database with the following tables:

- **passengers**: Stores passenger details
- **tickets**: Stores ticket information and status
- **berths**: Stores berth information and allocation status
- **berth_allocation_history**: Tracks the history of berth allocations

## API Usage Examples

### Book a Ticket

**Request:**
```http
POST /api/v1/tickets/book
Content-Type: application/json

{
  "passengers": [
    {
      "name": "Aman Singh",
      "age": 65,
      "gender": "male"
    },
    {
      "name": "Priti Singh",
      "age": 35,
      "gender": "female",
      "is_parent": true,
      "parent_identifier": "family1"
    },
    {
      "name": "Karan Singh",
      "age": 3,
      "gender": "female",
      "parent_identifier": "family1"
    }
  ]
}
```

**Response:**
```json
{
  "ticket_id": 1,
  "status": "confirmed",
  "passengers": [
    {
      "id": 1,
      "name": "Aman Singh",
      "age": 65,
      "gender": "male",
      "berth": "lower"
    },
    {
      "id": 2,
      "name": "Priti Singh",
      "age": 35,
      "gender": "female",
      "berth": "middle"
    },
    {
      "id": 3,
      "name": "Karan Singh",
      "age": 3,
      "gender": "female",
      "berth": null
    }
  ]
}
```

### Cancel a Ticket

**Request:**
```http
POST /api/v1/tickets/cancel/1
```

**Response:**
```json
{
  "message": "Ticket 1 has been cancelled successfully"
}
```

### Get Booked Tickets

**Request:**
```http
GET /api/v1/tickets/booked
```

**Response:**
```json
{
  "confirmed": [
    {
      "ticket_id": 2,
      "booking_time": "2023-05-01T10:30:00.000Z",
      "passengers": [
        {
          "id": 4,
          "name": "Sumit",
          "age": 45,
          "gender": "female",
          "berth": "lower"
        }
      ]
    }
  ],
  "rac": [
    {
      "ticket_id": 3,
      "booking_time": "2023-05-01T11:15:00.000Z",
      "passengers": [
        {
          "id": 5,
          "name": "Raju",
          "age": 50,
          "gender": "male",
          "berth": "side-lower",
          "rac_position": 1
        }
      ]
    }
  ],
  "waiting": [],
  "summary": {
    "confirmed_count": 1,
    "rac_count": 1,
    "waiting_count": 0,
    "total_count": 2
  }
}
```

### Get Available Tickets

**Request:**
```http
GET /api/v1/tickets/available
```

**Response:**
```json
{
  "confirmed_available": 62,
  "rac_available": 17,
  "waiting_list_available": 10,
  "available_berths": {
    "lower": 20,
    "middle": 21,
    "upper": 21,
    "side_lower": 8
  }
}
```

## Concurrency Handling

The system uses SQLAlchemy's row-level locking with `with_for_update()` to prevent race conditions when booking or cancelling tickets. This ensures that two users cannot book the same berth simultaneously.

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid input or no tickets available
- `404 Not Found`: Ticket not found
- `500 Internal Server Error`: Server-side errors

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Aman Kumar
