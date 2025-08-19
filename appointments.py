DB_PATH = "users_db.db"
import sqlite3

import json
from datetime import datetime
import os
import base64
import uuid
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd

DB = "users_db.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

DB = "users_db.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def create_appointments_table():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            username TEXT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            client_type TEXT,
            class TEXT,
            stream TEXT,
            term TEXT,
            appointment_date TEXT,
            appointment_time TEXT,
            appointment_type TEXT DEFAULT 'New',
            number_of_visits INTEGER DEFAULT 1,
            actions TEXT,
            statuses TEXT,
            action_dates TEXT,
            remaining_time TEXT,
            screening_tools TEXT,
            screen_type TEXT,
            assigned_therapist TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


create_appointments_table()
def generate_appointment_id():
    today = datetime.now().strftime("%Y%m%d")
    return f"App-{today}-{uuid.uuid4().hex[:2]}"

def insert_appointment(appointment_data):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        if "screen" in appointment_data['actions']:
            cursor.execute("""
                SELECT COUNT(*) FROM appointments
                WHERE user_id = ?
                  AND term = ?
                  AND screen_type = ?
                  AND strftime('%Y', appointment_date) = strftime('%Y', ?)
                  AND json_extract(actions, '$.screen') = 1
            """, (
                appointment_data['user_id'],
                appointment_data.get('term', ''),
                appointment_data.get('screen_type', ''),
                appointment_data.get('appointment_date', datetime.today().strftime('%Y-%m-%d'))
            ))
            if cursor.fetchone()[0] > 0:
                return False, "Duplicate screening appointment already exists for this term, screen type, and year."

        cursor.execute("""
            INSERT INTO appointments (
                appointment_id, user_id, username, name, age, gender, client_type,
                class, stream, term, appointment_date, appointment_time,
                appointment_type, number_of_visits, actions, statuses,
                action_dates, remaining_time, assigned_therapist,
                screening_tools, screen_type, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
        """, (
            appointment_data['appointment_id'],
            appointment_data['user_id'],
            appointment_data.get('username'),
            appointment_data['name'],
            appointment_data.get('age'),
            appointment_data.get('gender'),
            appointment_data['client_type'],
            appointment_data.get('class'),
            appointment_data.get('stream'),
            appointment_data.get('term'),
            appointment_data.get('appointment_date'),
            appointment_data.get('appointment_time'),
            appointment_data['appointment_type'],
            appointment_data['number_of_visits'],
            json.dumps(appointment_data['actions']),
            json.dumps(appointment_data['statuses']),
            json.dumps(appointment_data['action_dates']),
            json.dumps(appointment_data['remaining_time']),
            json.dumps(appointment_data['assigned_therapist']),
            json.dumps(appointment_data.get('screening_tools', {})),
            appointment_data.get('screen_type'),
            appointment_data['created_by']
        ))
        conn.commit()
        return True, "Appointment created successfully!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_visit_count(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def fetch_therapist_usernames():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE role = 'Therapist'")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def fetch_students_by_class_stream(student_class, student_stream):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, full_name, role, class, stream
        FROM users
        WHERE role = 'Student' AND class = ? AND stream = ?
    """, (student_class, student_stream))
    result = cursor.fetchall()
    conn.close()
    return result

def has_pending_action(user_id, action, term):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT statuses, term FROM appointments
        WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    for status_json, row_term in rows:
        try:
            statuses = json.loads(status_json)
            if statuses.get(action) == "Pending" and row_term == term:
                return True
        except:
            continue
    return False

def fetch_users_by_input(db, search_input, role_filter):
    cursor = db.cursor()
    search_input = search_input.strip()
    query = """
        SELECT * FROM users 
        WHERE role = ? AND (
            user_id LIKE ? OR 
            full_name LIKE ?
        )
    """
    pattern = f"%{search_input}%"
    cursor.execute(query, (role_filter, pattern, pattern))
    return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

def set_full_page_background(image_path):
    try:
        if not os.path.exists(image_path):
            st.warning(f"Missing background image: {image_path}")
            return
        with open(image_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/png;base64,{b64_img}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            </style>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Background error: {e}")

def appointment_form():
    username = st.session_state.get("user_name", "admin")
    db = create_connection()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT role FROM users WHERE role NOT IN ('Therapist', 'Admin', 'Admin2')")
        client_roles = [row[0] for row in cursor.fetchall()]

    with st.sidebar:
        selected_client_type = st.selectbox("Select Client Type", client_roles)
        is_bulk_mode = (
            selected_client_type == "Student"
            and st.toggle("Bulk Mode (Class-wise)", value=False))
    therapists = fetch_therapist_usernames()


    if selected_client_type == "Student" and is_bulk_mode:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT class FROM users WHERE role = 'Student' AND class IS NOT NULL"
            )
            all_classes = sorted([row[0] for row in cursor.fetchall()])

        with st.expander("BOOK MANY", expanded=True):
            col1, col2 = st.columns(2)
            selected_classes = col1.multiselect("Select Class(es)", all_classes)

            all_streams = []
            if selected_classes:
                query = f"""
                    SELECT DISTINCT stream FROM users
                    WHERE role = 'Student' AND stream IS NOT NULL
                    AND class IN ({','.join(['?']*len(selected_classes))})
                """
                cursor.execute(query, selected_classes)
                all_streams = sorted([row[0] for row in cursor.fetchall()])

            selected_streams = col2.multiselect("Select Stream(s)", all_streams)

            students = fetch_students_by_class_stream_bulk(selected_classes, selected_streams)
            all_names = [s[1] for s in students]
            selected_names = col2.multiselect("Select Student(s)", all_names)

            term = col1.selectbox("Select Term", ['', "1st-Term", "2nd-Term", "3rd-Term"])
            selected_actions = col1.multiselect("Actions", ["screen", "consult", "group session"])
            created_by = col2.selectbox("Created By", [username])

        if st.button("Create Appointments for Selected Group"):
            if not selected_actions or not term:
                st.warning("⚠️ Please select at least one action and a term.")
                return
            screen_type = None
            if "screen" in selected_actions:
                screen_type = col2.selectbox(
                    "Select Screen Type",
                    ['', "PRE-SCREEN", "POST-SCREEN", "ON-CONSULT", "SELF-REQUEST"],
                )
                if not screen_type:
                    st.warning("⚠️ Please select a valid Screen Type for 'screen'.")
                    return

            created, skipped = 0, 0
            skipped_users, created_users = [], []

            for student in students:
                user_id, name, _, cls, stream = student
                if name not in selected_names:
                    continue
                if any(has_pending_action(user_id, action, term) for action in selected_actions):
                    skipped += 1
                    skipped_users.append(name)
                    continue

                appointment_type = "New" if get_visit_count(user_id) == 0 else "Revisit"
                number_of_visits = get_visit_count(user_id) + 1
                now = datetime.now()
                dt_str = now.strftime("%Y-%m-%d %H:%M:%S")
                delta = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S") - now

                data = {
                    "appointment_id": generate_appointment_id(),
                    "user_id": user_id,
                    "name": name,
                    "client_type": "Student",
                    "appointment_type": appointment_type,
                    "number_of_visits": number_of_visits,
                    "class": cls,
                    "stream": stream,
                    "term": term,
                    "actions": {a: True for a in selected_actions},
                    "assigned_therapist": {a: [created_by] for a in selected_actions},
                    "statuses": {a: {"status": "Pending", "completion_date": None} for a in selected_actions},
                    "action_dates": {a: dt_str for a in selected_actions},
                    "remaining_time": {a: f"{delta.days} days" for a in selected_actions},
                    "created_by": created_by,
                    "screen_type": screen_type if "screen" in selected_actions else None,
                }

                success, msg = insert_appointment(data)
                if success:
                    created += 1
                    created_users.append(name)
                else:
                    st.error(f"Failed for {name}: {msg}")

            if created_users:
                st.success(f"Created Appointments for: {', '.join(created_users)}")
            if skipped_users:
                st.warning(f"Skipped (Pending Actions Exist): {', '.join(skipped_users)}")

    # -------------------------------------------------
    # INDIVIDUAL MODE
    # -------------------------------------------------
    if not is_bulk_mode:
        with st.sidebar.expander("Search & Select Client", expanded=True):
            search_input = st.text_input("Enter name or student ID")
            results = (
                fetch_users_by_input(db, search_input, selected_client_type)
                if search_input.strip()
                else []
            )
            selected_record = None
            if results:
                st.write(f"Found {len(results)} result(s)")
                options = {f"{r['full_name']} - {r['user_id']}": r for r in results}
                selected_option = st.selectbox("Select Record", list(options.keys()))
                selected_record = options[selected_option]
                st.markdown("---")
                st.write("###  Client Details")
                st.write(f"**Name:** {selected_record['full_name']}")
                st.write(f"**ID:** {selected_record['user_id']}")
                st.write(f"**Role:** {selected_record['role']}")
                if selected_record['role'] == "Student":
                    st.write(f"**Class:** {selected_record.get('class')}")
                    st.write(f"**Stream:** {selected_record.get('stream')}")

        if not selected_record:
            st.info("Select a client to continue.")
            return

        # Basic client details
        user_id = selected_record['user_id']
        name = selected_record['full_name']
        client_type = selected_record['role']
        student_class = selected_record.get('class') if client_type == "Student" else None
        student_stream = selected_record.get('stream') if client_type == "Student" else None

        with st.expander("CREATE_APPOINTMENT", expanded=True):
            col1, col2 = st.columns(2)

            term = (
                col1.selectbox("Term", ["", "1st-Term", "2nd-Term", "3rd-Term"])
                if client_type == "Student"
                else None
            )
            col2.text_input("Client Name", value=name, disabled=True)
            selected_actions = col2.multiselect("Select Actions", ["screen", "consult", "group session"])
            created_by = col1.selectbox("Created By", [username])

            screen_type = None
            if "screen" in selected_actions and client_type == "Student":
                screen_type = col2.selectbox(
                    "Select Screen Type",
                    ['', "PRE-SCREEN", "POST-SCREEN", "ON-CONSULT", "SELF-REQUEST"],
                )

            # Validate pending actions for students
            for action in selected_actions:
                if client_type == "Student" and has_pending_action(user_id, action, term):
                    st.warning(f"{action} appointment for {name} is still pending in {term}.")
                    return

            appointment_type = "New" if get_visit_count(user_id) == 0 else "Revisit"
            col1.text_input("Appointment Type", appointment_type)
            number_of_visits = get_visit_count(user_id) + 1

            actions, assigned_therapist, statuses, action_dates, remaining_time = {}, {}, {}, {}, {}

            for action in selected_actions:
                assignment_mode = st.radio(
                    f"Who will handle '{action}'?",
                    ["Self", "Assign Therapist(s)"],
                    key=f"{action}_radio",
                )
                if assignment_mode == "Self":
                    assigned_therapist[action] = ["SELF"]
                else:
                    selected = col2.multiselect(
                        f"Select Therapist(s) for '{action}'", therapists, key=f"{action}_therapist_multi"
                    )
                    assigned_therapist[action] = selected if selected else []

                statuses[action] = "Pending"
                date = col1.date_input(f"Date for {action}", key=f"{action}_date")
                time = col2.time_input(f"Time for {action}", key=f"{action}_time")
                dt_str = f"{date} {time}"
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                delta = dt_obj - datetime.now()
                action_dates[action] = dt_str
                remaining_time[action] = f"{delta.days} days"
                actions[action] = True

        if st.button("Create Appointment"):
            if not selected_actions:
                st.warning("⚠️ Please select at least one action.")
                return
            if client_type == "Student" and not term:
                st.warning("⚠️ Please select a term.")
                return
            if "screen" in selected_actions and client_type == "Student" and not screen_type:
                st.warning("⚠️ Please select a valid **Screen Type** for 'screen'.")
                return

            for action in selected_actions:
                if not assigned_therapist.get(action):
                    st.warning(f"⚠️ Please assign a therapist or select 'Self' for '{action}'.")
                    return
                if not action_dates.get(action):
                    st.warning(f"⚠️ Please select a date and time for '{action}'.")
                    return

            data = {
                "appointment_id": generate_appointment_id(),
                "user_id": user_id,
                "name": name,
                "client_type": client_type,
                "appointment_type": appointment_type,
                "number_of_visits": number_of_visits,
                "class": student_class,
                "stream": student_stream,
                "term": term,
                "actions": actions,
                "assigned_therapist": assigned_therapist,
                "statuses": statuses,
                "action_dates": action_dates,
                "remaining_time": remaining_time,
                "created_by": created_by,
                "appointment_date": action_dates[selected_actions[0]] if selected_actions else "",
                "appointment_time": action_dates[selected_actions[0]][11:] if selected_actions else "",
                "screen_type": screen_type if ("screen" in selected_actions and client_type == "Student") else None,
            }

            success, msg = insert_appointment(data)
            if success:
                st.success(
                    f"{msg} (Type: {appointment_type}, Visit#: {number_of_visits}, Role: {client_type})"
                )
            else:
                st.error(msg)


def fetch_students_by_class_stream_bulk(classes, streams):
    placeholders_cls = ','.join(['?'] * len(classes))
    placeholders_str = ','.join(['?'] * len(streams))
    query = f"""
        SELECT user_id, full_name, role, class, stream FROM users
        WHERE role = 'Student'
        AND class IN ({placeholders_cls})
        AND stream IN ({placeholders_str})
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, classes + streams)
        return cursor.fetchall()

