from database.db import execute_query, get_db_connection
import datetime

class Booking:
    @staticmethod
    def get_by_id(booking_id):
        query = """
            SELECT b.*, m.title as movie_title, m.poster_url, m.duration_mins, m.language,
                   h.name as hall_name, st.show_date, st.start_time, st.end_time,
                   p.payment_method, p.transaction_ref
            FROM bookings b
            JOIN showtimes st ON b.showtime_id = st.id
            JOIN movies m ON st.movie_id = m.id
            JOIN halls h ON st.hall_id = h.id
            LEFT JOIN payments p ON p.booking_id = b.id
            WHERE b.id = ?;
        """
        booking = execute_query(query, (booking_id,), fetchone=True)
        if booking:
            # Attach seats
            seats_query = """
                SELECT bs.price_lkr, s.seat_number, s.row_label, s.col_number, st.name as seat_type_name
                FROM booking_seats bs
                JOIN seats s ON bs.seat_id = s.id
                JOIN seat_types st ON s.seat_type_id = st.id
                WHERE bs.booking_id = ?
                ORDER BY s.seat_number ASC;
            """
            booking['seats'] = execute_query(seats_query, (booking_id,), fetchall=True)
        return booking

    @staticmethod
    def get_by_ref(booking_ref):
        query = "SELECT id FROM bookings WHERE booking_ref = ?;"
        res = execute_query(query, (booking_ref,), fetchone=True)
        if res:
            return Booking.get_by_id(res['id'])
        return None

    @staticmethod
    def get_by_user(user_id):
        query = """
            SELECT b.*, m.title as movie_title, m.poster_url, h.name as hall_name,
                   st.show_date, st.start_time
            FROM bookings b
            JOIN showtimes st ON b.showtime_id = st.id
            JOIN movies m ON st.movie_id = m.id
            JOIN halls h ON st.hall_id = h.id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC;
        """
        bookings = execute_query(query, (user_id,), fetchall=True)
        for bk in bookings:
            seats_query = """
                SELECT s.seat_number FROM booking_seats bs
                JOIN seats s ON bs.seat_id = s.id
                WHERE bs.booking_id = ? ORDER BY s.seat_number ASC;
            """
            seats_res = execute_query(seats_query, (bk['id'],), fetchall=True)
            bk['seats_str'] = ", ".join([s['seat_number'] for s in seats_res])
        return bookings

    @staticmethod
    def get_showtime_seat_map(showtime_id, current_session_id=None):
        """
        Retrieves all seats for the showtime's hall along with live status:
        'AVAILABLE', 'SELECTED' (by current_session_id), 'HELD' (by another session), or 'BOOKED'.
        """
        showtime_id = int(showtime_id)

        # Fetch showtime to get hall_id
        st_query = "SELECT hall_id FROM showtimes WHERE id = ?;"
        st = execute_query(st_query, (showtime_id,), fetchone=True)
        if not st:
            return []

        hall_id = st['hall_id']

        # Get all seats in hall
        seats_query = """
            SELECT s.id as seat_id, s.seat_number, s.row_label, s.col_number,
                   st.id as seat_type_id, st.name as seat_type_name, st.base_price_lkr, st.color_code
            FROM seats s
            JOIN seat_types st ON s.seat_type_id = st.id
            WHERE s.hall_id = ?
            ORDER BY s.row_label ASC, s.col_number ASC;
        """
        all_seats = execute_query(seats_query, (hall_id,), fetchall=True)

        # Get booked seats for this showtime
        booked_query = """
            SELECT bs.seat_id
            FROM booking_seats bs
            JOIN bookings b ON bs.booking_id = b.id
            WHERE b.showtime_id = ? AND b.booking_status != 'CANCELLED';
        """
        booked_res = execute_query(booked_query, (showtime_id,), fetchall=True)
        booked_seat_ids = set(int(r['seat_id']) for r in booked_res)

        # Clean expired holds first
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_holds_query = "DELETE FROM seat_holds WHERE expires_at <= ?;"
        try:
            execute_query(clean_holds_query, (now_str,), commit=True)
        except Exception:
            pass

        # Get active seat holds
        holds_query = """
            SELECT seat_id, session_id, expires_at
            FROM seat_holds
            WHERE showtime_id = ? AND expires_at > ?;
        """
        holds_res = execute_query(holds_query, (showtime_id, now_str), fetchall=True)
        holds_map = {int(h['seat_id']): h for h in holds_res}

        # Build seat status list
        result = []
        for s in all_seats:
            seat_id = s['seat_id']
            if seat_id in booked_seat_ids:
                status = 'BOOKED'
            elif seat_id in holds_map:
                hold = holds_map[seat_id]
                if current_session_id and hold['session_id'] == current_session_id:
                    status = 'SELECTED'
                else:
                    status = 'HELD'
            else:
                status = 'AVAILABLE'

            s['status'] = status
            result.append(s)

        return result

    @staticmethod
    def get_all_admin(date_from=None, date_to=None, search_term=None, status=None, source=None):
        where_clauses = []
        params = []

        if date_from:
            where_clauses.append("DATE(b.created_at) >= ?")
            params.append(date_from)

        if date_to:
            where_clauses.append("DATE(b.created_at) <= ?")
            params.append(date_to)

        if status:
            where_clauses.append("b.booking_status = ?")
            params.append(status)

        if source:
            where_clauses.append("b.booking_source = ?")
            params.append(source)

        if search_term:
            where_clauses.append("(b.booking_ref LIKE ? OR b.customer_name LIKE ? OR b.customer_phone LIKE ?)")
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

        where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
            SELECT b.*, m.title as movie_title, h.name as hall_name, st.show_date, st.start_time,
                   p.payment_method
            FROM bookings b
            JOIN showtimes st ON b.showtime_id = st.id
            JOIN movies m ON st.movie_id = m.id
            JOIN halls h ON st.hall_id = h.id
            LEFT JOIN payments p ON p.booking_id = b.id
            {where_str}
            ORDER BY b.created_at DESC;
        """
        bookings = execute_query(query, tuple(params), fetchall=True)
        for bk in bookings:
            seats_query = """
                SELECT s.seat_number FROM booking_seats bs
                JOIN seats s ON bs.seat_id = s.id
                WHERE bs.booking_id = ? ORDER BY s.seat_number ASC;
            """
            seats_res = execute_query(seats_query, (bk['id'],), fetchall=True)
            bk['seats_str'] = ", ".join([s['seat_number'] for s in seats_res])
        return bookings

    @staticmethod
    def cancel_booking(booking_id, user_id=None):
        query = "UPDATE bookings SET booking_status = 'CANCELLED', payment_status = 'REFUNDED' WHERE id = ?;"
        return execute_query(query, (booking_id,), commit=True)
