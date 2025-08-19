import sqlite3

import json
from datetime import datetime
import streamlit as st
import os, base64, json
import pandas as pd
import threading 
from pushbullet import Pushbullet
import threading 
import smtplib
from email.message import EmailMessage
import sqlite3


API_KEY = st.secrets["push_API_KEY"]
pb = Pushbullet(API_KEY)
DB_PATH = "users_db.db"

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def alter_screen_table_add_tools_columns():
    conn = create_connection()
    cursor = conn.cursor()
    try: cursor.execute("ALTER TABLE screen ADD COLUMN tools TEXT DEFAULT '[]'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_statuses TEXT DEFAULT '{}'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_scheduled_dates TEXT DEFAULT '{}'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_response_dates TEXT DEFAULT '{}'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_responses TEXT DEFAULT '{}'")  # 🆕 New
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE screen ADD COLUMN screen_type TEXT DEFAULT 'PRE-SCREEN'")  # ✅ Add this
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()


# def assign_tools_to_screen(action_id, appointment_id, user_id, created_by, tools_to_assign, scheduled_date):
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT tools, tools_statuses, tools_scheduled_dates, tools_response_dates, tools_responses FROM screen WHERE action_id = ?", (action_id,))
#     row = cursor.fetchone()
#     if row:
#         current_tools = json.loads(row[0]) if row[0] else []
#         current_statuses = json.loads(row[1]) if row[1] else {}
#         current_scheduled = json.loads(row[3]) if row[3] else {}
#         current_response = json.loads(row[4]) if row[4] else {}

#         new_tools_added = 0
#         skipped_tools = 0
#         for tool in tools_to_assign:
#             if tool in current_tools and current_statuses.get(tool) == 'Pending':
#                 skipped_tools += 1
#                 continue
#             if tool not in current_tools:
#                 current_tools.append(tool)
#             current_statuses[tool] = 'Pending'
#             current_scheduled[tool] = scheduled_date
#             current_response[tool] = None
#             new_tools_added += 1