def fetch_all_appointments():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC")
    rows = cursor.fetchall()
    return rows

def is_screening_complete(screening_tools):
    try:
        return all(tool.get("tool_status") == "Complete" for tool in screening_tools.values())
    except:
        return False

def compute_remaining(action_dates_str):
    try:
        action_dates = json.loads(action_dates_str)
        remaining = {}
        for action, dt_str in action_dates.items():
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                delta = dt - datetime.now()
                if delta.total_seconds() < 0:
                    remaining[action] = "Overdue"
                else:
                    remaining[action] = f"{delta.days}d"
            except:
                remaining[action] = "Invalid"
        return json.dumps(remaining)
    except:
        return "{}"





def display_appointment_table():
    st.subheader("📋 All Appointments")
    rows = fetch_all_appointments()
    if not rows:
        st.info("No appointments recorded yet.")
        return

    data = []
    for row in rows:
        appt = dict(row)
        actions = json.loads(appt["actions"])
        statuses = json.loads(appt["statuses"])
        screen_complete = "N/A"  # You can implement if needed
        data.append({
            "Date": appt["appointment_date"],
            "Time": appt["appointment_time"],
            "Name": appt["name"],
            "Client Type": appt["client_type"],
            "Actions": ", ".join(actions.keys()),
            "Status": json.dumps(statuses),
            "Screen Complete": screen_complete,
            "Created By": appt["created_by"],
            "Term": appt.get("term", "-") or "-",
            "Remaining": compute_remaining(appt["action_dates"])
        })

    df = pd.DataFrame(data)
    with st.expander("🗂 View Appointments Table", expanded=True):
        st.dataframe(df, use_container_width=True)

