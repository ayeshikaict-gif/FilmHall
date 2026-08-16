from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models.user import User
from models.audit import AuditLog

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Authentication required.", "warning")
                return redirect(url_for('auth.login'))
            user_role = session.get('user_role', 'CUSTOMER')
            if user_role not in allowed_roles and 'ADMIN' not in [user_role]:
                flash("Access denied: You do not have permission to view this page.", "danger")
                return redirect(url_for('customer.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

            user = User.get_by_email(email)
            if user and User.verify_password(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_email'] = user['email']
                session['user_role'] = user['role_name']

                try:
                    AuditLog.log(user['id'], "LOGIN", f"User {user['email']} logged in successfully.", request.remote_addr)
                except Exception:
                    pass

                flash(f"Welcome back, {user['full_name']}!", "success")

                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)

                if user['role_name'] == 'ADMIN':
                    return redirect(url_for('admin.dashboard'))
                elif user['role_name'] == 'CASHIER':
                    return redirect(url_for('cashier.dashboard'))
                else:
                    return redirect(url_for('customer.index'))
            else:
                flash("Invalid email address or password.", "danger")
        except Exception as e:
            print(f"[Login Error]: {e}")
            flash(f"Login failed: {str(e)}", "danger")

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template('auth/register.html')

            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template('auth/register.html')

            existing = User.get_by_email(email)
            if existing:
                flash("An account with this email address already exists.", "warning")
                return render_template('auth/register.html')

            user_id = User.create(full_name, email, phone, password, role_id=1)
            try:
                AuditLog.log(user_id, "REGISTER", f"New customer registration: {email}", request.remote_addr)
            except Exception:
                pass
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"[Register Error]: {e}")
            flash(f"Registration error: {str(e)}", "danger")

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        AuditLog.log(user_id, "LOGOUT", "User logged out", request.remote_addr)
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('customer.index'))
