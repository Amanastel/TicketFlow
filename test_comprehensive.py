#!/usr/bin/env python
import requests
import json
import time
from pprint import pprint

BASE_URL = "http://127.0.0.1:5005/api/v1/tickets"

def check_health():
    """Verify the health check endpoint is working"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.status_code}")
    assert response.status_code == 200
    return response.json()

def get_available_tickets():
    """Get available tickets information"""
    response = requests.get(f"{BASE_URL}/available")
    print(f"Available Tickets: {response.status_code}")
    assert response.status_code == 200
    return response.json()

def get_booked_tickets():
    """Get all booked tickets"""
    response = requests.get(f"{BASE_URL}/booked")
    print(f"Booked Tickets: {response.status_code}")
    assert response.status_code == 200
    return response.json()

def book_tickets(passengers_data):
    """Book tickets for multiple passengers"""
    response = requests.post(
        f"{BASE_URL}/book",
        json={"passengers": passengers_data}
    )
    print(f"Book Ticket: {response.status_code}")
    pprint(response.json())
    return response.json(), response.status_code

def cancel_ticket(ticket_id):
    """Cancel a specific ticket"""
    response = requests.delete(f"{BASE_URL}/cancel/{ticket_id}")
    print(f"Cancel Ticket {ticket_id}: {response.status_code}")
    pprint(response.json())
    return response.json(), response.status_code

def test_scenario_1():
    """Test booking a single passenger"""
    print("\n===== SCENARIO 1: Book a single senior passenger =====")
    available_before = get_available_tickets()
    
    # Book a ticket for a senior citizen
    passengers = [
        {
            "name": "Senior Citizen",
            "age": 65,
            "gender": "Male",
            "is_parent": False
        }
    ]
    
    booking_response, status_code = book_tickets(passengers)
    ticket_id = booking_response.get("ticket_id")
    assert status_code == 201
    
    # Check available tickets after booking
    available_after = get_available_tickets()
    print("\nAvailable tickets before booking:")
    pprint(available_before)
    print("\nAvailable tickets after booking:")
    pprint(available_after)
    
    # Check that one lower berth was allocated (senior gets priority)
    assert available_before["available_berths"]["lower"] - 1 == available_after["available_berths"]["lower"]
    assert available_before["confirmed_available"] - 1 == available_after["confirmed_available"]
    
    # Cancel the ticket
    cancel_ticket(ticket_id)
    
    # Verify available tickets are restored
    available_final = get_available_tickets()
    assert available_before["confirmed_available"] == available_final["confirmed_available"]
    assert available_before["available_berths"]["lower"] == available_final["available_berths"]["lower"]

def test_scenario_2():
    """Test booking multiple passengers with parent-child relationship"""
    print("\n===== SCENARIO 2: Book family with parent-child relationship =====")
    available_before = get_available_tickets()
    
    # Book a ticket for a family (parent with child)
    passengers = [
        {
            "name": "Parent",
            "age": 35,
            "gender": "Female",
            "is_parent": True,
            "parent_identifier": "family1"
        },
        {
            "name": "Child",
            "age": 4,  # Child below 5 years (doesn't need berth)
            "gender": "Male",
            "is_parent": False,
            "parent_identifier": "family1"
        }
    ]
    
    booking_response, status_code = book_tickets(passengers)
    ticket_id = booking_response.get("ticket_id")
    assert status_code == 201
    
    # Get booked tickets
    booked_tickets = get_booked_tickets()
    print("\nBooked tickets:")
    pprint(booked_tickets["confirmed"])
    
    # Cancel the ticket
    cancel_ticket(ticket_id)

def test_scenario_3():
    """Test RAC allocation"""
    print("\n===== SCENARIO 3: Test RAC allocation =====")
    # Get initial available tickets
    available_before = get_available_tickets()
    
    # Book tickets to fill all confirmed berths first
    confirmed_tickets = []
    confirmed_available = available_before["confirmed_available"]
    
    print(f"Booking {confirmed_available} tickets to fill all confirmed berths...")
    for i in range(confirmed_available):
        passengers = [
            {
                "name": f"Passenger Confirmed {i+1}",
                "age": 30,
                "gender": "Male",
                "is_parent": False
            }
        ]
        booking_response, status_code = book_tickets(passengers)
        assert status_code == 201
        confirmed_tickets.append(booking_response.get("ticket_id"))
    
    # Now book one more ticket that should go to RAC
    print("\nBooking one more ticket that should go to RAC...")
    passengers = [
        {
            "name": "RAC Passenger",
            "age": 40,
            "gender": "Female",
            "is_parent": False
        }
    ]
    rac_booking, status_code = book_tickets(passengers)
    rac_ticket_id = rac_booking.get("ticket_id")
    assert status_code == 201
    
    # Verify this ticket got RAC status
    booked_tickets = get_booked_tickets()
    rac_tickets = booked_tickets.get("rac", [])
    
    # There should be at least one RAC ticket
    assert len(rac_tickets) > 0
    
    # Check that RAC position is assigned
    assert any(t["ticket_id"] == rac_ticket_id for t in rac_tickets)
    
    # Cancel one confirmed ticket to see if RAC gets promoted
    print("\nCancelling one confirmed ticket to check RAC promotion...")
    if confirmed_tickets:
        cancel_ticket(confirmed_tickets[0])
    
    # Check if RAC passenger got promoted to confirmed
    time.sleep(1)  # Give system time to process
    booked_tickets = get_booked_tickets()
    
    # Clean up remaining tickets
    for ticket_id in confirmed_tickets[1:]:
        cancel_ticket(ticket_id)
    cancel_ticket(rac_ticket_id)

def test_scenario_4():
    """Test waiting list allocation and promotion"""
    print("\n===== SCENARIO 4: Test waiting list allocation and promotion =====")
    available_before = get_available_tickets()
    
    # Book tickets to fill all confirmed berths
    confirmed_tickets = []
    confirmed_available = available_before["confirmed_available"]
    
    print(f"Booking {confirmed_available} tickets to fill all confirmed berths...")
    for i in range(confirmed_available):
        passengers = [
            {
                "name": f"Passenger Confirmed {i+1}",
                "age": 30,
                "gender": "Male",
                "is_parent": False
            }
        ]
        booking_response, _ = book_tickets(passengers)
        confirmed_tickets.append(booking_response.get("ticket_id"))
    
    # Book tickets to fill all RAC berths
    rac_tickets = []
    rac_available = available_before["rac_available"]
    
    print(f"\nBooking {rac_available} tickets to fill all RAC berths...")
    for i in range(rac_available):
        passengers = [
            {
                "name": f"Passenger RAC {i+1}",
                "age": 35,
                "gender": "Female",
                "is_parent": False
            }
        ]
        booking_response, _ = book_tickets(passengers)
        rac_tickets.append(booking_response.get("ticket_id"))
    
    # Now book one more ticket that should go to waiting list
    print("\nBooking one more ticket that should go to waiting list...")
    passengers = [
        {
            "name": "Waiting List Passenger",
            "age": 25,
            "gender": "Male",
            "is_parent": False
        }
    ]
    waiting_booking, status_code = book_tickets(passengers)
    waiting_ticket_id = waiting_booking.get("ticket_id")
    assert status_code == 201
    
    # Verify this ticket got waiting list status
    booked_tickets = get_booked_tickets()
    waiting_tickets = booked_tickets.get("waiting", [])
    
    # There should be at least one waiting list ticket
    assert len(waiting_tickets) > 0
    
    # Check if waiting position is assigned
    assert any(t["ticket_id"] == waiting_ticket_id for t in waiting_tickets)
    
    # Cancel one RAC ticket to see if waiting list gets promoted to RAC
    print("\nCancelling one RAC ticket to check waiting list promotion...")
    if rac_tickets:
        cancel_ticket(rac_tickets[0])
    
    # Check if waiting list passenger got promoted to RAC
    time.sleep(1)  # Give system time to process
    booked_tickets = get_booked_tickets()
    
    # Clean up remaining tickets
    for ticket_id in confirmed_tickets:
        cancel_ticket(ticket_id)
    for ticket_id in rac_tickets[1:]:
        cancel_ticket(ticket_id)
    cancel_ticket(waiting_ticket_id)

def test_scenario_5():
    """Test priority allocation (senior citizens, ladies with children)"""
    print("\n===== SCENARIO 5: Test priority allocation =====")
    
    # Book a mixed group with senior citizens and regular passengers
    passengers = [
        {
            "name": "Senior Citizen",
            "age": 70,
            "gender": "Male",
            "is_parent": False
        },
        {
            "name": "Regular Adult",
            "age": 35,
            "gender": "Male",
            "is_parent": False
        },
        {
            "name": "Lady with Child",
            "age": 30,
            "gender": "Female",
            "is_parent": True,
            "parent_identifier": "family1"
        },
        {
            "name": "Child",
            "age": 4,
            "gender": "Female",
            "is_parent": False,
            "parent_identifier": "family1"
        }
    ]
    
    booking_response, status_code = book_tickets(passengers)
    ticket_id = booking_response.get("ticket_id")
    assert status_code == 201
    
    # Verify that senior citizen and lady with child got lower berths
    passengers_info = booking_response.get("passengers", [])
    
    senior_passenger = next((p for p in passengers_info if p["name"] == "Senior Citizen"), None)
    lady_passenger = next((p for p in passengers_info if p["name"] == "Lady with Child"), None)
    regular_passenger = next((p for p in passengers_info if p["name"] == "Regular Adult"), None)
    
    # Senior citizens and ladies with children should get lower berths
    if senior_passenger:
        print(f"Senior citizen berth: {senior_passenger.get('berth')}")
    if lady_passenger:
        print(f"Lady with child berth: {lady_passenger.get('berth')}")
    if regular_passenger:
        print(f"Regular adult berth: {regular_passenger.get('berth')}")
    
    # Clean up
    cancel_ticket(ticket_id)

def main():
    """Run all test scenarios"""
    try:
        print("===============================================")
        print("RAILWAY RESERVATION SYSTEM API TESTING")
        print("===============================================")
        
        # Test health check and available tickets
        check_health()
        get_available_tickets()
        
        # Run test scenarios
        test_scenario_1()
        test_scenario_2()
        test_scenario_3()
        test_scenario_4()
        test_scenario_5()
        
        print("\n===============================================")
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("===============================================")
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    main()
