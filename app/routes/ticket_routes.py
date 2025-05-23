from flask import Blueprint, request, jsonify, current_app
from app.services.ticket_service import TicketService
from app.db import db
from app.rate_limiter import limiter
from app.utils.error_handlers import ValidationError
import uuid
import time

# Create a blueprint for ticket routes
ticket_bp = Blueprint('tickets', __name__, url_prefix='/api/v1/tickets')

@ticket_bp.route('/health', methods=['GET'])
@limiter.exempt  # No rate limit for health checks
def health_check():
    """Health check endpoint for monitoring systems"""
    try:
        # Check database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db.session.commit()  # Add commit to ensure the connection is tested properly
        current_app.logger.info("Health check passed")
        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500

@ticket_bp.route('/book', methods=['POST'])
@limiter.limit("100 per hour")  # More permissive limit for testing
def book_ticket():
    """Book a new ticket"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    current_app.logger.info(f"Booking ticket request received [request_id={request_id}]")
    
    if not request.is_json:
        current_app.logger.warning(f"Non-JSON request received [request_id={request_id}]")
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    
    # Validate input
    if 'passengers' not in data or not isinstance(data['passengers'], list) or not data['passengers']:
        current_app.logger.warning(f"Invalid request data: missing or empty passengers list [request_id={request_id}]")
        raise ValidationError("Request must include a non-empty 'passengers' list", field="passengers")
        
    # Validate each passenger
    for passenger in data['passengers']:
        if not all(key in passenger for key in ['name', 'age', 'gender']):
            current_app.logger.warning(f"Invalid passenger data: missing required fields [request_id={request_id}]")
            raise ValidationError("Each passenger must have name, age and gender", field="passenger_data")
            
        try:
            # Convert age to integer
            passenger['age'] = int(passenger['age'])
        except ValueError:
            current_app.logger.warning(f"Invalid passenger age [request_id={request_id}]")
            raise ValidationError("Age must be a valid number", field="age")
    
    # Process booking
    response, status_code = TicketService.book_ticket(data['passengers'])
    
    # Log the result
    elapsed_time = time.time() - start_time
    if status_code == 201:
        current_app.logger.info(f"Ticket booked successfully: ticket_id={response.get('ticket_id')} [request_id={request_id}, elapsed={elapsed_time:.3f}s]")
    else:
        current_app.logger.warning(f"Ticket booking failed: {response.get('error')} [request_id={request_id}, elapsed={elapsed_time:.3f}s]")
    
    return jsonify(response), status_code

@ticket_bp.route('/cancel/<int:ticket_id>', methods=['DELETE'])
@limiter.limit("100 per hour")  # More permissive limit for testing
def cancel_ticket(ticket_id):
    """Cancel a ticket"""
    response, status_code = TicketService.cancel_ticket(ticket_id)
    return jsonify(response), status_code

@ticket_bp.route('/booked', methods=['GET'])
@limiter.limit("200 per hour")  # More permissive limit for testing
def get_booked_tickets():
    """Get all booked tickets"""
    response, status_code = TicketService.get_booked_tickets()
    return jsonify(response), status_code

@ticket_bp.route('/available', methods=['GET'])
@limiter.limit("200 per hour")  # More permissive limit for testing
def get_available_tickets():
    """Get available ticket counts"""
    response, status_code = TicketService.get_available_tickets()
    return jsonify(response), status_code
