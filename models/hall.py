from database.db import execute_query

class Hall:
    @staticmethod
    def get_all():
        query = "SELECT * FROM halls WHERE is_active = 1 ORDER BY id ASC;"
        return execute_query(query, fetchall=True)

    @staticmethod
    def get_by_id(hall_id):
        query = "SELECT * FROM halls WHERE id = ?;"
        return execute_query(query, (hall_id,), fetchone=True)

    @staticmethod
    def get_seat_types():
        query = "SELECT * FROM seat_types ORDER BY id ASC;"
        return execute_query(query, fetchall=True)

    @staticmethod
    def update_seat_price(seat_type_id, base_price_lkr):
        query = "UPDATE seat_types SET base_price_lkr = ? WHERE id = ?;"
        return execute_query(query, (base_price_lkr, seat_type_id), commit=True)

    @staticmethod
    def get_seats_by_hall(hall_id):
        query = """
            SELECT s.*, st.name as seat_type_name, st.base_price_lkr, st.color_code
            FROM seats s
            JOIN seat_types st ON s.seat_type_id = st.id
            WHERE s.hall_id = ?
            ORDER BY s.row_label ASC, s.col_number ASC;
        """
        return execute_query(query, (hall_id,), fetchall=True)
