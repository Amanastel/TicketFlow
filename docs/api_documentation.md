# Railway Reservation System API Documentation

## Overview

The Railway Reservation System API provides endpoints for booking railway tickets, cancelling tickets, and checking availability. The system handles berth allocation according to passenger priority, supports RAC (Reservation Against Cancellation) and waiting list, and automatically promotes tickets when cancellations occur.

## System Configuration

The system is configured with the following capacity:
- **Confirmed Berths (63 total)**:
  - 21 Lower Berths
  - 21 Middle Berths
  - 21 Upper Berths
- **RAC Berths**:
  - 9 Side-Lower Berths (accommodates 18 passengers, 2 per berth)
- **Waiting List**: 10 positions maximum

## Base URL

```
http://localhost:5005/api/v1/tickets
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are configured as follows:

| Endpoint                  | Rate Limit           | Description                                |
|---------------------------|----------------------|--------------------------------------------|
| `/health`                 | No limit             | Health check endpoint for monitoring       |
| `/book`                   | 100 per hour         | Book tickets endpoint                      |
| `/cancel/{ticket_id}`     | 100 per hour         | Cancel ticket endpoint                     |
| `/booked`                 | 200 per hour         | Get booked tickets endpoint                |
| `/available`              | 200 per hour         | Get available tickets endpoint             |
| Default                   | 1000 per day, 500 per hour | Default limit for all other endpoints |

Rate limit responses include the following headers:
- `X-RateLimit-Limit`: The maximum number of requests allowed in the current period
- `X-RateLimit-Remaining`: The number of requests remaining in the current period
- `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets

When a rate limit is exceeded, the API returns a `429 Too Many Requests` response.

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages:

- 200: Success
- 201: Resource created (e.g., ticket booked)
- 400: Bad Request (invalid input)
- 404: Resource not found
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error

Error responses include:
- Error message
- Error field (if applicable)
- Request ID (for debugging)

Common error codes include:

| HTTP Status | Error Code              | Description                                      |
|-------------|-------------------------|--------------------------------------------------|
| 400         | VALIDATION_ERROR        | Input validation failed                          |
| 400         | INVALID_PASSENGERS      | Invalid passenger data                           |
| 400         | INVALID_TICKET_STATUS   | Invalid ticket status                            |
| 400         | NO_AVAILABILITY         | No tickets available                             |
| 404         | RESOURCE_NOT_FOUND      | Requested resource not found                     |
| 409         | CONCURRENCY_ERROR       | Operation failed due to concurrent access        |
| 429         | RATE_LIMIT_EXCEEDED     | Rate limit exceeded                              |
| 500         | DATABASE_ERROR          | Database operation failed                        |
| 500         | INTERNAL_SERVER_ERROR   | Unexpected server error                          |

## Authentication

The API currently does not require authentication.

## Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Checks the health of the API and database connection.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Error message"
}
```

### 2. Book Ticket

**Endpoint:** `POST /book`

**Description:** Books tickets for one or more passengers and allocates berths based on availability and passenger priority.

**Request Body:**
```json
{
  "passengers": [
    {
      "name": "Passenger Name",
      "age": 35,
      "gender": "male",
      "is_parent": true,
      "parent_identifier": "family1"
    },
    {
      "name": "Child Name",
      "age": 4,
      "gender": "female",
      "parent_identifier": "family1"
    }
  ]
}
```

**Parameters:**
- `name` (string, required): Passenger's name
- `age` (number, required): Passenger's age
- `gender` (string, required): Passenger's gender ("male" or "female")
- `is_parent` (boolean, optional): Whether this passenger is a parent
- `parent_identifier` (string, optional): Identifier to link children with parents

**Response (201 Created):**
```json
{
  "ticket_id": 123,
  "status": "confirmed",
  "passengers": [
    {
      "id": 456,
      "name": "Passenger Name",
      "age": 35,
      "gender": "male",
      "berth": "lower"
    },
    {
      "id": 457,
      "name": "Child Name",
      "age": 4,
      "gender": "female",
      "berth": null
    }
  ]
}
```

**Error Responses:**
- 400 Bad Request: Invalid input or no tickets available
- 500 Internal Server Error: Database or server error

### 3. Cancel Ticket

**Endpoint:** `DELETE /cancel/{ticket_id}`

**Description:** Cancels a specific ticket and promotes passengers from RAC and waiting list.

**Parameters:**
- `ticket_id` (path parameter, required): ID of the ticket to cancel

**Response (200 OK):**
```json
{
  "message": "Ticket 123 has been cancelled successfully"
}
```

**Error Responses:**
- 400 Bad Request: Ticket already cancelled
- 404 Not Found: Ticket not found
- 500 Internal Server Error: Database or server error

### 4. Get Booked Tickets

**Endpoint:** `GET /booked`

**Description:** Retrieves all booked tickets grouped by status (confirmed, RAC, waiting).

**Response (200 OK):**
```json
{
  "confirmed": [
    {
      "ticket_id": 123,
      "booking_time": "2023-04-15T10:30:00",
      "passengers": [
        {
          "id": 456,
          "name": "Passenger Name",
          "age": 35,
          "gender": "male",
          "berth": "lower"
        }
      ]
    }
  ],
  "rac": [
    {
      "ticket_id": 124,
      "booking_time": "2023-04-15T11:45:00",
      "passengers": [
        {
          "id": 458,
          "name": "RAC Passenger",
          "age": 40,
          "gender": "female",
          "berth": "side_lower",
          "rac_position": 1
        }
      ]
    }
  ],
  "waiting": [
    {
      "ticket_id": 125,
      "booking_time": "2023-04-15T12:15:00",
      "passengers": [
        {
          "id": 459,
          "name": "Waiting Passenger",
          "age": 25,
          "gender": "male",
          "berth": null,
          "waiting_position": 1
        }
      ]
    }
  ],
  "summary": {
    "confirmed_count": 1,
    "rac_count": 1,
    "waiting_count": 1,
    "total_count": 3
  }
}
```

**Error Responses:**
- 500 Internal Server Error: Database or server error

### 5. Get Available Tickets

**Endpoint:** `GET /available`

**Description:** Retrieves information about available tickets and berths.

**Response (200 OK):**
```json
{
  "confirmed_available": 10,
  "rac_available": 5,
  "waiting_list_available": 10,
  "available_berths": {
    "lower": 3,
    "middle": 3,
    "upper": 3,
    "side_lower": 1
  }
}
```

**Error Responses:**
- 500 Internal Server Error: Database or server error

## Priority Allocation Logic

The system allocates berths with the following priority order:

1. **Seniors (age ≥ 60)**: Preferentially allocated lower berths
2. **Parents with small children (age < 5)**: Preferentially allocated lower berths
3. **Other passengers**: Allocated available berths (lower, middle, or upper)

## Booking Process

1. When a booking request is received:
   - System checks total available berths
   - Passengers are sorted by priority (seniors first, then parents with children)
   - System attempts to allocate appropriate berths based on priority

2. If confirmed berths are not available:
   - Passengers are moved to RAC (side-lower berths, 2 passengers per berth)
   - If RAC is full, passengers are placed in waiting list

3. Special handling:
   - Children under 5 years don't require separate berths
   - Parents traveling with children are kept together when possible
   - Seniors are given priority for lower berths

## Ticket Status Flow

Tickets can have one of the following statuses:

1. **Confirmed**: Passengers have been allocated regular berths (lower, middle, or upper)
2. **RAC (Reservation Against Cancellation)**: Passengers share side-lower berths
3. **Waiting**: No berths allocated, passengers are on the waiting list
4. **Cancelled**: Ticket has been cancelled

When a confirmed or RAC ticket is cancelled:
1. System automatically promotes RAC passengers to confirmed status (if berths are available)
2. Waiting list passengers are promoted to RAC status (if RAC positions are available)
3. Berth allocation history is maintained for audit purposes

## Concurrency Control

The system implements database-level locking to handle concurrent requests:
- Row-level locks with `with_for_update()` for ticket and berth updates
- Nested transactions with `begin_nested()`
- Proper error handling and rollback in case of failures

This ensures that concurrent operations (e.g., two users trying to book the last available berth) are processed safely and consistently.

## Deployment

The API can be deployed using Docker:

```bash
docker-compose up -d
```

For production deployment:

```bash
docker-compose -f docker-compose.prod.yml up -d
```
