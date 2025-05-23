import os
import sys
import unittest
import json
import datetime
from app import create_app
from app.db import db
from app.models.berth import Berth
from app.models.ticket import Ticket
from app.models.passenger import Passenger
from app.models.berth_allocation_history import BerthAllocationHistory
from app.config import BerthType, Config, TicketStatus

class RailwayReservationTestCase(unittest.TestCase):
    """Test case for the railway reservation API"""
    
    def setUp(self):
        """Set up test client and initialize database"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Initialize berths
            # Create confirmed berths (63 total)
            # Distribution: 21 lower, 21 middle, 21 upper
            for i in range(1, 22):  # 21 of each type
                # Lower berth
                db.session.add(Berth(berth_type=BerthType.LOWER))
                
                # Middle berth
                db.session.add(Berth(berth_type=BerthType.MIDDLE))
                
                # Upper berth
                db.session.add(Berth(berth_type=BerthType.UPPER))
            
            # Create 9 side-lower berths for RAC (18 passengers, 2 per berth)
            for i in range(1, 10):
                db.session.add(Berth(berth_type=BerthType.SIDE_LOWER))
            
            db.session.commit()
            
            # Verify berth initialization
            berth_count = Berth.query.count()
            if berth_count != Config.CONFIRMED_BERTHS + 9:  # 63 confirmed + 9 side-lower (RAC)
                raise Exception(f"Expected {Config.CONFIRMED_BERTHS + 9} berths, found {berth_count}")
    
    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_book_ticket_confirmed(self):
        """Test booking a ticket with confirmed status"""
        # Create a booking request with senior citizen
        booking_data = {
            "passengers": [
                {
                    "name": "Senior Citizen",
                    "age": 65,
                    "gender": "male"
                }
            ]
        }
        
        # Send the request
        response = self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'confirmed')
        self.assertEqual(data['passengers'][0]['berth'], 'lower')
    
    def test_book_ticket_rac(self):
        """Test booking a ticket with RAC status after confirmed berths are full"""
        with self.app.app_context():
            # First, fill all confirmed berths except one
            for i in range(62):
                Berth.query.filter_by(is_allocated=False).first().is_allocated = True
            db.session.commit()
            
        # Book 2 tickets (1 confirmed, 1 RAC)
        booking_data = {
            "passengers": [
                {
                    "name": "Passenger 1",
                    "age": 35,
                    "gender": "male"
                },
                {
                    "name": "Passenger 2",
                    "age": 40,
                    "gender": "female"
                }
            ]
        }
        
        # Send the request
        response = self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'rac')
    
    def test_cancel_ticket(self):
        """Test cancelling a ticket"""
        # First book a ticket
        booking_data = {
            "passengers": [
                {
                    "name": "To Cancel",
                    "age": 35,
                    "gender": "male"
                }
            ]
        }
        
        # Book the ticket
        response = self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        ticket_id = json.loads(response.data)['ticket_id']
        
        # Now cancel it
        response = self.client.post(f'/api/v1/tickets/cancel/{ticket_id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
    
    def test_get_booked_tickets(self):
        """Test getting all booked tickets"""
        # First book a ticket
        booking_data = {
            "passengers": [
                {
                    "name": "Test Passenger",
                    "age": 35,
                    "gender": "male"
                }
            ]
        }
        
        # Book the ticket
        self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        # Get booked tickets
        response = self.client.get('/api/v1/tickets/booked')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('confirmed', data)
        self.assertIn('summary', data)
        self.assertEqual(data['summary']['total_count'], 1)
    
    def test_get_available_tickets(self):
        """Test getting available tickets"""
        response = self.client.get('/api/v1/tickets/available')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['confirmed_available'], 63)
        self.assertEqual(data['rac_available'], 18)
        self.assertEqual(data['waiting_list_available'], 10)
    
    def test_book_ticket_with_child(self):
        """Test booking a ticket with a parent and child"""
        booking_data = {
            "passengers": [
                {
                    "name": "Parent",
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
        
        # Send the request
        response = self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        
        # Parent should get a lower berth
        parent = next(p for p in data['passengers'] if p['name'] == 'Parent')
        self.assertEqual(parent['berth'], 'lower')
        
        # Child under 5 should not get a berth
        child = next(p for p in data['passengers'] if p['name'] == 'Child')
        self.assertIsNone(child.get('berth'))
    
    def test_waiting_list(self):
        """Test booking tickets going to waiting list"""
        with self.app.app_context():
            # Make sure we have a fresh DB with all berths
            db.session.query(Berth).update({Berth.is_allocated: False, Berth.passenger_id: None})
            db.session.commit()
            
            # First, allocate all confirmed berths
            for berth in Berth.query.filter(Berth.berth_type.in_([BerthType.LOWER, BerthType.MIDDLE, BerthType.UPPER])).all():
                berth.is_allocated = True
            
            # Allocate all RAC berths
            for berth in Berth.query.filter(Berth.berth_type == BerthType.SIDE_LOWER).all():
                berth.is_allocated = True
            
            # Create tickets with all RAC positions used
            for i in range(Config.RAC_BERTHS):
                ticket = Ticket(status=TicketStatus.RAC, rac_position=i+1)
                db.session.add(ticket)
            
            db.session.commit()
            
        # Try to book when all berths are allocated
        booking_data = {
            "passengers": [
                {
                    "name": "Waiting List Passenger",
                    "age": 35,
                    "gender": "male"
                }
            ]
        }
        
        # Send the request
        response = self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'waiting')
        self.assertIsNotNone(data['passengers'][0]['waiting_position'])
    
    def test_berth_promotion(self):
        """Test berth promotion after ticket cancellation"""
        with self.app.app_context():
            # Make sure we have a fresh DB with all berths
            db.session.query(Berth).update({Berth.is_allocated: False, Berth.passenger_id: None})
            db.session.query(Ticket).delete()
            db.session.query(Passenger).delete()
            db.session.query(BerthAllocationHistory).delete()
            
            # Allocate all but 1 berth to simulate a nearly full train
            berths = Berth.query.filter(
                Berth.berth_type.in_([BerthType.LOWER, BerthType.MIDDLE, BerthType.UPPER])
            ).all()
            
            # Leave only one berth unallocated
            for i in range(len(berths) - 1):
                berths[i].is_allocated = True
            
            db.session.commit()
        
        # First book a ticket for one passenger (should get confirmed status)
        confirmed_booking = {
            "passengers": [
                {
                    "name": "Confirmed Passenger",
                    "age": 35,
                    "gender": "male"
                }
            ]
        }
        
        # Book the confirmed ticket
        confirmed_response = self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(confirmed_booking),
            content_type='application/json'
        )
        
        confirmed_data = json.loads(confirmed_response.data)
        self.assertEqual(confirmed_data['status'], 'confirmed')
        confirmed_ticket_id = confirmed_data['ticket_id']
        
        # Now all berths should be allocated, so book another passenger to go to RAC
        rac_booking = {
            "passengers": [
                {
                    "name": "RAC Passenger",
                    "age": 40,
                    "gender": "female"
                }
            ]
        }
        
        # Book the RAC ticket
        rac_response = self.client.post(
            '/api/v1/tickets/book',
            data=json.dumps(rac_booking),
            content_type='application/json'
        )
        
        rac_data = json.loads(rac_response.data)
        self.assertEqual(rac_data['status'], 'rac')
        rac_ticket_id = rac_data['ticket_id']
        
        # Now cancel the confirmed ticket
        cancel_response = self.client.post(f'/api/v1/tickets/cancel/{confirmed_ticket_id}')
        self.assertEqual(cancel_response.status_code, 200)
        
        # Check if RAC passenger was promoted to confirmed
        get_tickets_response = self.client.get('/api/v1/tickets/booked')
        tickets_data = json.loads(get_tickets_response.data)
        
        # The RAC ticket should now be in confirmed list
        self.assertEqual(len(tickets_data['confirmed']), 1)
        self.assertEqual(len(tickets_data['rac']), 0)

if __name__ == '__main__':
    unittest.main()
