from database.db import execute_query

class Payment:
    @staticmethod
    def create(booking_id, payment_method, transaction_ref, amount_lkr, payment_status='SUCCESS'):
        query = """
            INSERT INTO payments (booking_id, payment_method, transaction_ref, amount_lkr, payment_status)
            VALUES (?, ?, ?, ?, ?);
        """
        return execute_query(query, (booking_id, payment_method, transaction_ref, amount_lkr, payment_status), commit=True)
