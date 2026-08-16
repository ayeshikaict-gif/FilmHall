from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.movie import Movie
from models.showtime import Showtime
from models.hall import Hall
from models.booking import Booking
from models.user import User
from models.audit import AuditLog
from database.db import execute_query
from routes.auth import login_required, role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
@role_required('ADMIN')
def dashboard():
    try:
        # Statistics calculations
        today_res = execute_query("""
            SELECT COUNT(*) as bookings_count, COALESCE(SUM(total_amount_lkr), 0) as revenue
            FROM bookings
            WHERE DATE(created_at) = CURDATE() AND booking_status != 'CANCELLED';
        """, fetchone=True)

        today_bookings = (today_res['bookings_count'] if today_res and 'bookings_count' in today_res else 0) or 0
        today_revenue = (today_res['revenue'] if today_res and 'revenue' in today_res else 0) or 0

        total_cust_res = execute_query("SELECT COUNT(*) as cnt FROM users WHERE role_id = 1;", fetchone=True)
        total_customers = (total_cust_res['cnt'] if total_cust_res and 'cnt' in total_cust_res else 0) or 0

        movies_res = execute_query("SELECT COUNT(*) as cnt FROM movies WHERE is_deleted = 0 AND status = 'NOW SHOWING';", fetchone=True)
        active_movies = (movies_res['cnt'] if movies_res and 'cnt' in movies_res else 0) or 0

        # Source breakdown (Online vs Cashier)
        source_res = execute_query("""
            SELECT booking_source, COUNT(*) as count, COALESCE(SUM(total_amount_lkr), 0) as total
            FROM bookings
            WHERE booking_status != 'CANCELLED'
            GROUP BY booking_source;
        """, fetchall=True) or []

        # Top popular movies by ticket count
        pop_movies = execute_query("""
            SELECT m.title, COUNT(bs.id) as tickets_sold, COALESCE(SUM(bs.price_lkr), 0) as revenue
            FROM booking_seats bs
            JOIN bookings b ON bs.booking_id = b.id
            JOIN showtimes st ON b.showtime_id = st.id
            JOIN movies m ON st.movie_id = m.id
            WHERE b.booking_status != 'CANCELLED'
            GROUP BY m.id, m.title
            ORDER BY tickets_sold DESC
            LIMIT 5;
        """, fetchall=True) or []

        # Recent Audit Logs
        recent_logs = AuditLog.get_recent(limit=10) or []

        return render_template(
            'admin/dashboard.html',
            today_bookings=today_bookings,
            today_revenue=today_revenue,
            total_customers=total_customers,
            active_movies=active_movies,
            source_breakdown=source_res,
            popular_movies=pop_movies,
            recent_logs=recent_logs
        )
    except Exception as e:
        print(f"[Admin Dashboard Error]: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Dashboard metrics notice: {str(e)}", "warning")
        return render_template(
            'admin/dashboard.html',
            today_bookings=0,
            today_revenue=0,
            total_customers=0,
            active_movies=0,
            source_breakdown=[],
            popular_movies=[],
            recent_logs=[]
        )

