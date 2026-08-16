import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.movie import Movie
from models.showtime import Showtime
from models.booking import Booking
from models.hall import Hall
from models.user import User
from services.booking_service import BookingService
from routes.auth import login_required

customer_bp = Blueprint('customer', __name__)

def get_session_id():
    if 'session_token' not in session:
        session['session_token'] = str(uuid.uuid4())
    return session['session_token']

@customer_bp.route('/')
def index():
    now_showing = Movie.get_all(status='NOW SHOWING', limit=6)
    coming_soon = Movie.get_all(status='COMING SOON', limit=4)
    sinhala_movies = Movie.get_sinhala_movies()
    international_movies = Movie.get_international_movies()
    featured_movie = now_showing[0] if now_showing else None

    return render_template(
        'customer/index.html',
        featured_movie=featured_movie,
        now_showing=now_showing,
        coming_soon=coming_soon,
        sinhala_movies=sinhala_movies,
        international_movies=international_movies
    )

@customer_bp.route('/movies')
def movies():
    search = request.args.get('search', '').strip()
    genre = request.args.get('genre', '').strip()
    language = request.args.get('language', '').strip()
    status = request.args.get('status', '').strip()

    movie_list = Movie.get_all(
        search_term=search,
        genre=genre,
        language=language,
        status=status
    )
    return render_template(
        'customer/movies.html',
        movies=movie_list,
        search=search,
        genre=genre,
        language=language,
        status=status
    )

@customer_bp.route('/movies/<int:movie_id>')
def movie_details(movie_id):
    movie = Movie.get_by_id(movie_id)
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for('customer.movies'))

    showtimes = Showtime.get_by_movie(movie_id)
    
    # Group showtimes by date
    grouped_showtimes = {}
    for st in showtimes:
        sdate = str(st['show_date'])
        if sdate not in grouped_showtimes:
            grouped_showtimes[sdate] = []
        grouped_showtimes[sdate].append(st)

    return render_template(
        'customer/movie-details.html',
        movie=movie,
        grouped_showtimes=grouped_showtimes
    )

@customer_bp.route('/booking/seat-selection/<int:showtime_id>')
def seat_selection(showtime_id):
    st = Showtime.get_by_id(showtime_id)
    if not st:
        flash("Showtime not found or inactive.", "danger")
        return redirect(url_for('customer.movies'))

    session_id = get_session_id()
    seat_map = Booking.get_showtime_seat_map(showtime_id, current_session_id=session_id)
    seat_types = Hall.get_seat_types()

    return render_template(
        'customer/seat-selection.html',
        showtime=st,
        seat_map=seat_map,
        seat_types=seat_types,
        session_id=session_id
    )

@customer_bp.route('/booking/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        showtime_id = request.form.get('showtime_id')
        seat_ids_str = request.form.get('seat_ids', '')
        
        if not showtime_id or not seat_ids_str:
            flash("Invalid booking selection.", "danger")
            return redirect(url_for('customer.movies'))

        seat_ids = [int(s) for s in seat_ids_str.split(',') if s.isdigit()]
        session_id = get_session_id()

        # Hold seats for 5 mins
        hold_res = BookingService.hold_seats(showtime_id, seat_ids, session_id)
        if not hold_res['success']:
            flash(hold_res['message'], "danger")
            return redirect(url_for('customer.seat_selection', showtime_id=showtime_id))

        st = Showtime.get_by_id(showtime_id)
        
        # Calculate pricing
        seat_map = Booking.get_showtime_seat_map(showtime_id, current_session_id=session_id)
        selected_seats = [s for s in seat_map if s['seat_id'] in seat_ids]
        
        subtotal = sum(float(s['base_price_lkr']) for s in selected_seats)
        booking_fee = 50.00
        total = subtotal + booking_fee

        return render_template(
            'customer/checkout.html',
            showtime=st,
            selected_seats=selected_seats,
            seat_ids_str=seat_ids_str,
            subtotal=subtotal,
            booking_fee=booking_fee,
            total=total,
            user_name=session.get('user_name', ''),
            user_email=session.get('user_email', '')
        )
    
    return redirect(url_for('customer.movies'))

@customer_bp.route('/booking/process-payment', methods=['POST'])
def process_payment():
    showtime_id = request.form.get('showtime_id')
    seat_ids_str = request.form.get('seat_ids', '')
    customer_name = request.form.get('customer_name', '').strip()
    customer_email = request.form.get('customer_email', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    payment_method = request.form.get('payment_method', 'Credit Card').strip()

    if not customer_name or not customer_email or not customer_phone:
        flash("Please fill in all contact details.", "danger")
        return redirect(url_for('customer.movies'))

    seat_ids = [int(s) for s in seat_ids_str.split(',') if s.isdigit()]
    session_id = get_session_id()
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
        booking_source='ONLINE'
    )

    if res['success']:
        flash("Payment successful! Your tickets have been booked.", "success")
        return redirect(url_for('customer.booking_success', booking_id=res['booking_id']))
    else:
        flash(res['message'], "danger")
        return redirect(url_for('customer.seat_selection', showtime_id=showtime_id))

@customer_bp.route('/booking/success/<int:booking_id>')
def booking_success(booking_id):
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for('customer.index'))
    return render_template('customer/booking-success.html', booking=booking)

@customer_bp.route('/my-bookings')
@login_required
def my_bookings():
    user_id = session['user_id']
    bookings_list = Booking.get_by_user(user_id)
    return render_template('customer/my-bookings.html', bookings=bookings_list)

@customer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.get_by_id(session['user_id'])
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()

        User.update_profile(user['id'], full_name, phone)
        session['user_name'] = full_name
        flash("Profile updated successfully.", "success")
        return redirect(url_for('customer.profile'))

    return render_template('customer/profile.html', user=user)
