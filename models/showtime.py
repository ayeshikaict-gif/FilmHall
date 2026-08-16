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
    def get_by_movie(movie_id, from_date=None):
        params = [movie_id]
        date_filter = " AND st.show_date >= CURDATE()"
        if from_date:
            date_filter = " AND st.show_date >= ?"
            params.append(from_date)

        query = f"""
            SELECT st.*, h.name as hall_name, h.hall_type
            FROM showtimes st
            JOIN halls h ON st.hall_id = h.id
            WHERE st.movie_id = ? AND st.is_active = 1{date_filter}
            ORDER BY st.show_date ASC, st.start_time ASC;
        """
        return execute_query(query, tuple(params), fetchall=True)

    @staticmethod
    def get_all(show_date=None, hall_id=None):
        where_clauses = ["st.is_active = 1"]
        params = []

        if show_date:
            where_clauses.append("st.show_date = ?")
            params.append(show_date)

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
