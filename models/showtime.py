from database.db import execute_query

class Showtime:
    @staticmethod
    def get_by_id(showtime_id):
        query = """
            SELECT st.*, m.title as movie_title, m.title_sinhala, m.poster_url, m.duration_mins,
                   m.language, m.age_rating, h.name as hall_name, h.hall_type
            FROM showtimes st
            JOIN movies m ON st.movie_id = m.id
            JOIN halls h ON st.hall_id = h.id
            WHERE st.id = ? AND st.is_active = 1;
        """
        return execute_query(query, (showtime_id,), fetchone=True)

    @staticmethod
    def sync_dynamic_showtimes():
        """
        Deactivates past showtimes (before today) and auto-populates active showtimes
        starting from TODAY through the next 7 days for active movies.
        """
        import datetime
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")

        # 1. Deactivate past showtimes
        try:
            execute_query("UPDATE showtimes SET is_active = 0 WHERE show_date < ? AND is_active = 1;", (today_str,), commit=True)
        except Exception as ex:
            print(f"[!] Warning deactivating past showtimes: {ex}")

        # 2. Ensure showtimes exist for today and the next 7 days
        try:
            movies = execute_query("SELECT id FROM movies WHERE status = 'NOW SHOWING' AND is_deleted = 0;", fetchall=True)
            if not movies:
                movies = execute_query("SELECT id FROM movies WHERE is_deleted = 0 LIMIT 5;", fetchall=True)
            
            halls = execute_query("SELECT id FROM halls WHERE is_active = 1;", fetchall=True)

            if not movies or not halls:
                return

            movie_ids = [m['id'] for m in movies]
            hall_ids = [h['id'] for h in halls]

            for day_offset in range(0, 7):
                target_date = today + datetime.timedelta(days=day_offset)
                date_str = target_date.strftime("%Y-%m-%d")

                res = execute_query(
                    "SELECT COUNT(*) as cnt FROM showtimes WHERE show_date = ? AND is_active = 1;",
                    (date_str,),
                    fetchone=True
                )
                count = res['cnt'] if res and isinstance(res, dict) else (res[0] if res else 0)

                if count == 0:
                    m1 = movie_ids[0]
                    m2 = movie_ids[1] if len(movie_ids) > 1 else movie_ids[0]
                    m3 = movie_ids[2] if len(movie_ids) > 2 else movie_ids[0]

                    h1 = hall_ids[0]
                    h2 = hall_ids[1] if len(hall_ids) > 1 else hall_ids[0]
                    h3 = hall_ids[2] if len(hall_ids) > 2 else hall_ids[0]

                    schedules = [
                        (m1, h1, date_str, "10:30:00", "13:00:00"),
                        (m1, h1, date_str, "18:30:00", "21:00:00"),
                        (m2, h2, date_str, "14:00:00", "16:30:00"),
                        (m3, h3, date_str, "18:30:00", "21:30:00"),
                        (m2, h2, date_str, "19:00:00", "22:00:00"),
                    ]
                    for s in schedules:
                        try:
                            execute_query(
                                "INSERT INTO showtimes (movie_id, hall_id, show_date, start_time, end_time, is_active) VALUES (?, ?, ?, ?, ?, 1);",
                                s,
                                commit=True
                            )
                        except Exception:
                            pass
        except Exception as e:
            print(f"[!] Error in sync_dynamic_showtimes: {e}")

    @staticmethod
    def get_by_movie(movie_id, from_date=None):
        Showtime.sync_dynamic_showtimes()
        import datetime
        if not from_date:
            from_date = datetime.date.today().strftime("%Y-%m-%d")

        query = """
            SELECT st.*, h.name as hall_name, h.hall_type
            FROM showtimes st
            JOIN halls h ON st.hall_id = h.id
            WHERE st.movie_id = ? AND st.is_active = 1 AND st.show_date >= ?
            ORDER BY st.show_date ASC, st.start_time ASC;
        """
        return execute_query(query, (movie_id, from_date), fetchall=True)

    @staticmethod
    def get_all(show_date=None, hall_id=None, include_past=False):
        Showtime.sync_dynamic_showtimes()
        import datetime
        where_clauses = ["st.is_active = 1"]
        params = []

        if show_date:
            where_clauses.append("st.show_date = ?")
            params.append(show_date)
        elif not include_past:
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            where_clauses.append("st.show_date >= ?")
            params.append(today_str)

        if hall_id:
            where_clauses.append("st.hall_id = ?")
            params.append(hall_id)

        where_str = " WHERE " + " AND ".join(where_clauses)

        query = f"""
            SELECT st.*, m.title as movie_title, m.poster_url, h.name as hall_name
            FROM showtimes st
            JOIN movies m ON st.movie_id = m.id
            JOIN halls h ON st.hall_id = h.id
            {where_str}
            ORDER BY st.show_date ASC, st.start_time ASC;
        """
        return execute_query(query, tuple(params), fetchall=True)

    @staticmethod
    def check_overlap(hall_id, show_date, start_time, end_time, exclude_id=None):
        """
        Checks if a proposed showtime overlaps with existing showtimes in the same hall.
        Overlap condition: (StartA < EndB) AND (EndA > StartB)
        """
        params = [hall_id, show_date, start_time, end_time]
        exclude_sql = ""
        if exclude_id:
            exclude_sql = " AND id != ?"
            params.append(exclude_id)

        query = f"""
            SELECT COUNT(*) as count FROM showtimes
            WHERE hall_id = ? AND show_date = ? AND is_active = 1
            AND NOT (end_time <= ? OR start_time >= ?){exclude_sql};
        """
        res = execute_query(query, tuple(params), fetchone=True)
        count = res['count'] if isinstance(res, dict) else (res[0] if res else 0)
        return count > 0

    @staticmethod
    def create(movie_id, hall_id, show_date, start_time, end_time):
        if Showtime.check_overlap(hall_id, show_date, start_time, end_time):
            raise ValueError("Showtime overlaps with another show in the same hall.")

        query = """
            INSERT INTO showtimes (movie_id, hall_id, show_date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?);
        """
        return execute_query(query, (movie_id, hall_id, show_date, start_time, end_time), commit=True)

    @staticmethod
    def update(showtime_id, movie_id, hall_id, show_date, start_time, end_time):
        if Showtime.check_overlap(hall_id, show_date, start_time, end_time, exclude_id=showtime_id):
            raise ValueError("Showtime overlaps with another show in the same hall.")

        query = """
            UPDATE showtimes SET
                movie_id = ?, hall_id = ?, show_date = ?, start_time = ?, end_time = ?
            WHERE id = ?;
        """
        return execute_query(query, (movie_id, hall_id, show_date, start_time, end_time, showtime_id), commit=True)

    @staticmethod
    def delete(showtime_id):
        query = "UPDATE showtimes SET is_active = 0 WHERE id = ?;"
        return execute_query(query, (showtime_id,), commit=True)
