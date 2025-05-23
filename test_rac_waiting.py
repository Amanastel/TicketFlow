#!/usr/bin/env python3
"""
Advanced API Testing Script for Railway Ticket Reservation System
This script tests RAC and Waiting List functionality by booking many tickets
"""

import requests
import json
import time
import sys
import os

# Set API base URL
BASE_URL = "http://localhost:5005/api/v1"
SERVER_URL = "http://localhost:5005"

def print_colored(text, color):
    """Print colored text to the console"""
    colors = {
        'green': '\033[0;32m',
        'red': '\033[0;31m',
        'yellow': '\033[0;33m',
        'blue': '\033[0;34m',
        'purple': '\033[0;35m',
        'nc': '\033[0m'  # No Color
    }
    print(f"{colors.get(color, colors['nc'])}{text}{colors['nc']}")

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
    """Main function to run the advanced tests"""
    print_colored("===============================================", "blue")
    print_colored("Railway Reservation System - RAC & Waiting List Tests", "blue")
    print_colored("===============================================", "blue")
    
    # First, check server status
    try:
        response = requests.get(SERVER_URL, timeout=5)
        if response.status_code == 200:
            print_colored("Server is running.", "green")
        else:
            print_colored(f"Server returned status code {response.status_code}", "red")
            sys.exit(1)
    except requests.RequestException as e:
        print_colored(f"Server is not running: {e}", "red")
        sys.exit(1)
    
    # Get initial availability
    print_colored("\n===== Initial Ticket Availability =====", "purple")
    initial_available = test_endpoint("/tickets/available", "GET", description="Get initial availability")
    
    if not initial_available:
        print_colored("Failed to get initial availability. Exiting.", "red")
        sys.exit(1)
    
    # Calculate how many tickets we need to book to reach RAC
    confirmed_available = initial_available.get("confirmed_available", 0)
    print_colored(f"\nThere are {confirmed_available} confirmed berths available.", "purple")
    print_colored(f"Will book tickets to fill confirmed berths and test RAC/waiting list.", "purple")
    
    # 1. Book tickets until confirmed berths are filled
    ticket_ids = []
    print_colored("\n===== Phase 1: Filling Confirmed Berths =====", "purple")
    
    # Book single passenger tickets to fill confirmed berths
    for i in range(1, confirmed_available + 1):
        passenger_data = {
            "passengers": [
                {
                    "name": f"Passenger {i:03d}",
                    "age": 30,
                    "gender": "male" if i % 2 == 0 else "female"
                }
            ]
        }
        
        print_colored(f"\nBooking ticket {i}/{confirmed_available}", "yellow")
        response = test_endpoint("/tickets/book", "POST", passenger_data, 
                                f"Book single passenger ticket {i}", 201)
        
        if response and "ticket_id" in response:
            ticket_ids.append(response["ticket_id"])
        
        # Sleep briefly to avoid overwhelming the server
        time.sleep(0.2)
        
        # Check every 10 bookings
        if i % 10 == 0 or i == confirmed_available:
            avail = test_endpoint("/tickets/available", "GET", 
                                 description=f"Check availability after {i} bookings")
            if avail.get("confirmed_available", 0) == 0:
                print_colored("All confirmed berths are now filled!", "green")
                break
    
    # 2. Book RAC tickets
    print_colored("\n===== Phase 2: Testing RAC Allocation =====", "purple")
    rac_available = initial_available.get("rac_available", 0)
    
    for i in range(1, rac_available + 1):
        passenger_data = {
            "passengers": [
                {
                    "name": f"RAC Passenger {i:02d}",
                    "age": 30,
                    "gender": "male" if i % 2 == 0 else "female"
                }
            ]
        }
        
        print_colored(f"\nBooking RAC ticket {i}/{rac_available}", "yellow")
        response = test_endpoint("/tickets/book", "POST", passenger_data, 
                                f"Book RAC ticket {i}", 201)
        
        if response and "ticket_id" in response:
            ticket_ids.append(response["ticket_id"])
            
            # Check if we got an RAC ticket
            if response.get("status") == "rac":
                print_colored("Successfully received an RAC ticket!", "green")
            else:
                print_colored(f"Expected RAC ticket but got {response.get('status')}", "red")
        
        time.sleep(0.2)
        
        # Check every 5 RAC bookings
        if i % 5 == 0 or i == rac_available:
            avail = test_endpoint("/tickets/available", "GET", 
                                 description=f"Check availability after {i} RAC bookings")
            if avail.get("rac_available", 0) == 0:
                print_colored("All RAC positions are now filled!", "green")
                break
    
    # 3. Book Waiting List tickets
    print_colored("\n===== Phase 3: Testing Waiting List =====", "purple")
    waiting_available = initial_available.get("waiting_list_available", 0)
    
    for i in range(1, waiting_available + 1):
        passenger_data = {
            "passengers": [
                {
                    "name": f"Waiting List Passenger {i:02d}",
                    "age": 30,
                    "gender": "male" if i % 2 == 0 else "female"
                }
            ]
        }
        
        print_colored(f"\nBooking Waiting List ticket {i}/{waiting_available}", "yellow")
        response = test_endpoint("/tickets/book", "POST", passenger_data, 
                                f"Book Waiting List ticket {i}", 201)
        
        if response and "ticket_id" in response:
            ticket_ids.append(response["ticket_id"])
            
            # Check if we got a waiting list ticket
            if response.get("status") == "waiting":
                print_colored("Successfully received a Waiting List ticket!", "green")
            else:
                print_colored(f"Expected Waiting List ticket but got {response.get('status')}", "red")
        
        time.sleep(0.2)
        
        # Check every 3 Waiting List bookings
        if i % 3 == 0 or i == waiting_available:
            avail = test_endpoint("/tickets/available", "GET", 
                                 description=f"Check availability after {i} Waiting List bookings")
            if avail.get("waiting_list_available", 0) == 0:
                print_colored("All Waiting List positions are now filled!", "green")
                break
    
    # 4. Try to book when all positions are filled
    print_colored("\n===== Phase 4: Testing Booking When Full =====", "purple")
    overflow_data = {
        "passengers": [
            {
                "name": "Overflow Passenger",
                "age": 30,
                "gender": "male"
            }
        ]
    }
    
    response = test_endpoint("/tickets/book", "POST", overflow_data, 
                            "Book ticket when no positions available", 400)
    
    # 5. Get final ticket summary
    print_colored("\n===== Final Ticket Summary =====", "purple")
    final_booked = test_endpoint("/tickets/booked", "GET", description="Get all booked tickets")
    
    # Print statistics
    if final_booked:
        confirmed_count = len(final_booked.get("confirmed", []))
        rac_count = len(final_booked.get("rac", []))
        waiting_count = len(final_booked.get("waiting", []))
        
        print_colored("\nBooking Statistics:", "blue")
        print_colored(f"- Confirmed tickets: {confirmed_count}", "green")
        print_colored(f"- RAC tickets: {rac_count}", "yellow")
        print_colored(f"- Waiting List tickets: {waiting_count}", "red")
        print_colored(f"- Total tickets booked: {confirmed_count + rac_count + waiting_count}", "purple")
    
    # 6. Test cancellation and automatic promotion
    print_colored("\n===== Phase 5: Testing Cancellation and Promotion =====", "purple")
    
    # If we have both waiting and RAC tickets, test promotion
    if final_booked and final_booked.get("confirmed") and (final_booked.get("rac") or final_booked.get("waiting")):
        # Cancel the first confirmed ticket
        confirm_ticket_id = final_booked["confirmed"][0]["ticket_id"]
        print_colored(f"Cancelling confirmed ticket {confirm_ticket_id}", "yellow")
        
        cancel_response = test_endpoint(f"/tickets/cancel/{confirm_ticket_id}", "DELETE", 
                                        description="Cancel confirmed ticket to test promotion")
        
        # Check ticket status after cancellation
        after_cancel = test_endpoint("/tickets/booked", "GET", 
                                    description="Get ticket status after cancellation")
        
        if after_cancel:
            print_colored("\nPromotion Result:", "blue")
            print_colored("Checking if an RAC ticket was promoted to Confirmed status...", "yellow")
            
            # Here we would need to analyze the 'after_cancel' response to determine if promotion occurred
            # This requires knowledge of the tickets before and after cancellation
            
    print_colored("\n===== Advanced API Tests Completed =====", "green")

if __name__ == "__main__":
    main()
