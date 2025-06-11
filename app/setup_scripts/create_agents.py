import psycopg
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection string from .env
DB_URI = os.getenv("DB_URI")

if not DB_URI:
    raise ValueError("❌ Database connection string (DB_URI) is not set in the .env file.")

def init_agent_db():
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    gender TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            conn.commit()
    print("✅ PostgreSQL agents table initialized.")

def insert_demo_agents():
    demo_agents = [
        ("Agent Smith", "smith@example.com", "female", "2025-01-10 08:30:00", "2025-06-06 12:00:00"),
        ("Agent James", "james@example.com", "male", "2025-02-15 09:45:00", "2025-06-07 14:20:00"),
        ("Agent Jack", "jack@example.com", None, "2025-03-20 11:00:00", "2025-06-07 15:15:00"),
    ]

    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            for name, email, gender, created_at, last_login in demo_agents:
                agent_id = uuid.uuid4()
                cur.execute("""
                    INSERT INTO agents (agent_id, name, email, gender, created_at, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                """, (agent_id, name, email, gender, created_at, last_login))
            conn.commit()
    print("✅ Demo agents inserted.")

def print_agents():
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agents")
            rows = cur.fetchall()
            for row in rows:
                print(row)

# Run all steps
if __name__ == "__main__":
    init_agent_db()
    insert_demo_agents()
    print_agents()
