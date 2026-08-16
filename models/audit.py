from database.db import execute_query

class AuditLog:
    @staticmethod
    def log(user_id, action, details=None, ip_address=None):
        query = """
            INSERT INTO audit_logs (user_id, action, details, ip_address)
            VALUES (?, ?, ?, ?);
        """
        try:
            execute_query(query, (user_id, action, details, ip_address), commit=True)
        except Exception as e:
            print(f"[Audit Log Error]: {e}")

    @staticmethod
    def get_recent(limit=100):
        query = """
            SELECT a.*, u.full_name, u.email, r.name as role_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY a.created_at DESC
            LIMIT ?;
        """
        return execute_query(query, (limit,), fetchall=True)
