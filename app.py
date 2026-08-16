from flask import Flask, render_template, session, request
from config import Config
from database.db import init_db

# Import Blueprints
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.cashier import cashier_bp
from routes.admin import admin_bp
from routes.api import api_bp

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY if (hasattr(Config, 'SECRET_KEY') and Config.SECRET_KEY and len(str(Config.SECRET_KEY).strip()) > 0) else 'ceylon-cineplex-secret-key-2026-sl-super-secret'
app.config['SECRET_KEY'] = app.secret_key


# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(cashier_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

@app.context_processor
def inject_global_vars():
    return {
        'cinema_name': Config.CINEMA_NAME,
        'cinema_tagline': Config.CINEMA_TAGLINE,
        'cinema_address': Config.CINEMA_ADDRESS,
        'cinema_phone': Config.CINEMA_PHONE,
        'user_name': session.get('user_name'),
        'user_role': session.get('user_role', 'GUEST')
    }

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    import traceback
    err_trace = traceback.format_exc()
    print(f"[500 Internal Error]: {err_trace}")
    return render_template('errors/500.html', error_detail=str(error), error_trace=err_trace), 500

if __name__ == '__main__':
    init_db()
    print("[+] Starting Ceylon Cineplex Server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
