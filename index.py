import os
import sys

# Ensure root directory is in sys.path for Vercel serverless environment
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app
from database.db import init_db

# Initialize database schema if running in serverless container
try:
    init_db()
except Exception as e:
    print(f"[!] Serverless Init DB Error: {e}")

# Export for Vercel WSGI serverless runner
handler = app
app = app



