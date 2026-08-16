from flask import Blueprint, jsonify, request, session, make_response
from models.booking import Booking
from models.movie import Movie
from services.booking_service import BookingService
from services.ticket_service import TicketService

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/showtimes/<int:showtime_id>/seats')
def get_seats(showtime_id):
    session_id = session.get('session_token', '')
    if 'user_id' in session and session.get('user_role') in ['CASHIER', 'ADMIN']:
        session_id = f"POS-CASHIER-{session.get('user_id')}"
    
    seat_map = Booking.get_showtime_seat_map(showtime_id, current_session_id=session_id)
    return jsonify({'success': True, 'seats': seat_map})

@api_bp.route('/api/seats/hold', methods=['POST'])
def hold_seats_api():
    data = request.json or {}
    showtime_id = data.get('showtime_id')
    seat_ids = data.get('seat_ids', [])

    if not session.get('session_token'):
        import uuid
        session['session_token'] = str(uuid.uuid4())
    
    session_id = session.get('session_token')
    if 'user_id' in session and session.get('user_role') in ['CASHIER', 'ADMIN']:
        session_id = f"POS-CASHIER-{session.get('user_id')}"

    res = BookingService.hold_seats(showtime_id, seat_ids, session_id)
    return jsonify(res)

@api_bp.route('/api/bookings/<int:booking_id>/pdf')
def download_ticket_pdf(booking_id):
    try:
        pdf_bytes = TicketService.generate_ticket_pdf(booking_id)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Ceylon_Cineplex_Ticket_{booking_id}.pdf'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@api_bp.route('/api/movies/search')
def search_movies_api():
    query = request.args.get('q', '').strip()
    movies_list = Movie.get_all(search_term=query, limit=10)
    return jsonify({'success': True, 'movies': movies_list})
