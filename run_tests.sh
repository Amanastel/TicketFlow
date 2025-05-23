#!/bin/bash

# Test script for Railway Ticket Reservation System
# This script runs all tests and performs basic API health checks

echo "==============================================="
echo "Railway Ticket Reservation System Test Script"
echo "==============================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Docker is available
echo "Checking Docker installation..."
if command_exists docker && command_exists docker-compose; then
    echo "✅ Docker and Docker Compose are installed"
else
    echo "❌ Docker and/or Docker Compose are not installed"
    echo "Please install Docker and Docker Compose before running this script"
    exit 1
fi

# Check Python environment
echo -e "\nChecking Python installation..."
if command_exists python3; then
    python_version=$(python3 --version)
    echo "✅ $python_version is installed"
else
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3 before running this script"
    exit 1
fi

# Check required Python packages
echo -e "\nChecking Python dependencies..."
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
else
    echo "❌ requirements.txt not found"
    echo "Please ensure you're in the correct directory"
    exit 1
fi

# Run unit tests
echo -e "\nRunning unit tests..."
python -m unittest tests.py
if [ $? -eq 0 ]; then
    echo "✅ Unit tests passed"
else
    echo "❌ Some unit tests failed"
    exit 1
fi

# Start the application in a Docker container for API testing
echo -e "\nStarting application in Docker container..."
docker-compose up -d
if [ $? -eq 0 ]; then
    echo "✅ Application started successfully"
else
    echo "❌ Failed to start application in Docker"
    exit 1
fi

# Wait for the application to start
echo "Waiting for application to start..."
sleep 5

# Test API endpoints
echo -e "\nTesting API endpoints..."

# Base URL for API requests
BASE_URL="http://localhost:5000/api/v1"

# Function to make a request and check the response
test_endpoint() {
    local endpoint=$1
    local method=$2
    local expected_status=$3
    local data=$4
    
    echo -n "Testing $method $endpoint: "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method $BASE_URL$endpoint)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" $BASE_URL$endpoint)
    fi
    
    if [ "$response" == "$expected_status" ]; then
        echo "✅ Success ($response)"
        return 0
    else
        echo "❌ Failed (Expected: $expected_status, Got: $response)"
        return 1
    fi
}

# Test health check endpoint
test_endpoint "/tickets/health" "GET" "200"

# Test available tickets endpoint
test_endpoint "/tickets/available" "GET" "200"

# Test booking a ticket
BOOKING_DATA='{"passengers":[{"name":"Test Passenger","age":35,"gender":"male"}]}'
test_endpoint "/tickets/book" "POST" "201" "$BOOKING_DATA"

# Test getting booked tickets
test_endpoint "/tickets/booked" "GET" "200"

# Clean up
echo -e "\nStopping application..."
docker-compose down
echo "✅ Application stopped"

# Run production features test
echo -e "\nTesting production features..."
if command_exists python3; then
    python3 test_production.py 5000
    if [ $? -eq 0 ]; then
        echo "✅ Production features test passed"
    else
        echo "❌ Some production features tests failed"
        exit 1
    fi
else
    echo "❌ Python 3 is required to run production features test"
    exit 1
fi

echo -e "\n==============================================="
echo "All tests completed successfully!"
echo "==============================================="
exit 0
