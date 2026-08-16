from werkzeug.security import generate_password_hash, check_password_hash
from database.db import execute_query

class User:
    @staticmethod
    def get_by_id(user_id):
        query = """
            SELECT u.*, r.name as role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.id = ?;
        """
        return execute_query(query, (user_id,), fetchone=True)

    @staticmethod
    def get_by_email(email):
        query = """
            SELECT u.*, r.name as role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE LOWER(u.email) = LOWER(?);
        """
        return execute_query(query, (email,), fetchone=True)

    @staticmethod
    def create(full_name, email, phone, password, role_id=1):
        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO users (full_name, email, phone, password_hash, role_id)
            VALUES (?, ?, ?, ?, ?);
        """
        return execute_query(query, (full_name, email.lower(), phone, password_hash, role_id), commit=True)

    @staticmethod
    def verify_password(stored_hash, password):
        try:
            if not stored_hash or not password:
                return False
            if stored_hash == password:
                return True
            return check_password_hash(stored_hash, password)
        except Exception as e:
            print(f"[Password Verify Error]: {e}")
            return False

    @staticmethod
    def get_all():
        query = """
            SELECT u.id, u.full_name, u.email, u.phone, r.name as role_name, u.created_at
            FROM users u
            JOIN roles r ON u.role_id = r.id
            ORDER BY u.id ASC;
        """
        return execute_query(query, fetchall=True)

    @staticmethod
    def update_role(user_id, role_id):
        query = "UPDATE users SET role_id = ? WHERE id = ?;"
        return execute_query(query, (role_id, user_id), commit=True)

    @staticmethod
    def update_profile(user_id, full_name, phone):
        query = "UPDATE users SET full_name = ?, phone = ? WHERE id = ?;"
        return execute_query(query, (full_name, phone, user_id), commit=True)
