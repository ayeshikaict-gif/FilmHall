import os
import sqlite3
import pymysql
import datetime
from config import Config

def _create_raw_connection():
    """Creates a direct database connection without auto-init checks."""
    if Config.DB_TYPE == 'mysql':
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    else:
        # SQLite
        db_path = Config.SQLITE_DB_PATH
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        # Copy initial seed database if target DB doesn't exist or is 0 bytes
        base_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ceylon_cineplex.db')
        if db_path != base_db and (not os.path.exists(db_path) or os.path.getsize(db_path) == 0):
            if os.path.exists(base_db) and os.path.getsize(base_db) > 0:
                import shutil
                try:
                    shutil.copy(base_db, db_path)
                    try:
                        os.chmod(db_path, 0o666)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"[!] Warning copying base DB: {e}")

        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def get_db_connection():
    """Establishes database connection based on DB_TYPE in config, auto-initializing if empty."""
    conn = _create_raw_connection()
    is_sqlite = Config.DB_TYPE != 'mysql'

    if is_sqlite:
        # Auto-initialize database tables if movies table does not exist
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies';")
            if not cur.fetchone():
                init_db(conn=conn)
        except Exception as ex:
            print(f"[!] SQLite schema check error: {ex}")

    return conn

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """Executes a SQL query abstraction supporting both SQLite and MySQL."""
    conn = get_db_connection()
    is_sqlite = Config.DB_TYPE != 'mysql'

    # Replace MySQL syntax with SQLite equivalents if running SQLite
    if is_sqlite:
        query = query.replace("AUTO_INCREMENT", "AUTOINCREMENT")
        query = query.replace("INT PRIMARY KEY AUTOINCREMENT", "INTEGER PRIMARY KEY AUTOINCREMENT")
        query = query.replace("ON DUPLICATE KEY UPDATE name=VALUES(name)", "ON CONFLICT(name) DO UPDATE SET name=excluded.name")
        query = query.replace("NOW()", "DATETIME('now', 'localtime')")
        query = query.replace("CURDATE()", "DATE('now', 'localtime')")
    else:
        # Convert ? placeholders to %s for PyMySQL
        query = query.replace("?", "%s")

    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()

        if fetchone:
            res = cursor.fetchone()
            if res and is_sqlite:
                res = dict(res)
            return res
        if fetchall:
            res = cursor.fetchall()
            if res and is_sqlite:
                res = [dict(r) for r in res]
            return res

        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        return last_id or row_count
    except Exception as e:
        if commit:
            conn.rollback()
        raise e
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def init_db(conn=None):
    """Initializes schema, seeds database if missing, and generates seat maps & showtimes."""
    print(f"[*] Initializing Database ({Config.DB_TYPE.upper()})...")
    created_conn = False
    if conn is None:
        conn = _create_raw_connection()
        created_conn = True

    is_sqlite = Config.DB_TYPE != 'mysql'
    cursor = conn.cursor()

    try:
        # Read schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                raw_sql = f.read()

            # Remove single line comments
            clean_lines = []
            for line in raw_sql.splitlines():
                line_str = line.split('--')[0].strip()
                if line_str:
                    clean_lines.append(line_str)
            
            clean_sql = " ".join(clean_lines)

            if is_sqlite:
                clean_sql = clean_sql.replace("INT PRIMARY KEY AUTO_INCREMENT", "INTEGER PRIMARY KEY AUTOINCREMENT")
                clean_sql = clean_sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")
                clean_sql = clean_sql.replace("TINYINT(1)", "INTEGER")

            statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
            for stmt in statements:
                try:
                    cursor.execute(stmt)
                except Exception as ex:
                    print(f"[Schema Exec Warning]: {ex}")

        conn.commit()

        # Read and run seed.sql if tables are empty
        cursor.execute("SELECT COUNT(*) as cnt FROM users;")
        res = cursor.fetchone()
        user_count = res['cnt'] if isinstance(res, dict) else (res[0] if res else 0)

        if user_count == 0:
            print("[*] Seeding database with initial data...")
            seed_path = os.path.join(os.path.dirname(__file__), 'seed.sql')
            if os.path.exists(seed_path):
                with open(seed_path, 'r', encoding='utf-8') as f:
                    raw_seed = f.read()
                
                clean_seed_lines = []
                for line in raw_seed.splitlines():
                    line_str = line.split('--')[0].strip()
                    if line_str:
                        clean_seed_lines.append(line_str)
                
                clean_seed = " ".join(clean_seed_lines)
                statements = [s.strip() for s in clean_seed.split(';') if s.strip()]
                for stmt in statements:
                    if is_sqlite:
                        stmt = stmt.replace("ON DUPLICATE KEY UPDATE name=VALUES(name)", "")
                    try:
                        cursor.execute(stmt)
                    except Exception as ex:
                        print(f"[Seed Warning]: {ex} | Statement: {stmt[:60]}")
                conn.commit()

        # Seed Seats for Halls if not present
        cursor.execute("SELECT COUNT(*) as cnt FROM seats;")
        seat_res = cursor.fetchone()
        seat_count = seat_res['cnt'] if isinstance(seat_res, dict) else (seat_res[0] if seat_res else 0)

        if seat_count == 0:
            print("[*] Generating interactive seat maps for Cinema Halls...")
            # Hall 01: 10 rows (A-J) x 12 cols (120 seats)
            _generate_hall_seats(cursor, hall_id=1, rows=['A','B','C','D','E','F','G','H','I','J'], cols=12,
                                 row_types={'A':1,'B':1,'C':1,'D':1,'E':1,'F':1,'G':1,'H':2,'I':2,'J':3}, is_sqlite=is_sqlite)
            # Hall 02: 8 rows (A-H) x 10 cols (80 seats)
            _generate_hall_seats(cursor, hall_id=2, rows=['A','B','C','D','E','F','G','H'], cols=10,
                                 row_types={'A':1,'B':1,'C':1,'D':1,'E':1,'F':2,'G':2,'H':3}, is_sqlite=is_sqlite)
            # Hall 03: 5 rows (A-E) x 10 cols (50 seats)
            _generate_hall_seats(cursor, hall_id=3, rows=['A','B','C','D','E'], cols=10,
                                 row_types={'A':2,'B':2,'C':3,'D':3,'E':3}, is_sqlite=is_sqlite)
            conn.commit()

        # Auto-generate active showtimes for today and upcoming 7 days if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM showtimes;")
        st_res = cursor.fetchone()
        st_count = st_res['cnt'] if isinstance(st_res, dict) else (st_res[0] if st_res else 0)

        if st_count == 0:
            print("[*] Generating active showtimes schedule...")
            _generate_default_showtimes(cursor, is_sqlite=is_sqlite)
            conn.commit()

        print("[+] Database Initialization Complete.")
    except Exception as e:
        print(f"[!] Database Init Error: {e}")
        conn.rollback()
    finally:
        if created_conn:
            conn.close()