def count_pending_consult_clients(therapist_name):
    conn = create_connection()
    query = """
        SELECT * FROM appointments
        WHERE assigned_therapist = ? AND actions LIKE '%consult%'
    """
    df = pd.read_sql(query, conn, params=(therapist_name,))
    conn.close()

    count = 0
    for row in df.itertuples():
        try:
            statuses = json.loads(row.statuses)
            if statuses.get("consult") == "Pending":
                count += 1
        except:
            continue
    return count






def fetch_unique_classes():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT class FROM users WHERE class IS NOT NULL AND class != '' ORDER BY class")
        return [row[0] for row in cursor.fetchall()]

def fetch_unique_streams():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT stream FROM users WHERE stream IS NOT NULL AND stream != '' ORDER BY stream")
        return [row[0] for row in cursor.fetchall()]


def edit_appointment_form():
    st.subheader("✏️ Edit Appointment")
    db = create_connection()
    therapists = fetch_therapist_usernames()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT role FROM users WHERE role NOT IN ('Therapist', 'Admin', 'Admin2')")
        client_roles = [row[0] for row in cursor.fetchall()]

    with st.sidebar:
        selected_client_type = st.selectbox("Select Client Type", client_roles)

    if "SELF" not in therapists:
        therapists.append("SELF")

    selected_records = []

    with st.sidebar.expander("Search & Select Appointment", expanded=True):
        bulk_mode = st.checkbox("🔁 Bulk Mode", value=False)

        if bulk_mode:
            class_options = fetch_unique_classes()
            stream_options = fetch_unique_streams()
            selected_classes = st.multiselect("Select Classes", class_options)
            selected_streams = st.multiselect("Select Streams", stream_options)

            matched_students = fetch_students_by_class_stream_bulk(selected_classes, selected_streams)
            matched_appointments = [appt for appt in fetch_all_appointments() if appt["user_id"] in [s[0] for s in matched_students] and appt["client_type"] == selected_client_type]

            if matched_appointments:
                st.success(f"Found {len(matched_appointments)} matching appointment(s)")
                selected_options = st.multiselect("Select Appointment(s) to Edit", [f"{a['name']} - {a['appointment_id']}" for a in matched_appointments])
                selected_records = [a for a in matched_appointments if f"{a['name']} - {a['appointment_id']}" in selected_options]
        else:
            search_input = st.text_input("Enter name or student ID")
            matched_appointments = []
            if search_input.strip():
                all_appts = fetch_all_appointments()
                for appt in all_appts:
                    if selected_client_type != appt["client_type"]:
                        continue
                    if search_input.lower() in appt["name"].lower() or search_input.lower() in appt["user_id"].lower():
                        matched_appointments.append(appt)

                if matched_appointments:
                    st.write(f"Found {len(matched_appointments)} result(s)")
                    options = {f"{a['name']} - {a['appointment_id']}": a for a in matched_appointments}
                    selected_option = st.selectbox("Select Appointment", list(options.keys()))
                    selected_records = [options[selected_option]]
                    st.markdown("---")
                    selected_record = selected_records[0]
                    st.write("###  Appointment Details")
                    st.write(f"**Name:** {selected_record['name']}")
                    st.write(f"**User-ID:** {selected_record['user_id']}")
                    st.write(f"**Appoint-ID:** {selected_record['appointment_id']}")
                    st.write(f"**Appoint-date:** {selected_record['appointment_date']}")
                    st.write(f"**Client-Type:** {selected_record['client_type']}")
                    if selected_record['client_type'] == "Student":
                        st.write(f"**Class:** {selected_record['class']}")
                        st.write(f"**Stream:** {selected_record['stream']}")

    if not selected_records:
        st.info("Select at least one appointment to edit.")
        return
    selected_record = selected_records[0]
    prev_actions = json.loads(selected_record["actions"])
    prev_statuses_raw = json.loads(selected_record["statuses"])
    prev_actions = json.loads(selected_record["actions"])
    prev_statuses = json.loads(selected_record["statuses"])
    prev_assigned = json.loads(selected_record["assigned_therapist"]) if "assigned_therapist" in selected_record.keys() else {}
    prev_dates = json.loads(selected_record["action_dates"]) if "action_dates" in selected_record.keys() else {}
    screen_type = selected_record["screen_type"] if "screen_type" in selected_record.keys() else ""
    username = st.session_state.get("user_name", "admin")
    with st.expander("EDIT_APPOINTMENT", expanded=True):
        col1, col2 = st.columns(2)
        term_list = ["", "1st-Term", "2nd-Term", "3rd-Term"]
        current_term = selected_record["term"]
        term = col1.selectbox("Term", term_list, index=term_list.index(current_term) if current_term in term_list else 0) if selected_record["client_type"] == "Student" else None
        col2.text_input("Client Name", value=selected_record["name"], disabled=True)
        selected_actions = col2.multiselect("Select Actions", ["screen", "consult", "group session"], default=list(prev_actions.keys()))
        created_by = col1.selectbox("Created By", [username])

        if "screen" in selected_actions:
            screen_type_options = ["", "PRE-SCREEN", "POST-SCREEN", "ON-CONSULT", "SELF-REQUEST"]
            screen_type = col2.selectbox("Select Screen Type", screen_type_options, index=screen_type_options.index(screen_type or ""))
        else:
            screen_type = None

        actions, assigned_therapist, statuses, action_dates, remaining_time = {}, {}, {}, {}, {}

        for action in selected_actions:
            assignment_mode = st.radio(f"Who will handle '{action}'?", ["Self", "Assign Therapist(s)"], key=f"{action}_radio_edit")
            if assignment_mode == "Self":
                assigned_therapist[action] = ["SELF"]
            else:
                selected_th = col2.multiselect(
                    f"Select Therapist(s) for '{action}'",
                    therapists,
                    default=prev_assigned.get(action, []),
                    key=f"{action}_therapist_multi_edit"
                )
                assigned_therapist[action] = selected_th if selected_th else []

            previous_status = prev_statuses_raw.get(action)
            if isinstance(previous_status, dict):
                status_val = previous_status.get("status", "Pending")
                completion_date = previous_status.get("completion_date")
                prev_actions = json.loads(selected_record["actions"])
            else:
                status_val = previous_status or "Pending"
                completion_date = None
            statuses[action] = {"status": status_val, "completion_date": completion_date}
            fallback_dt = f"{selected_record['appointment_date']} {selected_record['appointment_time']}"
            dt_string = prev_dates.get(action, fallback_dt)

            try:
                dt_str = f"{date} {time}"
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

                default_date = dt_obj.date()
                default_time = dt_obj.time()
            
            except:
                default_date = datetime.now().date()
                default_time = datetime.now().time()

            date = col1.date_input(f"Date for {action}", value=default_date, key=f"{action}_date_edit")
            time = col2.time_input(f"Time for {action}", value=default_time, key=f"{action}_time_edit")

            dt_str = f"{date} {time}"
            delta = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f") - datetime.now()

            action_dates[action] = dt_str
            remaining_time[action] = f"{delta.days} days"
            actions[action] = True

    if st.button("Update Appointment"):
        if not selected_actions:
            st.warning("⚠️ Please select at least one action.")
            return
        if not term:
            st.warning("⚠️ Please select a term.")
            return
        if "screen" in selected_actions and not screen_type:
            st.warning("⚠️ Please select a valid Screen Type for 'screen'.")
            return
        for action in selected_actions:
            if not assigned_therapist.get(action) or assigned_therapist[action] == []:
                st.warning(f"⚠️ Please assign a therapist or select 'Self' for '{action}'.")
                return
            if not action_dates.get(action):
                st.warning(f"⚠️ Please select a date and time for '{action}'.")
                return

        try:
            conn = create_connection()
            cursor = conn.cursor()
            for appt in selected_records:
                cursor.execute("""
                    UPDATE appointments SET
                        term = ?, actions = ?, assigned_therapist = ?, statuses = ?,
                        action_dates = ?, remaining_time = ?, screen_type = ?,
                        appointment_date = ?, appointment_time = ?, created_by = ?
                    WHERE appointment_id = ?
                """, (
                    term,
                    json.dumps(actions),
                    json.dumps(assigned_therapist),
                    json.dumps(statuses),
                    json.dumps(action_dates),
                    json.dumps(remaining_time),
                    screen_type,
                    action_dates[selected_actions[0]].split()[0],
                    action_dates[selected_actions[0]].split()[1],
                    created_by,
                    appt["appointment_id"]
                ))
            conn.commit()
            st.success(f"✅ Updated {len(selected_records)} appointment(s) successfully.")
        except Exception as e:
            st.error(f"❌ Error updating appointment(s): {e}")
        finally:
            conn.close()



# --- Main App ---
def main():
    create_appointments_table()
    set_full_page_background("images/black_strip.jpg")
    selected = option_menu(
        menu_title=None,
        options=["BOOK", "VIEW", 'EDIT'],
        icons=["calendar2-plus", "table", 'pencil-square'],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

    if selected == "BOOK":
        appointment_form()
    elif selected == "VIEW":
        display_appointment_table()
    
    elif selected == 'EDIT':
        edit_appointment_form()


if __name__ == "__main__":
    main()

