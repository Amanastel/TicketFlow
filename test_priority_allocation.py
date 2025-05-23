#!/usr/bin/env python3
"""
Advanced Testing Script for Priority Allocation in Railway Ticket Reservation System
This script specifically tests the priority allocation logic for seniors and families
"""

import requests
import json
import time
import sys
from pprint import pprint

# Set API base URL
BASE_URL = "http://localhost:5005/api/v1/tickets"

def print_colored(text, color):
    """Print colored text to the console"""
    colors = {
        'green': '\033[0;32m',
        'red': '\033[0;31m',
        'yellow': '\033[0;33m',
        'blue': '\033[0;34m',
        'purple': '\033[0;35m',
        'cyan': '\033[0;36m',
        'nc': '\033[0m'  # No Color
    }
    print(f"{colors.get(color, colors['nc'])}{text}{colors['nc']}")

def get_available_tickets():
    """Get available tickets information"""
    response = requests.get(f"{BASE_URL}/available")
    print_colored(f"Available Tickets: {response.status_code}", "blue")
    return response.json()

def get_booked_tickets():
    """Get all booked tickets"""
    response = requests.get(f"{BASE_URL}/booked")
    print_colored(f"Booked Tickets: {response.status_code}", "blue")
    return response.json()

def book_tickets(passengers_data, expected_status=201):
    """Book tickets for multiple passengers"""
    response = requests.post(
        f"{BASE_URL}/book",
        json={"passengers": passengers_data}
    )
    print_colored(f"Book Ticket: {response.status_code}", "green" if response.status_code == expected_status else "red")
    
    try:
        response_data = response.json()
        pprint(response_data)
        return response_data, response.status_code
    except:
        print("Failed to parse response as JSON")
        return None, response.status_code

def cancel_ticket(ticket_id):
    """Cancel a specific ticket"""
    response = requests.delete(f"{BASE_URL}/cancel/{ticket_id}")
    print_colored(f"Cancel Ticket {ticket_id}: {response.status_code}", "yellow")
    
    try:
        response_data = response.json()
        pprint(response_data)
        return response_data, response.status_code
    except:
        print("Failed to parse response as JSON")
        return None, response.status_code

def test_senior_priority():
    """Test priority allocation for senior citizens"""
    print_colored("\n===== Test Case: Senior Priority Allocation =====", "cyan")
    
    # Check available berths
    available = get_available_tickets()
    if available["available_berths"]["lower"] < 2:
        print_colored("Not enough lower berths available for testing. Please reset the database.", "red")
        return False
    
    # Book a ticket with both senior and non-senior passengers
    passengers = [
        {
            "name": "Senior Citizen 1",
            "age": 65,
            "gender": "Male"
        },
        {
            "name": "Adult 1",
            "age": 35,
            "gender": "Male"
        },
        {
            "name": "Senior Citizen 2",
            "age": 70,
            "gender": "Female"
        },
        {
            "name": "Adult 2",
            "age": 30,
            "gender": "Female"
        }
    ]
    
    print_colored("\nBooking ticket with senior citizens and regular adults...", "yellow")
    booking_response, status_code = book_tickets(passengers)
    
    if status_code != 201 or not booking_response:
        print_colored("Failed to book ticket", "red")
        return False
    
    ticket_id = booking_response.get("ticket_id")
    ticket_passengers = booking_response.get("passengers", [])
    
    # Verify that seniors got lower berths
    senior_1 = next((p for p in ticket_passengers if p["name"] == "Senior Citizen 1"), None)
    senior_2 = next((p for p in ticket_passengers if p["name"] == "Senior Citizen 2"), None)
    adult_1 = next((p for p in ticket_passengers if p["name"] == "Adult 1"), None)
    adult_2 = next((p for p in ticket_passengers if p["name"] == "Adult 2"), None)
    
    print_colored("\nChecking berth allocation...", "yellow")
    seniors_with_lower = 0
    
    if senior_1 and senior_1["berth"] == "lower":
        print_colored("✓ Senior Citizen 1 received lower berth as expected", "green")
        seniors_with_lower += 1
    elif senior_1:
        print_colored(f"✗ Senior Citizen 1 received {senior_1['berth']} berth instead of lower", "red")
    
    if senior_2 and senior_2["berth"] == "lower":
        print_colored("✓ Senior Citizen 2 received lower berth as expected", "green")
        seniors_with_lower += 1
    elif senior_2:
        print_colored(f"✗ Senior Citizen 2 received {senior_2['berth']} berth instead of lower", "red")
    
    if adult_1:
        print_colored(f"Adult 1 received {adult_1['berth']} berth", "blue")
    
    if adult_2:
        print_colored(f"Adult 2 received {adult_2['berth']} berth", "blue")
    
    # Clean up
    print_colored("\nCleaning up...", "yellow")
    cancel_ticket(ticket_id)
    
    # Return test result
    if seniors_with_lower == 2:
        print_colored("✓ Test passed: All seniors received lower berths", "green")
        return True
    else:
        print_colored(f"✗ Test failed: Only {seniors_with_lower}/2 seniors received lower berths", "red")
        return False

