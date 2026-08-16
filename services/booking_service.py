import random
import datetime
from database.db import get_db_connection, execute_query
from config import Config
from models.audit import AuditLog

def _format_sql(query, is_sqlite):
    if is_sqlite:
        query = query.replace("NOW()", "DATETIME('now', 'localtime')")
        query = query.replace("CURDATE()", "DATE('now', 'localtime')")
    else:
        query = query.replace("?", "%s")
    return query

class BookingService:
    @staticmethod
    def hold_seats(showtime_id, seat_ids, session_id):
        """
        Attempts to place a 5-minute temporary hold on selected seats for a given session.
        Prevents concurrency conflicts.
        """
        if not seat_ids:
            return {'success': False, 'message': 'No seats selected.'}

        conn = get_db_connection()
        is_sqlite = Config.DB_TYPE != 'mysql'
        cursor = conn.cursor()

        try:
            # 1. Verify showtime active
            cursor.execute(_format_sql("SELECT hall_id, is_active FROM showtimes WHERE id = ?;", is_sqlite), (showtime_id,))
            st = cursor.fetchone()
            if not st or (is_sqlite and not dict(st)['is_active']) or (not is_sqlite and not st['is_active']):
                return {'success': False, 'message': 'Showtime is invalid or inactive.'}

            hall_id = st['hall_id'] if not is_sqlite else dict(st)['hall_id']

            # 2. Check if all seats belong to this hall
            placeholders = ",".join(["?"] * len(seat_ids))
            query = f"SELECT id, seat_number FROM seats WHERE hall_id = ? AND id IN ({placeholders});"
            cursor.execute(_format_sql(query, is_sqlite), (hall_id, *seat_ids))
            valid_seats = cursor.fetchall()
            if len(valid_seats) != len(seat_ids):
                return {'success': False, 'message': 'One or more selected seats do not belong to this hall.'}

            seat_name_map = { (s['id'] if not is_sqlite else dict(s)['id']): (s['seat_number'] if not is_sqlite else dict(s)['seat_number']) for s in valid_seats }

            # 3. Check if seats are already booked
            booked_query = f"""
                SELECT bs.seat_id FROM booking_seats bs
                JOIN bookings b ON bs.booking_id = b.id
                WHERE b.showtime_id = ? AND b.booking_status != 'CANCELLED' AND bs.seat_id IN ({placeholders});
            """
            cursor.execute(_format_sql(booked_query, is_sqlite), (showtime_id, *seat_ids))
            already_booked = cursor.fetchall()
            if already_booked:
                conflict_id = already_booked[0]['seat_id'] if not is_sqlite else dict(already_booked[0])['seat_id']
                seat_num = seat_name_map.get(conflict_id, f"ID {conflict_id}")
                return {'success': False, 'message': f"Seat {seat_num} was just booked by another customer. Please select another seat."}

            # 4. Clean expired holds
            if is_sqlite:
                cursor.execute("DELETE FROM seat_holds WHERE expires_at <= DATETIME('now', 'localtime');")
            else:
                cursor.execute("DELETE FROM seat_holds WHERE expires_at <= NOW();")

            # 5. Check if held by another session
            held_query = f"""
                SELECT seat_id, session_id FROM seat_holds
                WHERE showtime_id = ? AND seat_id IN ({placeholders}) AND session_id != ?;
            """
            cursor.execute(_format_sql(held_query, is_sqlite), (showtime_id, *seat_ids, session_id))
            held_by_others = cursor.fetchall()
            if held_by_others:
                conflict_id = held_by_others[0]['seat_id'] if not is_sqlite else dict(held_by_others[0])['seat_id']
                seat_num = seat_name_map.get(conflict_id, f"ID {conflict_id}")
                return {'success': False, 'message': f"Seat {seat_num} is currently being reserved by another user. Please select another seat."}

            # 6. Refresh/Insert holds for this session
            expires_at = datetime.datetime.now() + datetime.timedelta(minutes=Config.SEAT_HOLD_DURATION_MINUTES)
            expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")

            for sid in seat_ids:
                if is_sqlite:
                    cursor.execute("""
                        INSERT INTO seat_holds (showtime_id, seat_id, session_id, expires_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(showtime_id, seat_id) DO UPDATE SET session_id = excluded.session_id, expires_at = excluded.expires_at;
                    """, (showtime_id, sid, session_id, expires_str))
                else:
                    cursor.execute("""
                        INSERT INTO seat_holds (showtime_id, seat_id, session_id, expires_at)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE session_id=VALUES(session_id), expires_at=VALUES(expires_at);
                    """, (showtime_id, sid, session_id, expires_str))

            conn.commit()
            return {'success': True, 'expires_at': expires_str, 'message': 'Seats held successfully.'}

        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Seat hold failed: {str(e)}'}
        finally:
            conn.close()

    @staticmethod
    def create_booking(showtime_id, seat_ids, session_id, customer_name, customer_email, customer_phone, payment_method, user_id=None, booking_source='ONLINE'):
        """
        Creates a confirmed booking with transactional seat verification.
        """
        if not seat_ids:
            return {'success': False, 'message': 'No seats selected.'}

        conn = get_db_connection()
        is_sqlite = Config.DB_TYPE != 'mysql'
        cursor = conn.cursor()

        try:
            # 1. Fetch seat details & prices
            placeholders = ",".join(["?"] * len(seat_ids))
            query = f"""
                SELECT s.id, s.seat_number, st.base_price_lkr
                FROM seats s
                JOIN seat_types st ON s.seat_type_id = st.id
                WHERE s.id IN ({placeholders});
            """
            cursor.execute(_format_sql(query, is_sqlite), tuple(seat_ids))
            seats_data = cursor.fetchall()
            if len(seats_data) != len(seat_ids):
                return {'success': False, 'message': 'Invalid seats selection.'}

            if is_sqlite:
                seats_data = [dict(s) for s in seats_data]

            # 2. Verify seats are still available
            booked_query = f"""
                SELECT bs.seat_id FROM booking_seats bs
                JOIN bookings b ON bs.booking_id = b.id
                WHERE b.showtime_id = ? AND b.booking_status != 'CANCELLED' AND bs.seat_id IN ({placeholders});
            """
            cursor.execute(_format_sql(booked_query, is_sqlite), (showtime_id, *seat_ids))
            booked = cursor.fetchall()
            if booked:
                conn.rollback()
                return {'success': False, 'message': 'One or more of your selected seats have already been booked.'}

            # 3. Calculate total
            seats_subtotal = sum(float(s['base_price_lkr']) for s in seats_data)
            booking_fee = 50.00 if booking_source == 'ONLINE' else 0.00
            total_amount = seats_subtotal + booking_fee

            # 4. Generate unique Booking Ref (e.g. CCX-20260814-98412)
            today_str = datetime.date.today().strftime("%Y%m%d")
            rand_suffix = random.randint(10000, 99999)
            booking_ref = f"CCX-{today_str}-{rand_suffix}"

            # 5. Insert Booking
            cursor.execute(_format_sql("""
                INSERT INTO bookings (booking_ref, user_id, showtime_id, total_amount_lkr, booking_status, payment_status, booking_source, customer_name, customer_email, customer_phone)
                VALUES (?, ?, ?, ?, 'CONFIRMED', 'PAID', ?, ?, ?, ?);
            """, is_sqlite), (booking_ref, user_id, showtime_id, total_amount, booking_source, customer_name, customer_email, customer_phone))

            booking_id = cursor.lastrowid

            # 6. Insert Booking Seats
            for s in seats_data:
                cursor.execute(_format_sql("""
                    INSERT INTO booking_seats (booking_id, seat_id, price_lkr)
                    VALUES (?, ?, ?);
                """, is_sqlite), (booking_id, s['id'], s['base_price_lkr']))

            # 7. Insert Payment Record
            trans_ref = f"PAY-{booking_ref}"
            cursor.execute(_format_sql("""
                INSERT INTO payments (booking_id, payment_method, transaction_ref, amount_lkr, payment_status)
                VALUES (?, ?, ?, ?, 'SUCCESS');
            """, is_sqlite), (booking_id, payment_method, trans_ref, total_amount))

            # 8. Release seat holds for this session/showtime
            del_query = f"DELETE FROM seat_holds WHERE showtime_id = ? AND (session_id = ? OR seat_id IN ({placeholders}));"
            cursor.execute(_format_sql(del_query, is_sqlite), (showtime_id, session_id, *seat_ids))

            conn.commit()

            AuditLog.log(user_id, "CREATED_BOOKING", f"Booking {booking_ref} created for {customer_name} ({len(seat_ids)} seats, Total: LKR {total_amount:.2f})")

            return {
                'success': True,
                'booking_id': booking_id,
                'booking_ref': booking_ref,
                'total_amount': total_amount,
                'message': 'Booking confirmed successfully.'
            }

        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Booking creation error: {str(e)}'}
        finally:
            conn.close()
