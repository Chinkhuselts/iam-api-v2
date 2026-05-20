import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time  # We need this to add a delay

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Establishes connection to PostgreSQL with a retry loop for Docker."""
    
    # 1. Catch missing environment variables instantly
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is missing. Check docker-compose.yml!")

    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return conn
        except psycopg2.OperationalError:
            print(f"Database not ready yet. Retrying in 2 seconds... ({retries} attempts left)")
            retries -= 1
            time.sleep(2)
            
    # If it fails 5 times, crash gracefully
    raise Exception("Could not connect to the database after multiple retries.")

def init_db():
    """Creates the tables and default roles using RAW SQL."""
    create_tables_query = """
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO roles (name) VALUES ('admin'), ('manager'), ('user')
    ON CONFLICT (name) DO NOTHING;
    """
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(create_tables_query)
        conn.commit() 
        print("✅ Database initialized and roles created successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    finally:
        cur.close()
        conn.close()