def test_family_priority():
    """Test priority allocation for families with small children"""
    print_colored("\n===== Test Case: Family Priority Allocation =====", "cyan")
    
    # Check available berths
    available = get_available_tickets()
    if available["available_berths"]["lower"] < 2:
        print_colored("Not enough lower berths available for testing. Please reset the database.", "red")
        return False
    
    # Book a ticket with parents with small children and regular adults
    passengers = [
        {
            "name": "Parent 1",
            "age": 35,
            "gender": "Female",
            "is_parent": True,
            "parent_identifier": "family1"
        },
        {
            "name": "Child 1",
            "age": 4,  # Child below 5 years
            "gender": "Male",
            "is_parent": False,
            "parent_identifier": "family1"
        },
        {
            "name": "Parent 2",
            "age": 32,
            "gender": "Female",
            "is_parent": True,
            "parent_identifier": "family2"
        },
        {
            "name": "Child 2",
            "age": 3,  # Child below 5 years
            "gender": "Female",
            "is_parent": False,
            "parent_identifier": "family2"
        },
        {
            "name": "Regular Adult 1",
            "age": 40,
            "gender": "Male"
        },
        {
            "name": "Regular Adult 2",
            "age": 38,
            "gender": "Female"
        }
    ]
    
    print_colored("\nBooking ticket with parents with small children and regular adults...", "yellow")
    booking_response, status_code = book_tickets(passengers)
    
    if status_code != 201 or not booking_response:
        print_colored("Failed to book ticket", "red")
        return False
    
    ticket_id = booking_response.get("ticket_id")
    ticket_passengers = booking_response.get("passengers", [])
    
    # Verify that parents with small children got lower berths
    parent_1 = next((p for p in ticket_passengers if p["name"] == "Parent 1"), None)
    parent_2 = next((p for p in ticket_passengers if p["name"] == "Parent 2"), None)
    regular_1 = next((p for p in ticket_passengers if p["name"] == "Regular Adult 1"), None)
    regular_2 = next((p for p in ticket_passengers if p["name"] == "Regular Adult 2"), None)
    
    print_colored("\nChecking berth allocation...", "yellow")
    parents_with_lower = 0
    
    if parent_1 and parent_1["berth"] == "lower":
        print_colored("✓ Parent 1 received lower berth as expected", "green")
        parents_with_lower += 1
    elif parent_1:
        print_colored(f"✗ Parent 1 received {parent_1['berth']} berth instead of lower", "red")
    
    if parent_2 and parent_2["berth"] == "lower":
        print_colored("✓ Parent 2 received lower berth as expected", "green")
        parents_with_lower += 1
    elif parent_2:
        print_colored(f"✗ Parent 2 received {parent_2['berth']} berth instead of lower", "red")
    
    if regular_1:
        print_colored(f"Regular Adult 1 received {regular_1['berth']} berth", "blue")
    
    if regular_2:
        print_colored(f"Regular Adult 2 received {regular_2['berth']} berth", "blue")
    
    # Clean up
    print_colored("\nCleaning up...", "yellow")
    cancel_ticket(ticket_id)
    
    # Return test result
    if parents_with_lower == 2:
        print_colored("✓ Test passed: All parents with small children received lower berths", "green")
        return True
    else:
        print_colored(f"✗ Test failed: Only {parents_with_lower}/2 parents received lower berths", "red")
        return False

