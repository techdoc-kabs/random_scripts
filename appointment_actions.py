
import sqlite3

import pandas as pd
import json
from datetime import datetime
import streamlit as st

DB_PATH = "users_db.db"

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_action_id(action_type):
    today = datetime.now().strftime("%Y%m%d")
    prefix = action_type.upper().replace(" ", "_")
    conn = create_connection()
    cursor = conn.cursor()
    like_pattern = f"{prefix}-{today}-%"
    try:
        cursor.execute(f"""
            SELECT action_id FROM {prefix.lower()}
            WHERE action_id LIKE ? ORDER BY action_id DESC LIMIT 1
        """, (like_pattern,))
        result = cursor.fetchone()
        if result:
            last_num = int(result[0].split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1
    except:
        new_num = 1
    conn.close()
    return f"{prefix}-{today}-{new_num:04d}"

def create_action_table_if_needed(action_type):
    conn = create_connection()
    cursor = conn.cursor()
    table_name = action_type.lower().replace(" ", "_")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            action_id TEXT PRIMARY KEY,
            appointment_id TEXT,
            user_id TEXT,
            client_name TEXT,
            client_type TEXT,
            action_type TEXT,
            appointment_type TEXT,
            assigned_to TEXT,
            scheduled_for TEXT,
            status TEXT,
            class TEXT,
            stream TEXT,
            term TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def extract_and_fill_actions():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments")
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    conn.close()

    df = pd.DataFrame(rows, columns=colnames)
    if df.empty:
        return {}

    action_dfs = {}

    for idx, row in df.iterrows():
        appointment_id = row["appointment_id"]
        user_id = row["user_id"]
        client_name = row['name']
        created_by = row["created_by"]
        client_type = row['client_type']
        appointment_type = row["appointment_type"]
        student_class = row.get("class", None)
        student_stream = row.get("stream", None)
        term = row.get("term", None)

        # Load JSON fields
        try:
            statuses = json.loads(row["statuses"])
            responsible = json.loads(row["responsible"])
            action_dates = json.loads(row["action_dates"])
        except Exception as e:
            st.error(f"Error parsing JSON for appointment {appointment_id}: {e}")
            continue

        for action, status in statuses.items():
            if status.lower() != "pending":
                continue  # Only insert pending actions

            action_table = action.lower().replace(" ", "_")
            create_action_table_if_needed(action)

            scheduled_for = action_dates.get(action)
            assigned_to = responsible.get(action)

            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 1 FROM {action_table}
                WHERE appointment_id = ? AND user_id = ? AND action_type = ?
            """, (appointment_id, user_id, action))
            exists = cursor.fetchone()

            if not exists:
                action_id = generate_action_id(action)
                cursor.execute(f"""
                    INSERT INTO {action_table} (
                        action_id, appointment_id, user_id, client_name, client_type,
                        action_type, appointment_type, assigned_to, scheduled_for,
                        status, class, stream, term, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    action_id, appointment_id, user_id, client_name, client_type,
                    action, appointment_type, assigned_to, scheduled_for,
                    status, student_class, student_stream, term, created_by
                ))
                conn.commit()
            conn.close()

    unique_actions = list(set([a for acts in df["statuses"] for a in json.loads(acts).keys()]))
    for action in unique_actions:
        table_name = action.lower().replace(" ", "_")
        conn = create_connection()
        try:
            action_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        except Exception as e:
            st.warning(f"Could not read table {table_name}: {e}")
            conn.close()
            continue
        conn.close()

        def compute_remaining(scheduled_str):
            try:
                scheduled_dt = datetime.strptime(scheduled_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                delta = scheduled_dt - now
                if delta.total_seconds() < 0:
                    return "Overdue"
                days = delta.days
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                return f"{days}d {hours}h {minutes}m"
            except:
                return "Invalid"

        if not action_df.empty and "scheduled_for" in action_df.columns:
            action_df["remaining_time"] = action_df["scheduled_for"].apply(compute_remaining)
        action_dfs[action] = action_df

    return action_dfs


def initialize_session_vars():
    defaults = {
        'action_id': None,
        'appointment_id': None,
        'user_id': None,
        'client_name': "",
        'client_type': "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# def main():
#     # initialize_session_vars()
#     st.title("📋 Appointment Actions Summary")
#     action_tables = extract_and_fill_actions()
#     if not action_tables:
#         st.info("No appointment actions found.")
#     for action, df in action_tables.items():
#         st.subheader(f"{action.title()} Actions")
#         st.dataframe(df)

# if __name__ == "__main__":
#     main()
def main():
    initialize_session_vars()
    st.title("📋 Appointment Actions Summary")
    action_tables = extract_and_fill_actions()
    
    if not action_tables:
        st.info("No appointment actions found.")
        return

    for action, df in action_tables.items():
        create_action_table_if_needed(action)
        st.subheader(f"{action.title()} Actions")
        
        if df.empty:
            st.info("No data for this action.")
            continue
        
        selected_index = st.selectbox(
            f"Select a row from {action.title()}",
            options=df.index,
            format_func=lambda i: f"{df.loc[i, 'action_id']} ({df.loc[i, 'client_name']})",
            key=f"select_{action}"
        )
        
        if selected_index is not None:
            selected_row = df.loc[selected_index]
            st.session_state.action_id = selected_row['action_id']
            st.session_state.appointment_id = selected_row['appointment_id']
            st.session_state.user_id = selected_row['user_id']
            st.session_state.client_name = selected_row['client_name']
            st.session_state.client_type = selected_row['client_type']

            st.success(f"✅ Stored in session: {st.session_state.action_id} {st.session_state.appointment_id} { st.session_state.user_id}")

        st.dataframe(df)
if __name__ == "__main__":
    main()