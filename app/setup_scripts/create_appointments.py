import psycopg
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection string from .env
DB_URI = os.getenv("DB_URI")

if not DB_URI:
    raise ValueError("❌ Database connection string (DB_URI) is not set in the .env file.")

# -----------------------------------------
# Step 1: Initialize Unified Appointment DB
# -----------------------------------------
def init_db():
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id SERIAL PRIMARY KEY,
                    agent_id UUID NOT NULL,
                    customer_id UUID,  -- NULL if not booked
                    date DATE NOT NULL,
                    time_slot TIME NOT NULL,
                    booked BOOLEAN DEFAULT FALSE,
                    mode VARCHAR(50),  -- NULL if not booked
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(agent_id, date, time_slot)
                )
            """)
            conn.commit()
    print("✅ Appointments table initialized.")

# -----------------------------------------
# Step 2: Populate Available Time Slots
# -----------------------------------------
def populate_time_slots_for_agent(agent_id, start_date, days=1):
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

            for day_offset in range(days):
                day = (start_dt + timedelta(days=day_offset)).date()
                slot_time = datetime.strptime("00:00", "%H:%M")
                for _ in range(48):  # 48 half-hour slots per day
                    time_slot = slot_time.time()
                    try:
                        cur.execute("""
                            INSERT INTO appointments (agent_id, date, time_slot)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (agent_id, date, time_slot) DO NOTHING
                        """, (agent_id, day, time_slot))
                    except Exception as e:
                        print("⚠️ Error inserting slot:", e)
                    slot_time += timedelta(minutes=30)

            conn.commit()
    print(f"✅ Time slots populated for agent {agent_id} on {start_date} + {days} days.")

# -----------------------------------------
# Step 3: View Available Slots
# -----------------------------------------
def get_slots(agent_id, date_str):
    with psycopg.connect(DB_CONN_STR) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT time_slot FROM appointments
                WHERE agent_id = %s AND date = %s AND booked = FALSE
                ORDER BY time_slot
            """, (agent_id, date_str))
            return [row[0].strftime("%H:%M") for row in cur.fetchall()]

# -----------------------------------------
# Step 4: Setup for All 3 Agents
# -----------------------------------------
AGENTS = [
    "8f35e0bf-8991-4246-98d7-5831e5a816d8",
    "c02b4eda-1f51-440d-ad0f-7b5cb9584726",
    "b15bb78b-e79f-4c03-9374-d162b5e1bcf1"
]

if __name__ == "__main__":
    init_db()
    for agent_id in AGENTS:
        populate_time_slots_for_agent(agent_id, "2025-06-09", days=1)
        slots = get_slots(agent_id, "2025-06-09")
        print(f"\n🗓️ Available slots for agent {agent_id} on 2025-06-09:")
        print(slots)