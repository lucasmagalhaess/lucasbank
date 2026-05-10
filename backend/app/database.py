import psycopg2
import os
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lucasbank:lucasbank@localhost:5437/lucasbank")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
