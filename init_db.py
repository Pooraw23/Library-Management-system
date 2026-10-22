import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load configuration from .env
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'library_db')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

DATABASE_URL = os.getenv('DATABASE_URL')
# Allow passing password or database URL via command line argument: python init_db.py <password_or_url>
if len(sys.argv) > 1:
    arg = sys.argv[1].strip()
    if arg.startswith('postgres://') or arg.startswith('postgresql://'):
        DATABASE_URL = arg
    else:
        DB_PASSWORD = arg

def init_database():
    print("=" * 60)
    print(" Smart Library Management System - PostgreSQL Setup Tool")
    print("=" * 60)

    # Cloud Database Branch: If DATABASE_URL is provided
    if DATABASE_URL:
        db_url = DATABASE_URL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        print("Connecting to Cloud PostgreSQL using DATABASE_URL...")
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            sql_path = os.path.join(os.path.dirname(__file__), 'sql', 'setup_database.sql')
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            cur.execute(sql_script)
            conn.commit()
            print("All tables, foreign keys, indexes, and sample seed data created successfully!")
            
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [r[0] for r in cur.fetchall()]
            print(f"\nVerified {len(tables)} tables created in Cloud PostgreSQL:")
            for t in tables:
                print(f"  [OK] {t}")
            cur.close()
            conn.close()
            print("\n" + "=" * 60)
            print("SUCCESS! Cloud PostgreSQL is fully initialized!")
            print("=" * 60)
            return
        except Exception as e:
            print(f"Error connecting to Cloud PostgreSQL: {e}")
            sys.exit(1)

    print(f"Connecting to PostgreSQL server at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")

    # Step 1: Connect to default postgres database to create library_db if not exists
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        print("Connected to PostgreSQL successfully!")
    except Exception as e:
        print("\nConnection failed!")
        print(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. If the error is 'password authentication failed':")
        print("   Run this script with your PostgreSQL password:")
        print(f"   python init_db.py your_actual_password")
        print("2. Or update DB_PASSWORD in your .env file and run 'python init_db.py'")
        sys.exit(1)

    # Check if database exists
    cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}';")
    exists = cur.fetchone()
    if not exists:
        print(f"Database '{DB_NAME}' does not exist. Creating it now...")
        cur.execute(f"CREATE DATABASE {DB_NAME};")
        print(f"Database '{DB_NAME}' created successfully!")
    else:
        print(f"Database '{DB_NAME}' already exists.")

    cur.close()
    conn.close()

    # Step 2: Connect to the library_db and execute setup_database.sql
    print(f"\nConnecting to '{DB_NAME}' to execute SQL schema and seed queries...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        cur = conn.cursor()

        sql_path = os.path.join(os.path.dirname(__file__), 'sql', 'setup_database.sql')
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        cur.execute(sql_script)
        conn.commit()
        print("All tables, foreign keys, indexes, and sample seed data created successfully!")

        # Verify tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [r[0] for r in cur.fetchall()]
        print(f"\nVerified {len(tables)} tables created in PostgreSQL:")
        for t in tables:
            print(f"  [OK] {t}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error executing SQL setup script: {e}")
        sys.exit(1)

    # Step 3: Update .env file to enable USE_DB=true
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()

        # Update USE_DB to true
        env_lines = env_content.splitlines()
        updated_lines = []
        for line in env_lines:
            if line.startswith('USE_DB='):
                updated_lines.append('USE_DB=true')
            elif line.startswith('DB_PASSWORD='):
                updated_lines.append(f'DB_PASSWORD={DB_PASSWORD}')
            else:
                updated_lines.append(line)

        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines) + '\n')

        print("\nUpdated .env configuration:")
        print("  [OK] Set USE_DB=true")
        print(f"  [OK] Set DB_PASSWORD={DB_PASSWORD}")
    except Exception as e:
        print(f"Could not automatically update .env: {e}")

    print("\n" + "=" * 60)
    print("SUCCESS! Your Smart Library App is now fully connected to PostgreSQL!")
    print("Run 'python app.py' to start the live PostgreSQL-connected app.")
    print("=" * 60)

if __name__ == '__main__':
    init_database()