def _generate_hall_seats(cursor, hall_id, rows, cols, row_types, is_sqlite=True):
    ph = "?" if is_sqlite else "%s"
    for r in rows:
        seat_type_id = row_types.get(r, 1)
        for c in range(1, cols + 1):
            seat_num = f"{r}{c}"
            cursor.execute(
                f"INSERT INTO seats (hall_id, seat_number, row_label, col_number, seat_type_id) VALUES ({ph}, {ph}, {ph}, {ph}, {ph});",
                (hall_id, seat_num, r, c, seat_type_id)
            )

def _generate_default_showtimes(cursor, is_sqlite=True):
    today = datetime.date.today()
    ph = "?" if is_sqlite else "%s"
    insert_sql = f"INSERT INTO showtimes (movie_id, hall_id, show_date, start_time, end_time, is_active) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, 1)"

    for day_offset in range(0, 7):
        show_date = today + datetime.timedelta(days=day_offset)
        date_str = show_date.strftime("%Y-%m-%d")
        cursor.execute(insert_sql, (1, 1, date_str, "10:30:00", "13:00:00"))
        cursor.execute(insert_sql, (1, 1, date_str, "18:30:00", "21:00:00"))
        cursor.execute(insert_sql, (2, 2, date_str, "14:00:00", "16:30:00"))
        cursor.execute(insert_sql, (4, 3, date_str, "18:30:00", "21:30:00"))
        cursor.execute(insert_sql, (6, 2, date_str, "19:00:00", "22:00:00"))
