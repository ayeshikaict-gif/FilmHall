from database.db import execute_query

class Movie:
    @staticmethod
    def get_all(include_deleted=False, status=None, language=None, genre=None, search_term=None, limit=None):
        where_clauses = []
        params = []

        if not include_deleted:
            where_clauses.append("is_deleted = 0")

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        if language:
            where_clauses.append("LOWER(language) = LOWER(?)")
            params.append(language)

        if genre:
            where_clauses.append("LOWER(genre) LIKE LOWER(?)")
            params.append(f"%{genre}%")

        if search_term:
            where_clauses.append("(LOWER(title) LIKE LOWER(?) OR LOWER(title_sinhala) LIKE LOWER(?) OR LOWER(cast) LIKE LOWER(?))")
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

        where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        limit_str = f" LIMIT {limit}" if limit else ""

        query = f"SELECT * FROM movies{where_str} ORDER BY release_date DESC{limit_str};"
        return execute_query(query, tuple(params), fetchall=True)

    @staticmethod
    def get_by_id(movie_id):
        query = "SELECT * FROM movies WHERE id = ? AND is_deleted = 0;"
        return execute_query(query, (movie_id,), fetchone=True)

    @staticmethod
    def create(title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status):
        query = """
            INSERT INTO movies (title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        return execute_query(query, (title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status), commit=True)

    @staticmethod
    def update(movie_id, title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status):
        query = """
            UPDATE movies SET
                title = ?, title_sinhala = ?, poster_url = ?, backdrop_url = ?,
                description = ?, genre = ?, duration_mins = ?, language = ?,
                country = ?, release_date = ?, age_rating = ?, director = ?,
                cast = ?, trailer_url = ?, status = ?
            WHERE id = ?;
        """
        return execute_query(query, (title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status, movie_id), commit=True)

    @staticmethod
    def soft_delete(movie_id):
        query = "UPDATE movies SET is_deleted = 1 WHERE id = ?;"
        return execute_query(query, (movie_id,), commit=True)

    @staticmethod
    def get_sinhala_movies():
        return Movie.get_all(language='Sinhala', status='NOW SHOWING')

    @staticmethod
    def get_international_movies():
        query = "SELECT * FROM movies WHERE is_deleted = 0 AND LOWER(language) != 'sinhala' AND status = 'NOW SHOWING' ORDER BY release_date DESC;"
        return execute_query(query, fetchall=True)