#         cursor.execute("""
#             UPDATE screen SET
#                 tools = ?, tools_statuses = ?, tools_scheduled_dates = ?, tools_response_dates = ?
#             WHERE action_id = ?
#         """, (
#             json.dumps(current_tools),
#             json.dumps(current_statuses),
#             json.dumps(current_scheduled),
#             json.dumps(current_response),
#             action_id
#         ))
#         conn.commit()
#         conn.close()
#         return new_tools_added, skipped_tools
#     else:
#         tools_statuses = {tool: 'Pending' for tool in tools_to_assign}
#         tools_scores = {tool: None for tool in tools_to_assign}
#         tools_scheduled_dates = {tool: scheduled_date for tool in tools_to_assign}
#         tools_response_dates = {tool: None for tool in tools_to_assign}
#         cursor.execute("""
#             INSERT INTO screen (
#                 action_id, appointment_id, user_id, created_by,
#                 tools, tools_statuses, tools_scheduled_dates, tools_response_dates
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             action_id,
#             appointment_id,
#             user_id,
#             created_by,
#             json.dumps(tools_to_assign),
#             json.dumps(tools_statuses),
#             json.dumps(tools_scores),
#             json.dumps(tools_scheduled_dates),
#             json.dumps(tools_response_dates)
#         ))
#         conn.commit()
#         conn.close()
#         return len(tools_to_assign), 0
def assign_tools_to_screen(action_id, appointment_id, user_id, created_by, tools_to_assign, scheduled_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tools, tools_statuses, tools_scheduled_dates, tools_response_dates, tools_responses FROM screen WHERE action_id = ?", (action_id,))
    row = cursor.fetchone()
    if row:
        current_tools = json.loads(row[0]) if row[0] else []
        current_statuses = json.loads(row[1]) if row[1] else {}
        current_scheduled = json.loads(row[2]) if row[2] else {}
        current_response = json.loads(row[3]) if row[3] else {}

        new_tools_added = 0
        skipped_tools = 0

        for tool in tools_to_assign:
            if tool in current_tools:
                skipped_tools += 1
                continue  # Don't reassign if already exists on this action_id
            current_tools.append(tool)
            current_statuses[tool] = 'Pending'
            current_scheduled[tool] = scheduled_date
            current_response[tool] = None
            new_tools_added += 1

        cursor.execute("""
            UPDATE screen SET
                tools = ?, tools_statuses = ?, tools_scheduled_dates = ?, tools_response_dates = ?
            WHERE action_id = ?
        """, (
            json.dumps(current_tools),
            json.dumps(current_statuses),
            json.dumps(current_scheduled),
            json.dumps(current_response),
            action_id
        ))
        conn.commit()
        conn.close()
        return new_tools_added, skipped_tools
    else:
        tools_statuses = {tool: 'Pending' for tool in tools_to_assign}
        tools_scheduled_dates = {tool: scheduled_date for tool in tools_to_assign}
        tools_response_dates = {tool: None for tool in tools_to_assign}
        cursor.execute("""
            INSERT INTO screen (
                action_id, appointment_id, user_id, created_by,
                tools, tools_statuses, tools_scheduled_dates, tools_response_dates
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action_id,
            appointment_id,
            user_id,
            created_by,
            json.dumps(tools_to_assign),
            json.dumps(tools_statuses),
            json.dumps(tools_scheduled_dates),
            json.dumps(tools_response_dates)
        ))
        conn.commit()
        conn.close()
        return len(tools_to_assign), 0




# def update_tool_response_in_screen(action_id, tool_name, score, responses_dict=None, response_date_str=None):
#     if response_date_str is None:
#         response_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         SELECT tools_statuses, tools_response_dates, tools_responses, appointment_id
#         FROM screen WHERE action_id = ?
#     """, (action_id,))
#     row = cursor.fetchone()
#     if not row:
#         conn.close()
#         return False, "Screen ID not found"
#     tools_statuses = json.loads(row[0]) if row[0] else {}
#     tools_response_dates = json.loads(row[1]) if row[1] else {}
#     tools_responses = json.loads(row[2]) if row[2] else {}
#     appointment_id = row[3]
#     tools_statuses[tool_name] = "Completed"
#     tools_scores[tool_name] = score
#     tools_response_dates[tool_name] = response_date_str
#     if responses_dict:
#         tools_responses[tool_name] = responses_dict
#     cursor.execute("""
#         UPDATE screen SET
#             tools_statuses = ?,
#             tools_response_dates = ?,
#             tools_responses = ?
#         WHERE action_id = ?
#     """, (
#         json.dumps(tools_statuses),
#         json.dumps(tools_scores),
#         json.dumps(tools_response_dates),
#         json.dumps(tools_responses),
#         action_id
#     ))

#     if appointment_id:
#         cursor.execute("SELECT statuses FROM appointments WHERE appointment_id = ?", (appointment_id,))
#         result = cursor.fetchone()
#         if result:
#             appt_statuses = json.loads(result[0]) if result[0] else {}
#             appt_statuses[tool_name] = "Completed"
#             assigned_tools = list(tools_statuses.keys())
#             all_tools_completed = all(tools_statuses[t] == "Completed" for t in assigned_tools)

#             if all_tools_completed:
#                 appt_statuses["screen"] = "Completed"

#             cursor.execute("""
#                 UPDATE appointments SET statuses = ?
#                 WHERE appointment_id = ?
#             """, (
#                 json.dumps(appt_statuses),
#                 appointment_id
#             ))

#     conn.commit()
#     conn.close()
#     return True, "Tool response updated successfully"


def get_screens_with_tools(client_type_filter=None):
    conn = create_connection()
    cursor = conn.cursor()
    if client_type_filter:
        cursor.execute("""
            SELECT action_id, tools FROM screen WHERE tools IS NOT NULL AND tools != '[]' AND client_type = ?
        """, (client_type_filter,))
    else:
        cursor.execute("""
            SELECT action_id, tools FROM screen WHERE tools IS NOT NULL AND tools != '[]'
        """)
    rows = cursor.fetchall()
    conn.close()

    screen_tool_map = {}
    for action_id, tools_json in rows:
        try:
            tools = json.loads(tools_json)
            if isinstance(tools, list) and tools:
                screen_tool_map[action_id] = tools
        except:
            continue
    return screen_tool_map

def initialize_session_vars():
    defaults = {
        'action_id': None,
        'appointment_id': None,
        'user_id': None,
        'client_name': None,
        'client_type': None,
        'username': "SELF"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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

def search_pending_screens_by_client_name(db, client_type, screen_type, search_input):
    cursor = db.cursor()
    name_parts = search_input.strip().split()
    query_conditions = [
        "status = 'Pending'",
        "client_type = ?",
        "screen_type = ?"]
    params = [client_type, screen_type]
    if len(name_parts) == 2:
        query_conditions.append("(client_name LIKE ? OR client_name LIKE ?)")
        first_name, last_name = name_parts
        params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
    else:
        query_conditions.append("client_name LIKE ?")
        params.append(f"%{search_input.strip()}%")
    query = f"""
        SELECT action_id, client_name, created_at
        FROM screen
        WHERE {" AND ".join(query_conditions)}
        ORDER BY created_at DESC"""
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    return results



def fetch_screen_appointments_users(db, search_input, selected_term=None, selected_screen_type=None):
    cursor = db.cursor()
    if search_input.strip().upper().startswith("SCREEN-") or search_input.isdigit():
        query = """
        SELECT action_id, user_id, client_name, appointment_id, class, stream, term, screen_type, created_by
        FROM screen WHERE appointment_id = ?
        """
        params = (search_input.strip(),)
    else:
        name_parts = search_input.strip().split()
        query_conditions = []
        params = []
        if len(name_parts) == 2:
            first_name, last_name = name_parts
            query_conditions.append("client_name LIKE ?")
            query_conditions.append("client_name LIKE ?")
            params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
        else:
            query_conditions.append("client_name LIKE ?")
            params.append(f"%{search_input}%")
        if selected_term:
            query_conditions.append("term = ?")
            params.append(selected_term)
        if selected_screen_type:
            query_conditions.append("screen_type = ?")
            params.append(selected_screen_type)
        query = f"""
        SELECT action_id, user_id, client_name, appointment_id, class, stream, term, screen_type, created_by
        FROM screen
        WHERE {" AND ".join(query_conditions)}
        """
    query += " ORDER BY created_at DESC"
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()  
    return results


def fetch_screen_tools(appointment_id, db):
    cursor = db.cursor()
    cursor.execute("""
        SELECT action_id, appointment_id, client_name, screen_type, class, stream, term, client_type,
               tools, tools_statuses
        FROM screen
        WHERE tools IS NOT NULL AND tools != '' AND action_type = 'screen' AND appointment_id = ?
        ORDER BY action_id
    """, (appointment_id,))
    screens = cursor.fetchall()
    cursor.close()

    records = []
    for row in screens:
        try:
            tools_list = json.loads(row[8]) if row[8] else []  # tools
        except Exception as e:
            st.warning(f"Failed to parse tools for action_id {row[0]}: {e}")  # action_id
            tools_list = []

        try:
            tools_statuses = json.loads(row[9]) if row[9] else {}  # tools_statuses
        except Exception as e:
            st.warning(f"Failed to parse tools_statuses for action_id {row[0]}: {e}")
            tools_statuses = {}

        for tool in tools_list:
            status = tools_statuses.get(tool, "Pending")
            records.append({
                'appointment_id':row[1],
                "action_id": row[0],
                "client_name": row[2],
                # "client_type": row[7],
                "class": row[4],
                "stream": row[5],
                "term": row[6],
                "screen_type": row[3],
                "tool": tool,
                "status": status})

    return pd.DataFrame(records)


#### notifications #######
def fetch_user_email_by_name(name):
    conn = create_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        query = "SELECT email FROM users WHERE full_name = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def fetch_user_contact_by_name(name):
    conn = create_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        query = "SELECT contact FROM users WHERE full_name = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def send_email(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['To'] = to  
    user = st.secrets['U']
    msg['From'] = user
    password = st.secrets['SECRET']
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        st.success(f"📧 Email notification sent to {to}")
    except Exception as e:
        st.error(f"Error sending email: {e}")


def send_sms_notification(phone_number, message):
    st.warning("⚠️ SMS sending not implemented yet. Integrate an API like Twilio.")
    return


def send_email_notification(name, tools, date, email):
    subject = "🔔 Screening Tools Assigned"
    body = (f"Dear {name},\n\n"
            f"You have been assigned the following screening tools to complete:\n"
            f"{''.join(tools)}\n\n"
            f"Activity created on: {date}\n\n"
            f"Please ensure you complete them on time.\n\n"
            f"Best regards,\n"
            f"PUKKA PSYCHOMETRIC & PSYCHOLOGICAL SERVICES ")
    
    send_email(subject, body, email)


def send_notifications(name, tools, date):
    message = (f'Dear {name} !! \n'
               f'You have {tools} to fill \n'
               f'Scheduled on: {date}\n'
               f'Please ignore this message if already attended to') 

    threading.Thread(target=pb.push_note, args=("🔔 TODO Alert", message)).start()
    student_email = fetch_user_email_by_name(name)
    
    if student_email:
        send_email_notification(name, tools, date, student_email)
    phone_number = fetch_user_contact_by_name(name)
    if phone_number:
        send_sms_notification(phone_number, message)


def remove_requested_tool(db, action_id, appointment_id, tool_to_remove):
    cursor = db.cursor()
    cursor.execute("""
        SELECT tools, tools_statuses
        FROM screen
        WHERE action_id = ? AND appointment_id = ?
    """, (action_id, appointment_id))
    result = cursor.fetchone()
    if not result:
        st.error("No matching record found.")
        return
    try:
        tools = json.loads(result[0]) if result[0] else []
        tool_statuses = json.loads(result[1]) if result[1] else {}
    except Exception as e:
        st.error(f"Error parsing tools data: {e}")
        return

    if tool_to_remove not in tools:
        st.warning(f"Tool '{tool_to_remove}' not found.")
        return

    if tool_statuses.get(tool_to_remove) == "Completed":
        st.warning(f"Tool '{tool_to_remove}' is marked as Completed and cannot be removed.")
        return

    tools.remove(tool_to_remove)
    tool_statuses.pop(tool_to_remove, None)
    updated_tools_json = json.dumps(tools)
    updated_statuses_json = json.dumps(tool_statuses)

    cursor.execute("""
        UPDATE screen
        SET tools = ?, tools_statuses = ?
        WHERE action_id = ? AND appointment_id = ?
    """, (updated_tools_json, updated_statuses_json, action_id, appointment_id))
    db.commit()
    cursor.close()
    st.success(f"✅ Tool '{tool_to_remove}' was successfully removed.")





def screen_type_exists_for_appointment(db, appointment_id, screen_type):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 1 FROM screen
        WHERE appointment_id = ? AND screen_type = ?
        LIMIT 1
    """, (appointment_id, screen_type))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists

def is_pre_screen_completed(db, appointment_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT status FROM screen
        WHERE appointment_id = ? AND screen_type = 'PRE-SCREEN'
    """, (appointment_id,))
    row = cursor.fetchone()
    cursor.close()
    return row and row[0] == "Completed"


def get_available_screen_types(db, appointment_id):
    used_types = pd.read_sql("SELECT DISTINCT screen_type FROM screen WHERE appointment_id = ?", db, params=[appointment_id])['screen_type'].tolist()
    possible = ["PRE-SECREEN", "POST-SCREEN",'ON-CONSULT','ON-REQUEST']  # or dynamic from DB
    return [s for s in possible if s not in used_types]


def main():
    set_full_page_background('images/black_strip.jpg')
    alter_screen_table_add_tools_columns()
    db = create_connection()
    bulk_mode = st.toggle("Bulk Assign Mode", value=True)
    tools_list = ["PHQ-4", "PHQ-9", "GAD-7", 'CAPS-14','SSQ','HSQ','SNAP-IV-C', "DASS-21", 'BDI', "SRQ"]
    client_types = pd.read_sql("SELECT DISTINCT client_type FROM screen", db)['client_type'].dropna().tolist()
    terms = pd.read_sql("SELECT DISTINCT term FROM screen", db)['term'].dropna().tolist()
    screen_types = pd.read_sql("SELECT DISTINCT screen_type FROM screen", db)['screen_type'].dropna().tolist()

    with st.sidebar.expander('FILTER OPTIONS', expanded=True):
        selected_client_type = st.selectbox("Client Type", client_types)
        selected_screen_type = st.selectbox("Screen Type", screen_types)
        selected_term = st.selectbox("Term", terms)

    # ✅ BULK MODE
    if selected_client_type == "Student" and bulk_mode:
        class_options = pd.read_sql("SELECT DISTINCT class FROM screen WHERE class IS NOT NULL", db)['class'].tolist()
        stream_options = pd.read_sql("SELECT DISTINCT stream FROM screen WHERE stream IS NOT NULL", db)['stream'].tolist()

        with st.form("bulk_tool_form"):
            col1, col2 = st.columns(2)
            selected_class = col1.selectbox("🎓 Filter by Class", ["All"] + class_options)
            selected_stream = col2.selectbox("🏞️ Filter by Stream", ["All"] + stream_options)
            query = """
                SELECT action_id, appointment_id, user_id, created_by, client_name
                FROM screen
                WHERE client_type = ? AND screen_type = ?
            """
            filters = [selected_client_type, selected_screen_type]
            if selected_class != "All":
                query += " AND class = ?"
                filters.append(selected_class)
            if selected_stream != "All":
                query += " AND stream = ?"
                filters.append(selected_stream)
            if selected_term != "All":
                query += " AND term = ?"
                filters.append(selected_term)

            all_matching = pd.read_sql(query, db, params=filters).dropna().values.tolist()

            name_to_row = {row[4]: row for row in all_matching}
            selected_names = col1.multiselect(f"Select Specific {selected_client_type}s", list(name_to_row.keys()))
            selected_rows = [name_to_row[name] for name in selected_names] if selected_names else list(name_to_row.values())

            tools_to_assign = col2.multiselect("🧰 Select Tools to Assign", tools_list)
            scheduled_date = col1.date_input("📅 Scheduled Date").strftime("%Y-%m-%d")
            assign_tools_btn = st.form_submit_button("✅ Assign Tools (Bulk)")

        # ✅ Now outside the form block, process if submit was clicked
        if assign_tools_btn:
            if not tools_to_assign:
                st.error("Select at least one tool to assign.")
            elif not selected_rows:
                st.warning("No records selected.")
            else:
                added, skipped = [], []
                for action_id, appointment_id, user_id, created_by, client_name in selected_rows:
                    a, s = assign_tools_to_screen(action_id, appointment_id, user_id, created_by, tools_to_assign, scheduled_date)
                    if a > 0: added.append(client_name)
                    if s > 0: skipped.append(client_name)

                if added:
                    st.success(f"✅ Tools assigned: {', '.join(added)}")
                if skipped:
                    st.warning(f"⚠️ Already assigned: {', '.join(skipped)}")
                send_notifications("Bulk Admin", ' & '.join(tools_to_assign), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # 🔄 Bulk Remove Tool
        existing_tools = set()
        for row in selected_rows:
            tools_df = fetch_screen_tools(row[1], db)
            if not tools_df.empty:
                existing_tools.update(tools_df['tool'].tolist())

        if existing_tools:
            with st.form("remove_tool_form"):
                col1, col2 = st.columns(2)
                to_remove = col2.selectbox("🗑️ Tool to Remove", sorted(existing_tools))
                remove_btn = st.form_submit_button("Remove Tool from Selected")

            if remove_btn:
                for row in selected_rows:
                    remove_requested_tool(db, row[0], row[1], to_remove)
                st.success(f"🧹 Removed '{to_remove}' from selected screens.")
        else:
            st.info("No tools currently assigned across selected.")

        
    if not bulk_mode:
        col1, col2 = st.columns([1.5, 2])
        username = st.session_state.get("user_name")
        if not client_types:
            st.warning("No screens available.")
            return
        with col1.expander(f'Search {selected_client_type}', expanded=True):
            search_input = st.text_input("Name or Appointment ID", key="search_input")
        results = []
        if search_input.strip():
            db = create_connection()
            results = fetch_screen_appointments_users(
                db,
                search_input,
                selected_screen_type=selected_screen_type,
                selected_term=selected_term)
        else:
            st.info("Please search and select a client to assign tools.")
        if results:
            options = [
                f"{row[3]} - {row[2]} - {row[7]}" 
                for row in results]
            current_appointment = st.session_state.get("appointment_id")
            if current_appointment not in [row[3] for row in results]:
                for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'action_id', 'class_', 'stream', 'created_by']:
                    st.session_state.pop(key, None)
            with st.sidebar.expander('Search results', expanded=True):
                st.write(f':orange[{len(options)} results for {search_input} found]')
                selected = st.selectbox("Select Matching Client Record", options, key="client_select")

            if selected:
                selected_row = results[options.index(selected)]
                if st.session_state.get("appointment_id") != selected_row[3]:
                    st.session_state.user_id = selected_row[1]
                    st.session_state.full_name = selected_row[2]
                    st.session_state.appointment_id = selected_row[3]
                    st.session_state.selected_term = selected_row[6]
                    st.session_state.selected_screen_type = selected_row[7]
                    st.session_state.action_id = selected_row[0]
                    st.session_state.class_ = selected_row[4]
                    st.session_state.stream = selected_row[5]
                    st.session_state.created_by = selected_row[8]
                    st.rerun()
        else:
            if search_input.strip():
                st.warning("No matching clients/appointments found.")
            for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'action_id', 'class_', 'stream', 'created_by']:
                st.session_state.pop(key, None)

        if st.session_state.get("user_id"):
            with st.sidebar.expander('Results', expanded=True):
                st.subheader("📋 Selected Client Details")
                st.markdown(f"""
                **👤 Name:** {st.session_state.full_name}  
                **🆔 User ID:** {st.session_state.user_id}  
                **📅 Appointment ID:** {st.session_state.appointment_id}  
                **📘 Term:** {st.session_state.selected_term}  
                **🧾 Screen Type:** {st.session_state.selected_screen_type}  
                **✍️ Created By:** {st.session_state.created_by}
                """)
                if selected_client_type == "Student":
                    st.markdown(f"""
                    **🏫 Class:** {st.session_state.get('class_', 'N/A')}  
                    **🌊 Stream:** {st.session_state.get('stream', 'N/A')}
                    """)

            with col2.form('Assign Tools'):
                tools_to_assign = st.multiselect("🧰 Select Tools", tools_list)
                scheduled_date = st.date_input("📅 Scheduled Date").strftime("%Y-%m-%d")

                if st.form_submit_button("✅ Assign Tools"):
                    if not tools_to_assign:
                        st.error("Please select tools to assign.")
                    else:
                        added, skipped = assign_tools_to_screen(
                            st.session_state.action_id,
                            st.session_state.appointment_id,
                            st.session_state.user_id,
                            st.session_state.created_by,
                            tools_to_assign,
                            scheduled_date,)
                        st.success(f"✅ Tools assigned: {added} | ⛔ Skipped: {skipped} (already pending)")
                        send_notifications(st.session_state.full_name, ' & '.join(tools_to_assign), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            with col1.form("remove_tool_form"):
                appointment_id = st.session_state.get("appointment_id")
                action_id = st.session_state.get("action_id")
                tools_in_db_df = fetch_screen_tools(appointment_id, db)
                if not tools_in_db_df.empty:
                    tools_in_db = tools_in_db_df['tool'].tolist()
                    tool_to_remove = st.selectbox("Select a Tool to Remove", tools_in_db)
                else:
                    st.warning(f'No assigned tools yet for {appointment_id}')
                    tool_to_remove = None 
                remove = st.form_submit_button(":red[Delete]")
                if remove and tool_to_remove:
                    remove_requested_tool(db, action_id, appointment_id, tool_to_remove)

        if st.checkbox('View Assigned Tools'):
            appointment_id = st.session_state.get("appointment_id")
            assigned_tools = fetch_screen_tools(appointment_id, db)
            if not assigned_tools.empty:
                st.dataframe(assigned_tools)
            else:
                st.warning(f'No assigned_tools on {appointment_id}')

    db.close()
if __name__ == "__main__":
    main()
