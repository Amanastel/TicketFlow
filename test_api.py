#!/usr/bin/env python3
"""
API Endpoint Testing Script for Railway Ticket Reservation System
This script tests all the API endpoints and verifies their functionality
"""

import requests
import json
import time
import sys
import subprocess
import os

# Set API base URL
BASE_URL = "http://localhost:5001/api/v1"
SERVER_URL = "http://localhost:5001"

def print_colored(text, color):
    """Print colored text to the console"""
    colors = {
        'green': '\033[0;32m',
        'red': '\033[0;31m',
        'yellow': '\033[0;33m',
        'blue': '\033[0;34m',
        'nc': '\033[0m'  # No Color
    }
    print(f"{colors.get(color, colors['nc'])}{text}{colors['nc']}")

def check_server():
    """Check if the server is running and start it if needed"""
    print_colored("Checking if the server is running...", "yellow")
    try:
        response = requests.get(SERVER_URL, timeout=5)
        if response.status_code == 200:
            print_colored("Server is running.", "green")
            return True
    except requests.RequestException:
        pass
    
    print_colored("Server is not running. Starting the server...", "red")
    try:
        # Try to start the server using docker-compose
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("Waiting for server to start...")
        time.sleep(10)
        
        # Check if server is now running
        try:
            response = requests.get(SERVER_URL, timeout=5)
            if response.status_code == 200:
                print_colored("Server started successfully.", "green")
                return True
        except requests.RequestException:
            pass
        
        print_colored("Failed to start the server. Please start it manually.", "red")
        return False
    except subprocess.SubprocessError as e:
        print_colored(f"Error starting server: {e}", "red")
        return False

def test_endpoint(endpoint, method, data=None, description="", expected_status=200):
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    print_colored(f"\nTesting {description}", "yellow")
    print(f"{method} {url}")
    
    if data:
        print("Request data:")
        print(json.dumps(data, indent=2))
    
    response = None
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            print_colored(f"Unsupported method: {method}", "red")
            return None
    except requests.RequestException as e:
        print_colored(f"Request error: {e}", "red")
        return None
    
    # Check status code
    if response.status_code == expected_status:
        print_colored(f"✓ Status code: {response.status_code} (Expected: {expected_status})", "green")
    else:
        print_colored(f"✗ Status code: {response.status_code} (Expected: {expected_status})", "red")
    
    # Display response
    print("Response:")
    try:
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
        return response_json
    except ValueError:
        print(response.text)
        return response.text

def main():
    """Main function to run all API tests"""
    print_colored("===============================================", "blue")
    print_colored("Railway Ticket Reservation System API Tests", "blue")
    print_colored("===============================================", "blue")
    
    # Check if server is running
    if not check_server():
        sys.exit(1)
    
    # Test 1: Get available tickets
    print_colored("\n===== Test 1: Get Available Tickets =====", "yellow")
    available_response = test_endpoint("/tickets/available", "GET", description="Get available tickets")
    
    # Test 2: Book a ticket for a senior citizen (should get lower berth)
    print_colored("\n===== Test 2: Book Ticket for Senior Citizen =====", "yellow")
    senior_data = {
        "passengers": [
            {
                "name": "Senior Citizen",
                "age": 65,
                "gender": "male"
            }
        ]
    }
    senior_response = test_endpoint("/tickets/book", "POST", senior_data, 
                                    "Book ticket for senior citizen", 201)
    
    # Extract ticket ID for later use
    if senior_response and "ticket_id" in senior_response:
        senior_ticket_id = senior_response["ticket_id"]
        print(f"Extracted ticket ID: {senior_ticket_id}")
    else:
        print_colored("Could not extract ticket ID from response", "red")
        senior_ticket_id = 1  # Fallback
    
    # Test 3: Book a ticket for a family with a child
    print_colored("\n===== Test 3: Book Ticket for Family with Child =====", "yellow")
    family_data = {
        "passengers": [
            {
                "name": "Mother",
                "age": 35,
                "gender": "female",
                "is_parent": True,
                "parent_identifier": "family1"
            },
            {
                "name": "Child",
                "age": 4,
                "gender": "female",
                "parent_identifier": "family1"
            }
        ]
    }
    family_response = test_endpoint("/tickets/book", "POST", family_data, 
                                    "Book ticket for family with child", 201)
    
    # Extract ticket ID for later use
    if family_response and "ticket_id" in family_response:
        family_ticket_id = family_response["ticket_id"]
        print(f"Extracted ticket ID: {family_ticket_id}")
    else:
        print_colored("Could not extract ticket ID from response", "red")
        family_ticket_id = 2  # Fallback
    
    # Test 4: Get all booked tickets
    print_colored("\n===== Test 4: Get All Booked Tickets =====", "yellow")
    booked_response = test_endpoint("/tickets/booked", "GET", description="Get all booked tickets")
    
    # Test 5: Cancel a ticket
    print_colored("\n===== Test 5: Cancel Ticket =====", "yellow")
    cancel_response = test_endpoint(f"/tickets/cancel/{senior_ticket_id}", "POST", 
                                    description="Cancel ticket")
    
    # Test 6: Book multiple tickets to test RAC
    print_colored("\n===== Test 6: Book Multiple Tickets (Testing RAC) =====", "yellow")
    print("Booking multiple tickets to test RAC allocation...")
    
    # Book 5 more tickets (smaller batch for testing)
    for i in range(1, 6):
        print_colored(f"\nBooking ticket batch {i}", "yellow")
        multi_data = {
            "passengers": [
                {
                    "name": f"Regular Passenger {i}",
                    "age": 30,
                    "gender": "male"
                }
            ]
        }
        multi_response = test_endpoint("/tickets/book", "POST", multi_data, 
                                      f"Book ticket batch {i}", 201)
        time.sleep(1)
    
    # Test 7: Get updated available tickets
    print_colored("\n===== Test 7: Get Updated Available Tickets =====", "yellow")
    updated_available_response = test_endpoint("/tickets/available", "GET", 
                                              description="Get updated available tickets")
    
    # Test 8: Final check of all booked tickets
    print_colored("\n===== Test 8: Final Check of All Booked Tickets =====", "yellow")
    final_booked_response = test_endpoint("/tickets/booked", "GET", 
                                         description="Final check of all booked tickets")
    
    print_colored("\n===== All API Tests Completed =====", "green")

if __name__ == "__main__":
    main()
