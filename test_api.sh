#!/bin/bash

# API Endpoint Testing Script for Railway Ticket Reservation System
# This script tests all the API endpoints and verifies their functionality

echo "==============================================="
echo "Railway Ticket Reservation System API Tests"
echo "==============================================="

# Set API base URL
BASE_URL="http://localhost:5000/api/v1"

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if server is running
echo -e "${YELLOW}Checking if the server is running...${NC}"
SERVER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)

if [ "$SERVER_STATUS" != "200" ]; then
    echo -e "${RED}Server is not running. Starting the server...${NC}"
    # Try to start the server
    docker-compose up -d
    
    # Wait for server to start
    echo "Waiting for server to start..."
    sleep 10
    
    SERVER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
    if [ "$SERVER_STATUS" != "200" ]; then
        echo -e "${RED}Failed to start the server. Please start it manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Server is running.${NC}"
fi

# Function to test an API endpoint
test_endpoint() {
    local endpoint=$1
    local method=$2
    local data=$3
    local description=$4
    local expected_status=$5
    
    echo -e "\n${YELLOW}Testing $description${NC}"
    echo "$method $BASE_URL$endpoint"
    
    # Make the request
    if [ "$method" == "GET" ]; then
        response=$(curl -s -X GET $BASE_URL$endpoint)
        status_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET $BASE_URL$endpoint)
    else
        echo "Request data: $data"
        response=$(curl -s -X $method -H "Content-Type: application/json" -d "$data" $BASE_URL$endpoint)
        status_code=$(curl -s -o /dev/null -w "%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" $BASE_URL$endpoint)
    fi
    
    # Check status code
    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}✓ Status code: $status_code (Expected: $expected_status)${NC}"
    else
        echo -e "${RED}✗ Status code: $status_code (Expected: $expected_status)${NC}"
    fi
    
    # Display response
    echo "Response:"
    echo $response | python -m json.tool || echo $response
    
    # Return the response for later use
    echo $response
}

# Function to extract value from JSON response
extract_value() {
    local json=$1
    local key=$2
    echo $json | python -m json.tool | grep "\"$key\":" | head -1 | awk -F': ' '{print $2}' | tr -d '", '
}

# =======================================
# Test 1: Get available tickets
# =======================================
echo -e "\n${YELLOW}===== Test 1: Get Available Tickets =====${NC}"
available_response=$(test_endpoint "/tickets/available" "GET" "" "Get available tickets" "200")

# =======================================
# Test 2: Book a ticket for a senior citizen (should get lower berth)
# =======================================
echo -e "\n${YELLOW}===== Test 2: Book Ticket for Senior Citizen =====${NC}"
senior_data='{
  "passengers": [
    {
      "name": "Senior Citizen",
      "age": 65,
      "gender": "male"
    }
  ]
}'
senior_response=$(test_endpoint "/tickets/book" "POST" "$senior_data" "Book ticket for senior citizen" "201")

# Extract ticket ID for later use
senior_ticket_id=$(extract_value "$senior_response" "ticket_id")
echo -e "\nExtracted ticket ID: $senior_ticket_id"

# =======================================
# Test 3: Book a ticket for a family with a child
# =======================================
echo -e "\n${YELLOW}===== Test 3: Book Ticket for Family with Child =====${NC}"
family_data='{
  "passengers": [
    {
      "name": "Mother",
      "age": 35,
      "gender": "female",
      "is_parent": true,
      "parent_identifier": "family1"
    },
    {
      "name": "Child",
      "age": 4,
      "gender": "female",
      "parent_identifier": "family1"
    }
  ]
}'
family_response=$(test_endpoint "/tickets/book" "POST" "$family_data" "Book ticket for family with child" "201")

# Extract ticket ID for later use
family_ticket_id=$(extract_value "$family_response" "ticket_id")
echo -e "\nExtracted ticket ID: $family_ticket_id"

# =======================================
# Test 4: Get all booked tickets
# =======================================
echo -e "\n${YELLOW}===== Test 4: Get All Booked Tickets =====${NC}"
booked_response=$(test_endpoint "/tickets/booked" "GET" "" "Get all booked tickets" "200")

# =======================================
# Test 5: Cancel a ticket
# =======================================
echo -e "\n${YELLOW}===== Test 5: Cancel Ticket =====${NC}"
cancel_response=$(test_endpoint "/tickets/cancel/$senior_ticket_id" "POST" "" "Cancel ticket" "200")

# =======================================
# Test 6: Book multiple tickets to test RAC
# =======================================
echo -e "\n${YELLOW}===== Test 6: Book Multiple Tickets (Testing RAC) =====${NC}"
# Book 63 tickets to fill all confirmed berths
echo "Booking multiple tickets to test RAC allocation..."

# Book 5 more tickets (smaller batch for testing)
for i in {1..5}; do
    echo -e "\n${YELLOW}Booking ticket batch $i${NC}"
    multi_data='{
      "passengers": [
        {
          "name": "Regular Passenger '"$i"'",
          "age": 30,
          "gender": "male"
        }
      ]
    }'
    multi_response=$(test_endpoint "/tickets/book" "POST" "$multi_data" "Book ticket batch $i" "201")
    sleep 1
done

# =======================================
# Test 7: Get updated available tickets
# =======================================
echo -e "\n${YELLOW}===== Test 7: Get Updated Available Tickets =====${NC}"
updated_available_response=$(test_endpoint "/tickets/available" "GET" "" "Get updated available tickets" "200")

# =======================================
# Test 8: Final check of all booked tickets
# =======================================
echo -e "\n${YELLOW}===== Test 8: Final Check of All Booked Tickets =====${NC}"
final_booked_response=$(test_endpoint "/tickets/booked" "GET" "" "Final check of all booked tickets" "200")

echo -e "\n${GREEN}===== All API Tests Completed =====${NC}"
