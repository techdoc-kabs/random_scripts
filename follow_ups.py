DB_PATH = "users_db.db"
import sqlite3

from datetime import datetime

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_follow_ps_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS follow_ps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            full_name TEXT,
            appointment_id TEXT,
            follow_up_date TEXT,
            reason TEXT,
            assigned_to TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            done_at TEXT,
            remaining_time TEXT
        )
    """)
    db.commit()


def insert_follow_up(
    db,
    user_id: str,
    full_name: str,
    appointment_id: str,
    follow_up_date,  # datetime.date
    reason: str,
    assigned_to: str
):
    try:
        cursor = db.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        follow_up_date_str = follow_up_date.strftime("%Y-%m-%d")
        days_remaining = (follow_up_date - datetime.now().date()).days
        remaining_time = f"{days_remaining} days remaining" if days_remaining >= 0 else f"Overdue by {-days_remaining} days"

        cursor.execute("""
            INSERT INTO follow_ps (
                user_id, full_name, appointment_id, follow_up_date,
                reason, assigned_to, status, created_at, remaining_time
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (
            user_id, full_name, appointment_id, follow_up_date_str,
            reason, assigned_to, created_at, remaining_time
        ))
        db.commit()
        return {"success": True, "message": "Follow-up recorded"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def mark_follow_up_done(db, follow_up_id: int):
    try:
        cursor = db.cursor()
        done_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE follow_ps
            SET status = 'done', done_at = ?
            WHERE id = ?
        """, (done_at, follow_up_id))
        db.commit()
        return {"success": True, "message": "Marked as done"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def fetch_user_follow_ups(db, user_id: str):
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM follow_ps
        WHERE user_id = ?
        ORDER BY follow_up_date ASC
    """, (user_id,))
    return cursor.fetchall()
