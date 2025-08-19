import sqlite3

import streamlit as st
import pandas as pd
from datetime import datetime
import os, base64
import json
DB_PATH = "users_db.db"

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def set_full_page_background(image_path):
    try:
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found.")
            return

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        st.markdown(f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error setting background: {e}")



def get_available_therapists():
    conn = create_connection()
    therapists = pd.read_sql("SELECT DISTINCT full_name FROM users WHERE role = 'Therapist'", conn)['full_name'].tolist()
    conn.close()
    return therapists


def fetch_appointments_for_assignment(client_type, selected_action):
    conn = create_connection()
    query = """
    SELECT appointment_id, name, class, stream, term, assigned_therapist, actions
    FROM appointments
    WHERE client_type = ?
    """
    df = pd.read_sql(query, conn, params=(client_type,))
    conn.close()

    st.write("Raw actions data sample:", df['actions'].head().tolist())

    def has_action_true(actions_json):
        try:
            actions = json.loads(actions_json) if isinstance(actions_json, str) else actions_json
            return actions.get(selected_action.lower(), False) is True
        except Exception as e:
            st.warning(f"Failed to parse actions JSON: {e}")
            return False

    filtered_df = df[df['actions'].apply(has_action_true)]

    filtered_df = filtered_df[
        filtered_df['assigned_therapist'].isnull() |
        (filtered_df['assigned_therapist'] == '') |
        (filtered_df['assigned_therapist'] == 'Not assigned')
    ]

    return filtered_df



def ensure_columns_exist():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN assigned_therapist TEXT DEFAULT 'Not assigned'")
    except sqlite3.OperationalError:
        pass 
    
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN assigned_date TEXT")  # Store as ISO string
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN to_do_date TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def get_all_action_types():
    conn = create_connection()
    df = pd.read_sql("SELECT actions FROM appointments WHERE actions IS NOT NULL", conn)
    conn.close()

    action_set = set()
    for actions_json in df['actions']:
        try:
            actions = json.loads(actions_json)
            action_set.update(actions.keys())
        except:
            continue
    return sorted(action_set)

def ensure_assigned_therapist_column():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN assigned_therapist TEXT DEFAULT 'Not assigned'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.close()

def assign_clients_to_therapist(appointment_id, therapist_name, to_do_date):
    assigned_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments
        SET assigned_therapist = ?, assigned_date = ?, to_do_date = ?
        WHERE appointment_id = ?
    """, (therapist_name, assigned_date, to_do_date, appointment_id))
    conn.commit()
    conn.close()

from datetime import datetime, timedelta

def compute_time_info(row):
    try:
        due_date = datetime.strptime(str(row['to_do_date']), "%Y-%m-%d")
        now = datetime.now()
        delta = due_date - now
        if delta.total_seconds() > 0:
            return str(delta).split('.')[0], "-"
        else:
            wait_time = now - due_date
            return "⏰ Overdue", str(wait_time).split('.')[0]
    except:
        return "-", "-"


from datetime import datetime, timedelta
def fetch_appointments_for_assignment(client_type, selected_action):
    conn = create_connection()
    query = """
        SELECT appointment_id, name, class, stream, term, assigned_therapist, actions
        FROM appointments
        WHERE client_type = ?
    """
    df = pd.read_sql(query, conn, params=(client_type,))
    conn.close()

    def has_action_true(actions_json):
        try:
            actions = json.loads(actions_json) if isinstance(actions_json, str) else {}
            return actions.get(selected_action.lower(), False) is True
        except Exception as e:
            return False

    # First: filter by action = True
    df = df[df['actions'].apply(has_action_true)]

    # Now: filter only unassigned clients
    if 'assigned_therapist' not in df.columns:
        st.error("❌ Missing 'assigned_therapist' column in database.")
        return pd.DataFrame()  # empty

    unassigned_df = df[
        df['assigned_therapist'].isnull() |
        (df['assigned_therapist'].str.strip() == '') |
        (df['assigned_therapist'] == 'Not assigned')
    ]

    return unassigned_df

from datetime import datetime, timedelta
def ensure_columns_exist():
    conn = create_connection()
    cursor = conn.cursor()
    for col in ["assigned_therapist", "assigned_date", "to_do_date", "time_remaining", "waiting_time"]:
        try:
            cursor.execute(f"ALTER TABLE appointments ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # Already exists
    conn.commit()
    conn.close()
def assign_clients_to_therapist(appointment_id, therapist_name, to_do_date):
    assigned_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Compute initial timing
    try:
        due = datetime.strptime(to_do_date, "%Y-%m-%d")
        now = datetime.now()
        delta = due - now
        if delta.total_seconds() > 0:
            time_remaining = str(delta).split('.')[0]
            waiting_time = "-"
        else:
            time_remaining = "⏰ Overdue"
            waiting_time = str(now - due).split('.')[0]
    except:
        time_remaining = "-"
        waiting_time = "-"

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments
        SET assigned_therapist = ?, assigned_date = ?, to_do_date = ?,
            time_remaining = ?, waiting_time = ?
        WHERE appointment_id = ?
    """, (therapist_name, assigned_date, to_do_date, time_remaining, waiting_time, appointment_id))
    conn.commit()
    conn.close()