@admin_bp.route('/admin/movies', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def movies():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            title = request.form.get('title')
            title_sinhala = request.form.get('title_sinhala')
            poster_url = request.form.get('poster_url')
            backdrop_url = request.form.get('backdrop_url')
            description = request.form.get('description')
            genre = request.form.get('genre')
            duration_mins = int(request.form.get('duration_mins', 120))
            language = request.form.get('language')
            country = request.form.get('country', 'Sri Lanka')
            release_date = request.form.get('release_date')
            age_rating = request.form.get('age_rating', 'PG-13')
            director = request.form.get('director')
            cast = request.form.get('cast')
            trailer_url = request.form.get('trailer_url')
            status = request.form.get('status', 'NOW SHOWING')

            movie_id = Movie.create(title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status)
            AuditLog.log(session.get('user_id'), "ADD_MOVIE", f"Added movie: {title} (ID: {movie_id})", request.remote_addr)
            flash(f"Movie '{title}' added successfully.", "success")

        elif action == 'edit':
            movie_id = int(request.form.get('movie_id'))
            title = request.form.get('title')
            title_sinhala = request.form.get('title_sinhala')
            poster_url = request.form.get('poster_url')
            backdrop_url = request.form.get('backdrop_url')
            description = request.form.get('description')
            genre = request.form.get('genre')
            duration_mins = int(request.form.get('duration_mins', 120))
            language = request.form.get('language')
            country = request.form.get('country')
            release_date = request.form.get('release_date')
            age_rating = request.form.get('age_rating')
            director = request.form.get('director')
            cast = request.form.get('cast')
            trailer_url = request.form.get('trailer_url')
            status = request.form.get('status')

            Movie.update(movie_id, title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status)
            AuditLog.log(session.get('user_id'), "EDIT_MOVIE", f"Updated movie ID {movie_id}: {title}", request.remote_addr)
            flash(f"Movie '{title}' updated successfully.", "success")

        return redirect(url_for('admin.movies'))

    all_movies = Movie.get_all(include_deleted=False)
    return render_template('admin/movies.html', movies=all_movies)

@admin_bp.route('/admin/movies/<int:movie_id>/delete', methods=['POST'])
@login_required
@role_required('ADMIN')
def delete_movie(movie_id):
    Movie.soft_delete(movie_id)
    AuditLog.log(session.get('user_id'), "DELETE_MOVIE", f"Soft deleted movie ID {movie_id}", request.remote_addr)
    flash("Movie archived successfully.", "info")
    return redirect(url_for('admin.movies'))

@admin_bp.route('/admin/showtimes', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def showtimes():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            movie_id = int(request.form.get('movie_id'))
            hall_id = int(request.form.get('hall_id'))
            show_date = request.form.get('show_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')

            try:
                Showtime.create(movie_id, hall_id, show_date, start_time, end_time)
                AuditLog.log(session.get('user_id'), "ADD_SHOWTIME", f"Created showtime for movie {movie_id} in hall {hall_id} on {show_date}", request.remote_addr)
                flash("Showtime created successfully.", "success")
            except ValueError as ve:
                flash(str(ve), "danger")

        elif action == 'edit':
            st_id = int(request.form.get('showtime_id'))
            movie_id = int(request.form.get('movie_id'))
            hall_id = int(request.form.get('hall_id'))
            show_date = request.form.get('show_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')

            try:
                Showtime.update(st_id, movie_id, hall_id, show_date, start_time, end_time)
                AuditLog.log(session.get('user_id'), "EDIT_SHOWTIME", f"Updated showtime ID {st_id}", request.remote_addr)
                flash("Showtime updated successfully.", "success")
            except ValueError as ve:
                flash(str(ve), "danger")

        return redirect(url_for('admin.showtimes'))

    showtimes_list = Showtime.get_all()
    movies_list = Movie.get_all(status='NOW SHOWING')
    halls_list = Hall.get_all()

    return render_template(
        'admin/showtimes.html',
        showtimes=showtimes_list,
        movies=movies_list,
        halls=halls_list
    )

@admin_bp.route('/admin/showtimes/<int:showtime_id>/delete', methods=['POST'])
@login_required
@role_required('ADMIN')
def delete_showtime(showtime_id):
    Showtime.delete(showtime_id)
    AuditLog.log(session.get('user_id'), "DELETE_SHOWTIME", f"Deactivated showtime ID {showtime_id}", request.remote_addr)
    flash("Showtime removed.", "info")
    return redirect(url_for('admin.showtimes'))

@admin_bp.route('/admin/halls', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def halls():
    if request.method == 'POST':
        seat_type_id = int(request.form.get('seat_type_id'))
        price = float(request.form.get('price_lkr'))
        Hall.update_seat_price(seat_type_id, price)
        AuditLog.log(session.get('user_id'), "UPDATE_SEAT_PRICE", f"Updated seat type ID {seat_type_id} price to LKR {price:.2f}", request.remote_addr)
        flash("Seat pricing updated successfully.", "success")
        return redirect(url_for('admin.halls'))

    halls_list = Hall.get_all()
    seat_types = Hall.get_seat_types()
    return render_template('admin/halls.html', halls=halls_list, seat_types=seat_types)

@admin_bp.route('/admin/bookings')
@login_required
@role_required('ADMIN')
def bookings():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    source = request.args.get('source', '').strip()

    bookings_list = Booking.get_all_admin(
        search_term=search if search else None,
        status=status if status else None,
        source=source if source else None
    )

    return render_template(
        'admin/bookings.html',
        bookings=bookings_list,
        search=search,
        status=status,
        source=source
    )

@admin_bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def users():
    if request.method == 'POST':
        target_user_id = int(request.form.get('user_id'))
        role_id = int(request.form.get('role_id'))
        User.update_role(target_user_id, role_id)
        AuditLog.log(session.get('user_id'), "UPDATE_USER_ROLE", f"Updated user ID {target_user_id} role to {role_id}", request.remote_addr)
        flash("User role updated successfully.", "success")
        return redirect(url_for('admin.users'))

    users_list = User.get_all()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/admin/reports')
@login_required
@role_required('ADMIN')
def reports():
    try:
        daily_sales = execute_query("""
            SELECT DATE(created_at) as sale_date, COUNT(*) as bookings_count, COALESCE(SUM(total_amount_lkr), 0) as revenue
            FROM bookings
            WHERE booking_status != 'CANCELLED'
            GROUP BY DATE(created_at)
            ORDER BY sale_date DESC
            LIMIT 14;
        """, fetchall=True) or []

        movie_stats = execute_query("""
            SELECT m.title, COUNT(DISTINCT b.id) as total_bookings, COUNT(bs.id) as total_tickets, COALESCE(SUM(bs.price_lkr), 0) as total_revenue
            FROM movies m
            LEFT JOIN showtimes st ON m.id = st.movie_id
            LEFT JOIN bookings b ON st.id = b.showtime_id AND b.booking_status != 'CANCELLED'
            LEFT JOIN booking_seats bs ON b.id = bs.booking_id
            WHERE m.is_deleted = 0
            GROUP BY m.id, m.title
            ORDER BY total_revenue DESC;
        """, fetchall=True) or []

        return render_template('admin/reports.html', daily_sales=daily_sales, movie_stats=movie_stats)
    except Exception as e:
        print(f"[Admin Reports Error]: {e}")
        flash(f"Reports notice: {str(e)}", "warning")
        return render_template('admin/reports.html', daily_sales=[], movie_stats=[])

@admin_bp.route('/admin/audit-logs')
@login_required
@role_required('ADMIN')
def audit_logs():
    logs = AuditLog.get_recent(limit=100)
    return render_template('admin/audit-logs.html', logs=logs)
