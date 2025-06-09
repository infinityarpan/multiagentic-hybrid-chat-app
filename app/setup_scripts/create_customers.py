import psycopg
import uuid
from datetime import datetime
import os

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection string from .env
DB_URI = os.getenv("DB_URI")

if not DB_URI:
    raise ValueError("❌ Database connection string (DB_URI) is not set in the .env file.")

def init_customer_db():
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    custom_id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    gender TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            conn.commit()
    print("✅ PostgreSQL DB and table initialized.")


def insert_demo_customers():
    demo_customers = [
        ("Alice Johnson", "alice@example.com", "female", "2025-01-10 08:30:00", "2025-06-06 12:00:00"),
        ("Bob Smith", "bob@example.com", "male", "2025-02-15 09:45:00", "2025-06-07 14:20:00"),
        ("Charlie Lee", "charlie@example.com", None, "2025-03-20 11:00:00", "2025-06-07 15:15:00"),
    ]

    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            for name, email, gender, created_at, last_login in demo_customers:
                custom_id = uuid.uuid4()
                cur.execute("""
                    INSERT INTO customers (custom_id, name, email, gender, created_at, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                """, (custom_id, name, email, gender, created_at, last_login))
            conn.commit()
    print("✅ Demo customers inserted.")


def print_customers():
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM customers")
            rows = cur.fetchall()
            for row in rows:
                print(row)


# Main execution
if __name__ == "__main__":
    init_customer_db()
    insert_demo_customers()
    print_customers()
