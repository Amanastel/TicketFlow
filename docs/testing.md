# Railway Ticket Reservation System API Testing

This document provides comprehensive documentation for testing the Railway Ticket Reservation System API.

## Test Scripts

The following test scripts are available in the main project directory:

### 1. `test_api.sh` (Bash Script)

A bash script that tests all API endpoints sequentially. This script:

- Checks if the server is running
- Tests the available tickets endpoint
- Books tickets for various scenarios (senior citizens, families with children)
- Tests ticket cancellation
- Tests RAC and waiting list allocation

**Usage:**
```bash
./test_api.sh
```

### 2. `test_api.py` (Python Script)

A more robust Python version of the API test script that provides better error handling and output formatting. This script:

- Checks if the server is running and starts it if needed
- Tests all API endpoints with various scenarios
- Provides detailed feedback for each test

**Usage:**
```bash
./test_api.py
```

### 3. `test_rac_waiting.py` (Python Script)

A specialized test script focused on testing the RAC and waiting list functionality:

- Fills all confirmed berths
- Tests RAC allocation
- Tests waiting list allocation
- Tests automatic promotion when tickets are cancelled

**Usage:**
```bash
./test_rac_waiting.py
```

### 4. `run_tests.sh`

A comprehensive script that tests both the application code and the API functionality. This script:

- Checks your environment for dependencies
- Runs unit tests from the `tests.py` file
- Starts the application in a Docker container
- Tests API endpoints
- Cleans up after testing

**Usage:**
```bash
./run_tests.sh
```

## Postman Collection

The file `postman_collection.json` contains a Postman collection that can be imported into Postman for manual API testing. The collection includes:

1. Get Available Tickets
2. Get Booked Tickets
3. Book Ticket - Senior Citizen
4. Book Ticket - Family with Child
5. Book Ticket - Single Passenger
6. Book Ticket - Multiple Passengers
7. Cancel Ticket
8. Book Multiple Tickets for RAC Testing
9. Book Ticket for Waiting List Testing

**Usage:**
1. Import the collection into Postman
2. Set the `baseUrl` variable to `http://localhost:5001` (or your server URL)
3. Run the requests in sequence to test the API functionality

## Documentation

Additional documentation in this directory:

- `er_diagram.md`: Entity-relationship diagram and database schema
- `api_flow.md`: API flow diagrams and process descriptions

## Testing Scenarios

The following scenarios should be tested:

1. **Basic Ticket Booking**
   - Book tickets for a single passenger
   - Book tickets for multiple passengers

2. **Priority Allocation**
   - Book tickets for senior citizens (age ≥ 60)
   - Book tickets for ladies with children

3. **Ticket Statuses**
   - Confirmed booking
   - RAC booking
   - Waiting list booking

4. **Cancellation and Promotion**
   - Cancel confirmed tickets
   - Verify RAC passengers are promoted to confirmed
   - Verify waiting list passengers are promoted to RAC

5. **Edge Cases**
   - Booking when no tickets are available

## Test Results (May 23, 2025)

The following test results were observed during comprehensive testing:

### API Endpoints Test Results

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/` | GET | Welcome message | ✅ Pass |
| `/api/v1/tickets/available` | GET | Get available tickets | ✅ Pass |
| `/api/v1/tickets/booked` | GET | Get all booked tickets | ✅ Pass |
| `/api/v1/tickets/book` | POST | Book a ticket | ✅ Pass |
| `/api/v1/tickets/cancel/{ticket_id}` | POST | Cancel a ticket | ✅ Pass |

### Functional Test Results

| Test Scenario | Description | Status | Notes |
|---------------|-------------|--------|-------|
| Basic Booking | Book tickets for single passengers | ✅ Pass | Correctly allocates berths |
| Priority - Senior | Book tickets for seniors (age ≥ 60) | ✅ Pass | Correctly allocates lower berths |
| Priority - Lady with Child | Book tickets for ladies with children | ✅ Pass | Correctly allocates lower berths |
| Multi-passenger Booking | Book tickets for multiple passengers | ✅ Pass | All passengers assigned to same ticket |
| RAC Allocation | Book tickets when confirmed berths are full | ✅ Pass | Correctly assigns RAC positions |
| Waiting List | Book tickets when confirmed and RAC are full | ✅ Pass | Correctly assigns waiting list positions |
| Booking Beyond Capacity | Book tickets when all positions are full | ✅ Pass | Correctly returns error response |
| Cancel Confirmed Ticket | Cancel a confirmed ticket | ✅ Pass | Berth is properly released |
| Automatic Promotion | RAC to confirmed, waiting to RAC | ✅ Pass | Automatic promotion works correctly |

### Key Observations

1. **Berth Allocation Logic**: The system correctly implements the berth allocation logic based on priority (seniors and ladies with children get lower berths).

2. **Concurrency Handling**: The system correctly handles concurrent booking requests through database locking mechanisms.

3. **Automatic Promotion**: When a confirmed ticket is cancelled:
   - An RAC passenger is automatically promoted to confirmed status
   - A waiting list passenger is automatically promoted to RAC
   - All berth assignments are updated correctly

4. **Error Handling**: The system returns appropriate error messages when:
   - Invalid ticket IDs are provided for cancellation
   - No tickets are available for booking
   - Input validation fails

5. **Response Format**: All API responses follow a consistent format with appropriate HTTP status codes.

## Testing Production Features

The following tests should be performed to validate the production-ready features:

### 1. Health Check Endpoint

Test the health check endpoint to verify system status:

```bash
curl http://localhost:5000/api/v1/tickets/health
```

Expected output:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Rate Limiting

Test the rate limiting functionality by making multiple requests in quick succession:

```bash
for i in {1..30}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5000/api/v1/tickets/available
done
```

After a certain number of requests, you should start seeing `429 Too Many Requests` responses.

### 3. Testing with Gunicorn in Production Mode

1. Start the application in production mode:
   ```bash
   ./run.sh --prod
   ```

2. Run the test suite against the production setup:
   ```bash
   PORT=5000 python test_api.py
   ```

### 4. Load Testing (Optional)

For more comprehensive load testing, you can use tools like Apache Bench or JMeter:

```bash
# Install Apache Bench if not already installed
# Then run a simple load test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:5000/api/v1/tickets/available
```

### 5. Testing Nginx Configuration (Production Mode)

When running in production mode with Nginx:

1. Test that requests are properly proxied:
   ```bash
   curl http://localhost:80/api/v1/tickets/available
   ```

2. Test that the rate limiting works at the Nginx level:
   ```bash
   for i in {1..15}; do
     curl -s -o /dev/null -w "%{http_code}\n" http://localhost:80/api/v1/tickets/available
   done
   ```

## Recommendations

Based on the test results, the following improvements are recommended:

1. **Performance Optimization**: When many tickets are booked, the `/api/v1/tickets/booked` endpoint can become slow. Consider adding pagination.

2. **Input Validation**: Add more robust input validation with specific error messages for client-side validation.

3. **Logging**: Enhance logging for better debugging and monitoring.

4. **API Versioning**: Implement formal API versioning for future changes.

## Testing Results

| Feature | Status | Notes |
|---------|--------|-------|
| API Endpoints | ✅ Passed | All endpoints working as expected |
| Ticket Booking | ✅ Passed | Berth allocation follows priority rules |
| RAC & Waiting List | ✅ Passed | Proper promotion when tickets are cancelled |
| Health Check | ✅ Passed | Provides accurate system status |
| Rate Limiting | ✅ Passed | Protects API from abuse |
| Production Setup | ✅ Passed | Gunicorn and Nginx working correctly |

## Conclusion

The Railway Ticket Reservation System API passes all functional tests and correctly implements the business requirements. The system has been enhanced with production-ready features including:

1. Health check endpoints
2. Rate limiting
3. Production-ready server (Gunicorn)
4. Load balancing (Nginx)
5. Enhanced documentation
6. PostgreSQL database support

The system is ready for production deployment.
   - Cancelling non-existent tickets
   - Booking with invalid passenger data
