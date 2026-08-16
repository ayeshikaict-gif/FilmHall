import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ceylon-cineplex-secret-key-2026-sl')
    
    # DB configuration: 'sqlite' or 'mysql'
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')
    
    # SQLite config
    base_sqlite_path = os.path.join(os.path.dirname(__file__), 'ceylon_cineplex.db')
    is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    
    if is_vercel:
        SQLITE_DB_PATH = '/tmp/ceylon_cineplex.db'
        if not os.path.exists(SQLITE_DB_PATH) and os.path.exists(base_sqlite_path):
            import shutil
            try:
                shutil.copy(base_sqlite_path, SQLITE_DB_PATH)
                try:
                    os.chmod(SQLITE_DB_PATH, 0o666)
                except Exception:
                    pass
            except Exception as e:
                print(f"[!] Warning copying DB to /tmp: {e}")
    else:
        SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', base_sqlite_path)
    
    # MySQL config
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'ceylon_cineplex_db')

    SEAT_HOLD_DURATION_MINUTES = 5
    CINEMA_NAME = "Ceylon Cineplex"
    CINEMA_TAGLINE = "Your Movie. Your Seat. Your Experience."
    CINEMA_ADDRESS = "No. 450, Galle Road, Colombo 03, Sri Lanka"
    CINEMA_PHONE = "+94 11 234 5678"
    CINEMA_EMAIL = "info@ceyloncineplex.lk"
