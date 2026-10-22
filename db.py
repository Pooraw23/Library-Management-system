import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Establish and return a new connection to the PostgreSQL database
    using cloud DATABASE_URL or individual host parameters.
    """
    if Config.DATABASE_URL:
        return psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
    return psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for single or combined database operations.
    Automatically rolls back on exception and closes the cursor and connection.
    If commit=True, commits on clean exit.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        yield cur, conn
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error occurred: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

def execute_query(query, params=None, fetch=None, commit=False):
    """
    Utility helper to execute parameterized queries.
    fetch can be 'one', 'all', or None.
    """
    with get_db_cursor(commit=commit) as (cur, conn):
        cur.execute(query, params or ())
        if fetch == 'one':
            result = cur.fetchone()
            return dict(result) if result else None
        elif fetch == 'all':
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        return None