def test_mixed_priority():
    """Test priority allocation when there's a mix of seniors and families with children"""
    print_colored("\n===== Test Case: Mixed Priority Allocation =====", "cyan")
    
    # Check available berths
    available = get_available_tickets()
    if available["available_berths"]["lower"] < 2:
        print_colored("Not enough lower berths available for testing. Please reset the database.", "red")
        return False
    
    # Book a ticket with seniors, parents with small children, and regular adults
    passengers = [
        {
            "name": "Senior Citizen",
            "age": 68,
            "gender": "Male"
        },
        {
            "name": "Parent",
            "age": 34,
            "gender": "Female",
            "is_parent": True,
            "parent_identifier": "family1"
        },
        {
            "name": "Child",
            "age": 3,  # Child below 5 years
            "gender": "Female",
            "is_parent": False,
            "parent_identifier": "family1"
        },
        {
            "name": "Regular Adult",
            "age": 42,
            "gender": "Male"
        }
    ]
    
    print_colored("\nBooking ticket with senior, parent with small child, and regular adult...", "yellow")
    booking_response, status_code = book_tickets(passengers)
    
    if status_code != 201 or not booking_response:
        print_colored("Failed to book ticket", "red")
        return False
    
    ticket_id = booking_response.get("ticket_id")
    ticket_passengers = booking_response.get("passengers", [])
    
    # Verify priority allocation
    senior = next((p for p in ticket_passengers if p["name"] == "Senior Citizen"), None)
    parent = next((p for p in ticket_passengers if p["name"] == "Parent"), None)
    regular = next((p for p in ticket_passengers if p["name"] == "Regular Adult"), None)
    
    print_colored("\nChecking berth allocation...", "yellow")
    priority_with_lower = 0
    
    if senior and senior["berth"] == "lower":
        print_colored("✓ Senior Citizen received lower berth as expected", "green")
        priority_with_lower += 1
    elif senior:
        print_colored(f"✗ Senior Citizen received {senior['berth']} berth instead of lower", "red")
    
    if parent and parent["berth"] == "lower":
        print_colored("✓ Parent received lower berth as expected", "green")
        priority_with_lower += 1
    elif parent:
        print_colored(f"✗ Parent received {parent['berth']} berth instead of lower", "red")
    
    if regular:
        print_colored(f"Regular Adult received {regular['berth']} berth", "blue")
    
    # Clean up
    print_colored("\nCleaning up...", "yellow")
    cancel_ticket(ticket_id)
    
    # Return test result
    if priority_with_lower == 2:
        print_colored("✓ Test passed: Both senior and parent received lower berths", "green")
        return True
    else:
        print_colored(f"✗ Test failed: Only {priority_with_lower}/2 priority passengers received lower berths", "red")
        return False

def main():
    """Run all test cases"""
    print_colored("===============================================", "blue")
    print_colored("Railway Reservation System Priority Allocation Tests", "blue")
    print_colored("===============================================", "blue")
    
    # First, check server status
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_colored("Server is running.", "green")
        else:
            print_colored(f"Server returned status code {response.status_code}", "red")
            sys.exit(1)
    except requests.RequestException as e:
        print_colored(f"Server is not running: {e}", "red")
        sys.exit(1)
    
    # Run test cases
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Senior priority
    if test_senior_priority():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: Family priority
    if test_family_priority():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 3: Mixed priority
    if test_mixed_priority():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Print summary
    print_colored("\n===============================================", "blue")
    print_colored("Test Summary", "blue")
    print_colored("===============================================", "blue")
    print_colored(f"Tests Passed: {tests_passed}", "green")
    print_colored(f"Tests Failed: {tests_failed}", "red")
    print_colored(f"Total Tests: {tests_passed + tests_failed}", "blue")
    
    if tests_failed == 0:
        print_colored("\n✓ All priority allocation tests passed!", "green")
        sys.exit(0)
    else:
        print_colored("\n✗ Some priority allocation tests failed.", "red")
        sys.exit(1)

if __name__ == "__main__":
    main()
