DB_PATH = "users_db.db"
import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
, os, base64
import time


def set_full_page_background(image_path):
    try:
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found.")
            return

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        st.markdown(
            f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Error setting background: {e}")

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
      # <-- add this line!
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


def fetch_follow_ups_for_assigned(db, assigned_to: str):
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM follow_ps
        WHERE assigned_to LIKE ?
        ORDER BY follow_up_date ASC
    """, (f"%{assigned_to}%",))
    return cursor.fetchall()


def load_follow_ups_for_user(db, assigned_to):
    rows = fetch_follow_ups_for_assigned(db, assigned_to)
    if rows:
        df = pd.DataFrame([dict(row) for row in rows])
    else:
        df = pd.DataFrame()
    return df


def toggle_follow_up_status(db, follow_up_id: int, current_status: str):
    try:
        cursor = db.cursor()
        new_status = 'pending' if current_status == 'done' else 'done'
        done_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == 'done' else None
        cursor.execute("""
            UPDATE follow_ps
            SET status = ?, done_at = ?
            WHERE id = ?
        """, (new_status, done_at, follow_up_id))
        db.commit()
        return {"success": True, "new_status": new_status}
    except Exception as e:
        return {"success": False, "message": str(e)}

def main():
    set_full_page_background('images/black_strip.jpg')
    db = create_connection()
    create_follow_ps_table(db)
    username = st.session_state.get("user_name")
    if not username:
        st.error("User not logged in.")
        st.stop()
    st.markdown("""
        <style>
        .header-row {
            background-color: #1565c0;
            color: white;
            padding: 10px;
            font-weight: bold;
            border-radius: 5px;
            margin-top: 15px;
        }
        .data-row {
            padding: 10px;
            border-radius: 5px;
        }
        .row-even {
            background-color: #2c2c2c;
        }
        .row-odd {
            background-color: #1e1e1e;
        }
        .status-pending {
            color: #e67e22;
            font-weight: bold;
        }
        .status-done {
            color: #27ae60;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)
    df = load_follow_ups_for_user(db, username)
    if df.empty:
        st.info("✅ You have no follow-ups.")
        return
    status_filter = st.sidebar.selectbox("🔎 Filter by Status", ["All", "Pending", "Completed"], index=0)
    header = st.columns([1.6, 1.3, 1.2, 1.8, 0.8, 0.8])
    header[0].markdown("<div class='header-row'>Client</div>", unsafe_allow_html=True)
    header[1].markdown("<div class='header-row'>Reason</div>", unsafe_allow_html=True)
    header[2].markdown("<div class='header-row'>Due Date</div>", unsafe_allow_html=True)
    header[3].markdown("<div class='header-row'>Time Left</div>", unsafe_allow_html=True)
    header[4].markdown("<div class='header-row'>Status</div>", unsafe_allow_html=True)
    header[5].markdown("<div class='header-row'>Action</div>", unsafe_allow_html=True)
    count = 0
    for idx, row in df.iterrows():
        is_done = row["status"] == "done"
        if status_filter == "Pending" and is_done:
            continue
        if status_filter == "Completed" and not is_done:
            continue
        row_class = "row-even" if count % 2 == 0 else "row-odd"
        status_tag = '<span class="status-done">Done</span>' if is_done else '<span class="status-pending">Pending</span>'
        count += 1
        cols = st.columns([1.8, 1.4, 1.2, 2, 1, 0.85])
        with cols[0]:
            st.markdown(f"<div class='data-row {row_class}' style='color:#ecf0f1;'>{row['full_name']}</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"<div class='data-row {row_class}' style='color:#ecf0f1;'>{row['reason']}</div>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<div class='data-row {row_class}' style='color:#dcdde1;'>{row['follow_up_date']}</div>", unsafe_allow_html=True)
        with cols[3]:
            if row["status"] == "done":
                display_time = f"{row['done_at']}✅" if row["done_at"] else "Done"
            else:
                due_date = datetime.strptime(row['follow_up_date'], "%Y-%m-%d").date()
                days_left = (due_date - datetime.now().date()).days
                if days_left >= 0:
                    display_time = f"{days_left} day(s) remaining"
                else:
                    display_time = f"Overdue by {-days_left} day(s)"
            st.markdown(f"<div class='data-row {row_class}' style='color:#bdc3c7;'>{display_time}</div>", unsafe_allow_html=True)

        with cols[4]:
            st.markdown(f"<div class='data-row {row_class}'>{status_tag}</div>", unsafe_allow_html=True)
        with cols[5]:
            btn_label = "✅" if not is_done else "🔁"
            if st.button(btn_label, key=f"toggle_{row['id']}"):
                result = toggle_follow_up_status(db, row['id'], row['status'])
                if result["success"]:
                    st.success(f"{result['new_status']}")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Error: {result['message']}")

    st.info(f"Showing **{count}** follow-up(s) under **{status_filter}**")
    db.close()

if __name__ == "__main__":
    main()