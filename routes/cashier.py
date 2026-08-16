from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.movie import Movie
from models.showtime import Showtime
from models.booking import Booking
from models.hall import Hall
from services.booking_service import BookingService
from routes.auth import login_required, role_required

cashier_bp = Blueprint('cashier', __name__)

@cashier_bp.route('/cashier')
@login_required
@role_required('CASHIER', 'ADMIN')
def dashboard():
    search = request.args.get('search', '').strip()
    show_date = request.args.get('date', '').strip()

    try:
        showtimes = Showtime.get_all(show_date=show_date if show_date else None) or []
        movies = Movie.get_all(status='NOW SHOWING') or []
        recent_bookings = Booking.get_all_admin(search_term=search if search else None) or []
        recent_bookings = recent_bookings[:15]
    except Exception as e:
        print(f"[Cashier Dashboard Error]: {e}")
        showtimes, movies, recent_bookings = [], [], []

    return render_template(
        'cashier/dashboard.html',
        showtimes=showtimes,
        movies=movies,
        recent_bookings=recent_bookings,
        search=search,
        selected_date=show_date
    )

@cashier_bp.route('/cashier/booking/<int:showtime_id>')
@login_required
@role_required('CASHIER', 'ADMIN')
def pos_booking(showtime_id):
    st = Showtime.get_by_id(showtime_id)
    if not st:
        flash("Showtime not found.", "danger")
        return redirect(url_for('cashier.dashboard'))

    session_id = f"POS-CASHIER-{session.get('user_id')}"
    seat_map = Booking.get_showtime_seat_map(showtime_id, current_session_id=session_id)
    seat_types = Hall.get_seat_types()

    return render_template(
        'cashier/booking.html',
        showtime=st,
        seat_map=seat_map,
        seat_types=seat_types,
        session_id=session_id
    )

@cashier_bp.route('/api/cashier/process-booking', methods=['POST'])
@login_required
@role_required('CASHIER', 'ADMIN')
def process_cashier_booking():
    data = request.json or {}
    showtime_id = data.get('showtime_id')
    seat_ids = data.get('seat_ids', [])
    customer_name = data.get('customer_name', 'Walk-in Customer').strip()
    customer_email = data.get('customer_email', 'walkin@ceyloncineplex.lk').strip()
    customer_phone = data.get('customer_phone', '+94700000000').strip()
    payment_method = data.get('payment_method', 'Cash').strip()

    session_id = f"POS-CASHIER-{session.get('user_id')}"
    user_id = session.get('user_id')

    res = BookingService.create_booking(
        showtime_id=showtime_id,
        seat_ids=seat_ids,
        session_id=session_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        payment_method=payment_method,
        user_id=user_id,
        booking_source='CASHIER'
    )

    if res['success']:
        return jsonify({
            'success': True,
            'booking_id': res['booking_id'],
            'booking_ref': res['booking_ref'],
            'total_amount': res['total_amount'],
            'redirect_url': url_for('customer.booking_success', booking_id=res['booking_id'])
        })
    else:
        return jsonify({'success': False, 'message': res['message']}), 400

@cashier_bp.route('/cashier/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@role_required('CASHIER', 'ADMIN')
def cancel_booking(booking_id):
    Booking.cancel_booking(booking_id, user_id=session.get('user_id'))
    flash("Booking cancelled successfully.", "success")
    return redirect(url_for('cashier.dashboard'))
