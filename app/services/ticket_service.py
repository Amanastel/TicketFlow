from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func

from app.db import db
from app.models.ticket import Ticket
from app.models.passenger import Passenger
from app.models.berth import Berth
from app.models.berth_allocation_history import BerthAllocationHistory
from app.config import TicketStatus, BerthType, Config
from app.utils.error_handlers import (
    ResourceNotFoundError, 
    NoAvailabilityError, 
    ValidationError,
    ConcurrencyError,
    DatabaseError
)

class TicketService:
    """Service for handling ticket booking and cancellation operations"""
    
    @staticmethod
    def book_ticket(passengers_data: List[Dict[str, Any]]) -> Tuple[Dict, int]:
        """
        Book a ticket for a list of passengers
        
        Args:
            passengers_data: List of passenger data dictionaries
        
        Returns:
            Tuple containing response data and HTTP status code
        """
        try:
            # Start a transaction
            db.session.begin_nested()
            
            # First, check if we have enough space in the system
            # Count passengers who need berths (age >= 5)
            passengers_needing_berths = [p for p in passengers_data if p.get('age', 0) >= Config.MIN_AGE_FOR_BERTH]
            
            if not passengers_needing_berths:
                raise ValidationError("At least one passenger must be 5 years or older", field="passengers")
                
            num_berths_needed = len(passengers_needing_berths)
            
            # Lock rows for update to prevent race conditions
            current_status = TicketService._get_current_status(for_update=True)
            
            # Determine if we can accommodate the request
            if current_status['waiting_list_available'] == 0 and num_berths_needed > current_status['confirmed_available'] + current_status['rac_available']:
                raise NoAvailabilityError("No tickets available for the requested number of passengers")
            
            # Create a new ticket
            ticket = Ticket()
            db.session.add(ticket)
            db.session.flush()  # Get the ticket ID
            
            # Process parent passengers first, then children
            parent_map = {}  # To store parent IDs for children
            
            # First process all passengers
            for passenger_data in passengers_data:
                passenger = Passenger(
                    name=passenger_data['name'],
                    age=passenger_data['age'],
                    gender=passenger_data['gender'],
                    child=passenger_data['age'] < Config.MIN_AGE_FOR_BERTH,
                    ticket_id=ticket.id
                )
                
                db.session.add(passenger)
                db.session.flush()  # Get the passenger ID
                
                # Store parent information for linking children later
                if passenger_data.get('is_parent', False):
                    parent_map[passenger_data.get('parent_identifier', '')] = passenger.id
                
            # Now link children to parents
            for passenger_data in passengers_data:
                if passenger_data.get('parent_identifier') and not passenger_data.get('is_parent', False):
                    parent_id = parent_map.get(passenger_data.get('parent_identifier'))
                    if parent_id:
                        # Find this passenger and update parent_id
                        child_passenger = Passenger.query.filter_by(
                            name=passenger_data['name'],
                            age=passenger_data['age'],
                            ticket_id=ticket.id
                        ).first()
                        if child_passenger:
                            child_passenger.parent_id = parent_id
            
            # Now handle berth allocation based on availability
            passengers_for_berths = Passenger.query.filter(
                and_(
                    Passenger.ticket_id == ticket.id,
                    Passenger.age >= Config.MIN_AGE_FOR_BERTH
                )
            ).all()
            
            # Allocate berths based on priority
            result = TicketService._allocate_berths(ticket, passengers_for_berths)
            
            # Commit the transaction
            db.session.commit()
            
            # Prepare response data
            response_data = {
                "ticket_id": ticket.id,
                "status": ticket.status,
                "passengers": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "age": p.age,
                        "gender": p.gender,
                        "berth": p.berth.berth_type if p.berth else None,
                        "rac_position": ticket.rac_position if ticket.status == TicketStatus.RAC else None,
                        "waiting_position": ticket.waiting_position if ticket.status == TicketStatus.WAITING else None
                    } 
                    for p in Passenger.query.filter_by(ticket_id=ticket.id).all()
                ]
            }
            
            return response_data, 201
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": f"Database error: {str(e)}"}, 500
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error: {str(e)}"}, 500
    
    @staticmethod
    def cancel_ticket(ticket_id: int) -> Tuple[Dict, int]:
        """
        Cancel a ticket and promote RAC and waiting list tickets
        
        Args:
            ticket_id: ID of the ticket to cancel
            
        Returns:
            Tuple containing response data and HTTP status code
        """
        try:
            # Start a transaction with isolation
            db.session.begin_nested()
            
            # Get the ticket with FOR UPDATE lock
            ticket = Ticket.query.with_for_update().filter_by(id=ticket_id).first()
            
            if not ticket:
                raise ResourceNotFoundError("Ticket", ticket_id)
                
            if ticket.status == TicketStatus.CANCELLED:
                raise ValidationError("Ticket is already cancelled", field="ticket_status")
            
            # Get all berths that need to be freed
            berths_to_free = []
            for passenger in ticket.passengers:
                if passenger.berth:
                    berths_to_free.append(passenger.berth)
                    # Unlink passenger from berth
                    passenger.berth.is_allocated = False
                    passenger.berth.passenger_id = None
            
            # Update ticket status
            old_status = ticket.status
            ticket.status = TicketStatus.CANCELLED
            
            # If the ticket was confirmed or RAC, we need to promote others
            if old_status in [TicketStatus.CONFIRMED, TicketStatus.RAC]:
                TicketService._promote_tickets(berths_to_free)
            
            # Commit the transaction
            db.session.commit()
            
            return {"message": f"Ticket {ticket_id} has been cancelled successfully"}, 200
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": f"Database error: {str(e)}"}, 500
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error: {str(e)}"}, 500
    
    @staticmethod
    def get_booked_tickets() -> Tuple[Dict, int]:
        """
        Get all booked tickets with their details
        
        Returns:
            Tuple containing response data and HTTP status code
        """
        try:
            # Get all active tickets (not cancelled)
            tickets = Ticket.query.filter(Ticket.status != TicketStatus.CANCELLED).all()
            
            response_data = {
                "confirmed": [],
                "rac": [],
                "waiting": [],
                "summary": {
                    "confirmed_count": 0,
                    "rac_count": 0,
                    "waiting_count": 0,
                    "total_count": 0
                }
            }
            
            for ticket in tickets:
                ticket_data = {
                    "ticket_id": ticket.id,
                    "booking_time": ticket.booking_time.isoformat(),
                    "passengers": []
                }
                
                for passenger in ticket.passengers:
                    passenger_data = {
                        "id": passenger.id,
                        "name": passenger.name,
                        "age": passenger.age,
                        "gender": passenger.gender,
                        "berth": passenger.berth.berth_type if passenger.berth else None
                    }
                    
                    if ticket.status == TicketStatus.RAC:
                        passenger_data["rac_position"] = ticket.rac_position
                    elif ticket.status == TicketStatus.WAITING:
                        passenger_data["waiting_position"] = ticket.waiting_position
                        
                    ticket_data["passengers"].append(passenger_data)
                
                # Add ticket to appropriate category
                response_data[ticket.status].append(ticket_data)
                response_data["summary"][f"{ticket.status}_count"] += 1
                response_data["summary"]["total_count"] += 1
            
            return response_data, 200
            
        except Exception as e:
            return {"error": f"Error: {str(e)}"}, 500
    
    @staticmethod
    def get_available_tickets() -> Tuple[Dict, int]:
        """
        Get available ticket counts and details
        
        Returns:
            Tuple containing response data and HTTP status code
        """
        try:
            current_status = TicketService._get_current_status()
            
            response_data = {
                "confirmed_available": current_status["confirmed_available"],
                "rac_available": current_status["rac_available"],
                "waiting_list_available": current_status["waiting_list_available"],
                "available_berths": {
                    "lower": current_status["available_berths"]["lower"],
                    "middle": current_status["available_berths"]["middle"],
                    "upper": current_status["available_berths"]["upper"],
                    "side_lower": current_status["available_berths"]["side_lower"]
                }
            }
            
            return response_data, 200
            
        except Exception as e:
            return {"error": f"Error: {str(e)}"}, 500
    
    @staticmethod
    def _get_current_status(for_update: bool = False) -> Dict[str, Any]:
        """
        Get the current status of available berths, RAC, and waiting list
        
        Args:
            for_update: Whether to lock rows for update (used in transactions)
            
        Returns:
            Dictionary with current status information
        """
        # Count confirmed tickets
        confirmed_query = Berth.query
        if for_update:
            confirmed_query = confirmed_query.with_for_update()
            
        confirmed_berths_used = confirmed_query.filter_by(is_allocated=True).count()
        
        # Count RAC tickets
        rac_query = Ticket.query.filter_by(status=TicketStatus.RAC)
        if for_update:
            rac_query = rac_query.with_for_update()
        rac_used = rac_query.count()
        
        # Count waiting list
        waiting_query = Ticket.query.filter_by(status=TicketStatus.WAITING)
        if for_update:
            waiting_query = waiting_query.with_for_update()
        waiting_used = waiting_query.count()
        
        # Get available berths by type
        berth_query = Berth.query.filter_by(is_allocated=False)
        if for_update:
            berth_query = berth_query.with_for_update()
        
        available_berths = {
            "lower": berth_query.filter_by(berth_type=BerthType.LOWER).count(),
            "middle": berth_query.filter_by(berth_type=BerthType.MIDDLE).count(),
            "upper": berth_query.filter_by(berth_type=BerthType.UPPER).count(),
            "side_lower": berth_query.filter_by(berth_type=BerthType.SIDE_LOWER).count()
        }
        
        return {
            "confirmed_available": Config.CONFIRMED_BERTHS - confirmed_berths_used,
            "rac_available": Config.RAC_BERTHS - rac_used,
            "waiting_list_available": Config.WAITING_LIST_MAX - waiting_used,
            "available_berths": available_berths
        }
    
    @staticmethod
    def _allocate_berths(ticket: Ticket, passengers: List[Passenger]) -> bool:
        """
        Allocate berths to passengers based on priority and availability
        
        Args:
            ticket: The ticket object
            passengers: List of passengers who need berths
            
        Returns:
            True if allocation was successful
        """
        # Get the current status
        current_status = TicketService._get_current_status(for_update=True)
        
        # Check what we can allocate
        num_passengers = len(passengers)
        confirmed_available = current_status["confirmed_available"]
        rac_available = current_status["rac_available"]
        waiting_available = current_status["waiting_list_available"]
        
        # Sort passengers by priority:
        # 1. Seniors (age >= 60)
        # 2. Ladies with children
        # 3. Everyone else
        priority_passengers = sorted(
            passengers,
            key=lambda p: (
                -1 if p.is_senior else (0 if p.is_lady_with_child else 1),
                -p.age  # Secondary sort by age in descending order
            )
        )
        
        # Determine the ticket status
        if num_passengers <= confirmed_available:
            # All can be confirmed
            ticket.status = TicketStatus.CONFIRMED
            
            # Allocate berths with priority for lower berths
            TicketService._allocate_confirmed_berths(ticket, priority_passengers)
            
        elif num_passengers <= confirmed_available + rac_available:
            # Some confirmed, some RAC
            confirmed_passengers = priority_passengers[:confirmed_available]
            rac_passengers = priority_passengers[confirmed_available:]
            
            # Allocate confirmed berths
            if confirmed_passengers:
                TicketService._allocate_confirmed_berths(ticket, confirmed_passengers)
            
            # Allocate RAC
            ticket.status = TicketStatus.RAC
            TicketService._allocate_rac_berths(ticket, rac_passengers)
            
        elif num_passengers <= confirmed_available + rac_available + waiting_available:
            # Some confirmed, some RAC, some waiting
            confirmed_passengers = priority_passengers[:confirmed_available]
            rac_passengers = priority_passengers[confirmed_available:confirmed_available+rac_available]
            waiting_passengers = priority_passengers[confirmed_available+rac_available:]
            
            # Allocate confirmed berths
            if confirmed_passengers:
                TicketService._allocate_confirmed_berths(ticket, confirmed_passengers)
            
            # Allocate RAC
            if rac_passengers:
                # If all passengers would get RAC or waiting status, just put them all in waiting
                if not confirmed_passengers and waiting_passengers:
                    ticket.status = TicketStatus.WAITING
                    TicketService._allocate_waiting_list(ticket, priority_passengers)
                    return True
                    
                TicketService._allocate_rac_berths(ticket, rac_passengers)
            
            # Allocate waiting list
            if waiting_passengers:
                ticket.status = TicketStatus.WAITING
                TicketService._allocate_waiting_list(ticket, waiting_passengers)
        else:
            # Reject - not enough space
            return False
            
        return True
        
    @staticmethod
    def _allocate_confirmed_berths(ticket: Ticket, passengers: List[Passenger]) -> None:
        """
        Allocate confirmed berths to passengers
        
        Args:
            ticket: The ticket object
            passengers: List of passengers who need confirmed berths
        """
        # First prioritize lower berths for seniors and ladies with children
        priority_passengers = [p for p in passengers if p.is_senior or p.is_lady_with_child]
        regular_passengers = [p for p in passengers if not (p.is_senior or p.is_lady_with_child)]
        
        # Allocate lower berths to priority passengers
        for passenger in priority_passengers:
            # Find an available lower berth
            berth = Berth.query.filter_by(
                berth_type=BerthType.LOWER, 
                is_allocated=False
            ).first()
            
            if berth:
                # Allocate this berth
                berth.is_allocated = True
                berth.passenger_id = passenger.id
                
                # Record allocation history
                history = BerthAllocationHistory(
                    ticket_id=ticket.id,
                    berth_id=berth.id
                )
                db.session.add(history)
            else:
                # No lower berths available, add to regular passengers
                regular_passengers.append(passenger)
        
        # Now allocate any berth to regular passengers
        for passenger in regular_passengers:
            # Find any available berth
            berth = Berth.query.filter_by(is_allocated=False).first()
            
            if berth:
                # Allocate this berth
                berth.is_allocated = True
                berth.passenger_id = passenger.id
                
                # Record allocation history
                history = BerthAllocationHistory(
                    ticket_id=ticket.id,
                    berth_id=berth.id
                )
                db.session.add(history)
    
    @staticmethod
    def _allocate_rac_berths(ticket: Ticket, passengers: List[Passenger]) -> None:
        """
        Allocate RAC berths to passengers
        
        Args:
            ticket: The ticket object
            passengers: List of passengers who need RAC berths
        """
        # Find the next RAC position
        max_rac_position = db.session.query(func.max(Ticket.rac_position)).filter(
            Ticket.status == TicketStatus.RAC
        ).scalar() or 0
        
        # Allocate side-lower berths for RAC passengers
        rac_position = max_rac_position + 1
        ticket.rac_position = rac_position
        ticket.status = TicketStatus.RAC
        
        # For RAC, we use side-lower berths (2 passengers per berth)
        # Each side-lower berth can accommodate 2 RAC passengers
        side_lower_berths = Berth.query.filter_by(
            berth_type=BerthType.SIDE_LOWER, 
            is_allocated=False
        ).all()
        
        for i, passenger in enumerate(passengers):
            if i < len(side_lower_berths):
                berth = side_lower_berths[i]
                berth.is_allocated = True
                berth.passenger_id = passenger.id
                
                # Record allocation history
                history = BerthAllocationHistory(
                    ticket_id=ticket.id,
                    berth_id=berth.id,
                    rac_position=rac_position
                )
                db.session.add(history)
    
    @staticmethod
    def _allocate_waiting_list(ticket: Ticket, passengers: List[Passenger]) -> None:
        """
        Allocate waiting list positions to passengers
        
        Args:
            ticket: The ticket object
            passengers: List of passengers who need waiting list positions
        """
        # Find the next waiting list position
        max_waiting_position = db.session.query(func.max(Ticket.waiting_position)).filter(
            Ticket.status == TicketStatus.WAITING
        ).scalar() or 0
        
        # Assign waiting list position
        waiting_position = max_waiting_position + 1
        ticket.waiting_position = waiting_position
        ticket.status = TicketStatus.WAITING
        
        # Record history for all passengers in this waiting list
        for passenger in passengers:
            history = BerthAllocationHistory(
                ticket_id=ticket.id,
                berth_id=None,  # No berth allocated yet
                waiting_position=waiting_position
            )
            db.session.add(history)
    
    @staticmethod
    def _promote_tickets(freed_berths: List[Berth]) -> None:
        """
        Promote tickets from RAC to confirmed and waiting list to RAC
        
        Args:
            freed_berths: List of berths that were freed by cancellation
        """
        if not freed_berths:
            return
            
        # First, get all RAC tickets ordered by booking time (oldest first)
        rac_tickets = Ticket.query.filter_by(status=TicketStatus.RAC).order_by(Ticket.booking_time).all()
        
        if not rac_tickets:
            return  # No RAC tickets to promote
            
        # For each freed berth, promote a passenger from RAC
        for berth in freed_berths:
            if not rac_tickets:
                break  # No more RAC tickets to promote
                
            # Get the oldest RAC ticket
            rac_ticket = rac_tickets[0]
            
            # Find a passenger to promote (one that doesn't have a confirmed berth)
            passenger = None
            for p in rac_ticket.passengers:
                if p.age >= Config.MIN_AGE_FOR_BERTH and (not p.berth or p.berth.berth_type == BerthType.SIDE_LOWER):
                    passenger = p
                    break
                    
            if not passenger:
                # All passengers already have confirmed berths or are children, try next ticket
                rac_tickets.pop(0)
                continue
                
            # Update the berth allocation
            if passenger.berth:
                # Free the old RAC berth
                old_berth = passenger.berth
                old_berth.is_allocated = False
                old_berth.passenger_id = None
            
            # Allocate the new confirmed berth
            berth.is_allocated = True
            berth.passenger_id = passenger.id
            
            # Record the allocation
            history = BerthAllocationHistory(
                ticket_id=rac_ticket.id,
                berth_id=berth.id
            )
            db.session.add(history)
            
            # Update passenger's berth reference directly
            passenger.berth = berth
            
            # Check if all passengers in this ticket now have confirmed berths
            # A passenger has a confirmed berth if they have a berth and it's not a side-lower berth
            all_confirmed = True
            for p in rac_ticket.passengers:
                if p.age >= Config.MIN_AGE_FOR_BERTH:
                    has_confirmed_berth = p.berth and p.berth.berth_type in [BerthType.LOWER, BerthType.MIDDLE, BerthType.UPPER]
                    if not has_confirmed_berth:
                        all_confirmed = False
                        break
            
            if all_confirmed:
                # Update ticket status to confirmed
                rac_ticket.status = TicketStatus.CONFIRMED
                rac_ticket.rac_position = None
                # Remove this ticket from our list
                rac_tickets.pop(0)
        
        # Now promote waiting list tickets to RAC if there are any RAC positions available
        # Count how many RAC spots are available
        rac_used = Ticket.query.filter_by(status=TicketStatus.RAC).count()
        rac_available = Config.RAC_BERTHS - rac_used
        
        if rac_available > 0:
            # Find waiting list tickets to promote (oldest first)
            waiting_tickets = Ticket.query.filter_by(
                status=TicketStatus.WAITING
            ).order_by(Ticket.booking_time).limit(rac_available).all()
            
            for waiting_ticket in waiting_tickets:
                # Find the next RAC position
                max_rac_position = db.session.query(func.max(Ticket.rac_position)).filter(
                    Ticket.status == TicketStatus.RAC
                ).scalar() or 0
                
                new_rac_position = max_rac_position + 1
                
                # Promote to RAC
                waiting_ticket.status = TicketStatus.RAC
                waiting_ticket.rac_position = new_rac_position
                waiting_ticket.waiting_position = None
                
                # Allocate side-lower berths if available
                side_lower_berth = Berth.query.filter_by(
                    berth_type=BerthType.SIDE_LOWER, 
                    is_allocated=False
                ).first()
                
                if side_lower_berth:
                    # Find a passenger to assign this berth to
                    passenger = Passenger.query.filter(
                        Passenger.ticket_id == waiting_ticket.id,
                        Passenger.age >= Config.MIN_AGE_FOR_BERTH
                    ).first()
                    
                    if passenger:
                        side_lower_berth.is_allocated = True
                        side_lower_berth.passenger_id = passenger.id
                        passenger.berth = side_lower_berth  # Update passenger's berth reference directly
                        
                        # Record allocation
                        history = BerthAllocationHistory(
                            ticket_id=waiting_ticket.id,
                            berth_id=side_lower_berth.id,
                            rac_position=new_rac_position
                        )
                        db.session.add(history)