def update_all_time_fields():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT appointment_id, to_do_date FROM appointments WHERE to_do_date IS NOT NULL")
    rows = cursor.fetchall()
    now = datetime.now()

    for appointment_id, to_do_date in rows:
        try:
            due = datetime.strptime(to_do_date, "%Y-%m-%d")
            delta = due - now
            if delta.total_seconds() > 0:
                time_remaining = str(delta).split('.')[0]
                waiting_time = "-"
            else:
                time_remaining = "⏰ Overdue"
                waiting_time = str(now - due).split('.')[0]
        except:
            time_remaining = "-"
            waiting_time = "-"

        cursor.execute("""
            UPDATE appointments
            SET time_remaining = ?, waiting_time = ?
            WHERE appointment_id = ?
        """, (time_remaining, waiting_time, appointment_id))

    conn.commit()
    conn.close()

def main():
    ensure_columns_exist()
    update_all_time_fields()
    set_full_page_background('images/black_strip.jpg')
    conn = create_connection()
    client_types = pd.read_sql("SELECT DISTINCT client_type FROM appointments", conn)['client_type'].dropna().tolist()
    action_types = get_all_action_types()
    conn.close()
    if not action_types:
        st.error("⚠️ No action types found in database.")
        return
    with st.sidebar:
        selected_client_type = st.selectbox("Client Type", client_types)
        selected_action = st.selectbox("Action Type", action_types)
        therapist_list = get_available_therapists()
    appointments_df = fetch_appointments_for_assignment(selected_client_type, selected_action)
    has_unassigned = not appointments_df.empty
    if not has_unassigned:
        st.info("✅ All appointments for this action are already assigned.")
    if has_unassigned:
        bulk_mode = st.toggle("Bulk Assignment Mode", value=True)
        if bulk_mode:
            selected_rows = st.multiselect(
                "Select Appointments to Assign",
                appointments_df.apply(lambda x: f"{x['appointment_id']} - {x['name']}", axis=1).tolist()
            )
            if selected_rows:
                appointment_map = {
                    f"{row['appointment_id']} - {row['name']}": row for _, row in appointments_df.iterrows()
                }
                selected_therapist = st.selectbox("Select Therapist", therapist_list)
                to_do_date = st.date_input("🗓️ Set To-Do Deadline")

                if st.button("✅ Assign Selected to Therapist"):
                    for row_label in selected_rows:
                        row = appointment_map[row_label]
                        assign_clients_to_therapist(
                            row['appointment_id'], selected_therapist, to_do_date.strftime("%Y-%m-%d")
                        )
                    st.success(f"Successfully assigned selected clients to {selected_therapist}.")
        else:
            selected_row = st.selectbox(
                "Select a Client Appointment",
                appointments_df.apply(lambda x: f"{x['appointment_id']} - {x['name']}", axis=1).tolist()
            )
            if selected_row:
                row = appointments_df[
                    appointments_df.apply(lambda x: f"{x['appointment_id']} - {x['name']}", axis=1) == selected_row
                ].iloc[0]
                selected_therapist = st.selectbox("Select Therapist", therapist_list, key="individual_assign")
                to_do_date = st.date_input("🗓️ Set To-Do Deadline", key="individual_date")
                if st.button("Assign to Therapist"):
                    assign_clients_to_therapist(
                        row['appointment_id'], selected_therapist, to_do_date.strftime("%Y-%m-%d")
                    )
                    st.success(f"Client {row['name']} assigned to {selected_therapist}.")
        st.markdown("---")

    if st.sidebar.checkbox('View Assigned'):
        conn = create_connection()
        df_all = pd.read_sql("""
            SELECT appointment_id, name, client_type, class, stream, term,
                   assigned_therapist, assigned_date, to_do_date, actions
            FROM appointments
            WHERE client_type = ?
        """, conn, params=(selected_client_type,))
        conn.close()

        def parse_actions(actions_json):
            try:
                actions = json.loads(actions_json) if isinstance(actions_json, str) else {}
                return actions
            except:
                return {}

        action_df = df_all['actions'].apply(parse_actions).apply(pd.Series)
        action_df.columns = [f"🛠 {col.capitalize()}" for col in action_df.columns]
        display_df = pd.concat([df_all.drop(columns=["actions"]), action_df], axis=1)

        def compute_time_info(row):
            try:
                due_date = datetime.strptime(str(row['to_do_date']), "%Y-%m-%d")
                now = datetime.now()
                delta = due_date - now
                if delta.total_seconds() > 0:
                    return str(delta).split('.')[0], "-"
                else:
                    wait_time = now - due_date
                    return "⏰ Overdue", str(wait_time).split('.')[0]
            except:
                return "-", "-"

        display_df[['⏱ Time Remaining', '⏳ Waiting Time']] = display_df.apply(compute_time_info, axis=1, result_type="expand")

        if selected_action:
            action_col = f"🛠 {selected_action.capitalize()}"
            if action_col in display_df.columns:
                filtered_df = display_df[display_df[action_col] == True]
                if filtered_df.empty:
                    st.info(f"No clients found with action '{selected_action}'")
                    st.dataframe(display_df)
                else:
                    cols_to_show = [
                        'appointment_id', 'name', 'client_type', 'class', 'stream', 'term',
                        'assigned_therapist', 'assigned_date', 'to_do_date',
                        action_col, '⏱ Time Remaining', '⏳ Waiting Time'
                    ]
                    st.dataframe(filtered_df[cols_to_show])
            else:
                st.info(f"No clients found with action '{selected_action}'")
                # st.markdown(f" #### 📋 Therapist Assignment for {selected_action}")
                st.dataframe(display_df)
        else:
            
            st.dataframe(display_df)

if __name__ == "__main__":
    main()
