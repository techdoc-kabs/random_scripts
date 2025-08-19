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

# def alter_screen_table_add_tools_columns():
#     conn = create_connection()
#     cursor = conn.cursor()
#     try: cursor.execute("ALTER TABLE screen ADD COLUMN tools TEXT DEFAULT '[]'")
#     except sqlite3.OperationalError: pass
#     try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_statuses TEXT DEFAULT '{}'")
#     except sqlite3.OperationalError: pass
#     try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_scheduled_dates TEXT DEFAULT '{}'")
#     except sqlite3.OperationalError: pass
#     try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_response_dates TEXT DEFAULT '{}'")
#     except sqlite3.OperationalError: pass
#     try: cursor.execute("ALTER TABLE screen ADD COLUMN tools_responses TEXT DEFAULT '{}'")  # 🆕 New
#     except sqlite3.OperationalError: pass
#     try: cursor.execute("ALTER TABLE screen ADD COLUMN screen_type TEXT DEFAULT 'PRE-SCREEN'")  # ✅ Add this
#     except sqlite3.OperationalError: pass
#     conn.commit()
#     conn.close()


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
# def assign_tools_to_screen(appointment_id, user_id, created_by, tools_to_assign, scheduled_date):
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT tools, tools_statuses, tools_scheduled_dates, tools_response_dates, tools_responses FROM screen WHERE appointment_id = ?", (appointment_id,))
#     row = cursor.fetchone()
#     if row:
#         current_tools = json.loads(row[0]) if row[0] else []
#         current_statuses = json.loads(row[1]) if row[1] else {}
#         current_scheduled = json.loads(row[2]) if row[2] else {}
#         current_response = json.loads(row[3]) if row[3] else {}

#         new_tools_added = 0
#         skipped_tools = 0

#         for tool in tools_to_assign:
#             if tool in current_tools:
#                 skipped_tools += 1
#                 continue  # Don't reassign if already exists on this appointment_id
#             current_tools.append(tool)
#             current_statuses[tool] = 'Pending'
#             current_scheduled[tool] = scheduled_date
#             current_response[tool] = None
#             new_tools_added += 1

#         cursor.execute("""
#             UPDATE screen SET
#                 tools = ?, tools_statuses = ?, tools_scheduled_dates = ?, tools_response_dates = ?
#             WHERE appointment_id = ?
#         """, (
#             json.dumps(current_tools),
#             json.dumps(current_statuses),
#             json.dumps(current_scheduled),
#             json.dumps(current_response),
#             appointment_id
#         ))
#         conn.commit()
#         conn.close()
#         return new_tools_added, skipped_tools
#     else:
#         tools_statuses = {tool: 'Pending' for tool in tools_to_assign}
#         tools_scheduled_dates = {tool: scheduled_date for tool in tools_to_assign}
#         tools_response_dates = {tool: None for tool in tools_to_assign}
#         cursor.execute("""
#             INSERT INTO screen (
#                 appointment_id, appointment_id, user_id, created_by,
#                 tools, tools_statuses, tools_scheduled_dates, tools_response_dates
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             appointment_id,
#             user_id,
#             created_by,
#             json.dumps(tools_to_assign),
#             json.dumps(tools_statuses),
#             json.dumps(tools_scheduled_dates),
#             json.dumps(tools_response_dates)
#         ))
#         conn.commit()
#         conn.close()
#         return len(tools_to_assign), 0


import sqlite3

import json
import streamlit as st

def assign_tools_to_screen(appointment_id, user_id, created_by, tools_to_assign, scheduled_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT screening_tools FROM appointments WHERE appointment_id = ?", (appointment_id,))
    row = cursor.fetchone()

    if row:
        existing = json.loads(row[0]) if row[0] else {}
        new_tools_added = 0
        skipped_tools = 0

        for tool in tools_to_assign:
            if tool in existing:
                skipped_tools += 1
                continue
            existing[tool] = {
                "status": "Pending",
                "scheduled_date": scheduled_date,
                "response_date": None,
                "response": None,
                "assigned_by": created_by
            }
            new_tools_added += 1

        # Update the existing appointment
        cursor.execute("""
            UPDATE appointments
            SET screening_tools = ?
            WHERE appointment_id = ?
        """, (json.dumps(existing), appointment_id))
        conn.commit()
        conn.close()
        return new_tools_added, skipped_tools

    else:
        # Appointment not found
        st.error(f"No appointment found with ID: {appointment_id}")
        conn.close()
        return 0, 0





def initialize_session_vars():
    defaults = {
        'appointment_id': None,
        'user_id': None,
        'name': None,
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



def fetch_screen_tools(appointment_id, db):
    cursor = db.cursor()
    cursor.execute("""
        SELECT appointment_id, name, screen_type, class, stream, term, client_type,
               screening_tools
        FROM appointments
        WHERE screening_tools IS NOT NULL AND screening_tools != ''
              AND appointment_id = ?
    """, (appointment_id,))
    screens = cursor.fetchall()
    cursor.close()

    records = []
    for row in screens:
        (
            appointment_id,
            name,
            screen_type,
            class_,
            stream,
            term,
            client_type,
            screening_tools_raw
        ) = row

        try:
            tools_data = json.loads(screening_tools_raw)
        except Exception as e:
            st.warning(f"Failed to parse screening_tools for appointment {appointment_id}: {e}")
            tools_data = {}

        for tool_name, tool_info in tools_data.items():
            records.append({
                "appointment_id": appointment_id,
                "name": name,
                "screen_type": screen_type,
                "class": class_,
                "stream": stream,
                "term": term,
                "client_type": client_type,
                "tool": tool_name,
                "status": tool_info.get("status", "Pending"),
                "scheduled_date": tool_info.get("scheduled_date"),
                "response_date": tool_info.get("response_date"),
                "response": tool_info.get("response")
            })

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



def remove_requested_tool(db, appointment_id, tool_to_remove):
    cursor = db.cursor()
    cursor.execute("""
        SELECT screening_tools
        FROM appointments
        WHERE appointment_id = ?
    """, (appointment_id,))
    result = cursor.fetchone()

    if not result:
        st.error("No matching record found.")
        return

    try:
        tools_data = json.loads(result[0]) if result[0] else {}
    except Exception as e:
        st.error(f"Error parsing screening_tools: {e}")
        return

    if tool_to_remove not in tools_data:
        st.warning(f"Tool '{tool_to_remove}' not found.")
        return

    if tools_data[tool_to_remove].get("status") == "Completed":
        st.warning(f"Tool '{tool_to_remove}' is marked as Completed and cannot be removed.")
        return

    # Remove the tool
    tools_data.pop(tool_to_remove)

    # Save the updated JSON back
    cursor.execute("""
        UPDATE appointments
        SET screening_tools = ?
        WHERE appointment_id = ?
    """, (json.dumps(tools_data), appointment_id))

    db.commit()
    cursor.close()
    st.success(f"✅ Tool '{tool_to_remove}' was successfully removed.")



def screen_type_exists_for_appointment(db, appointment_id, screen_type):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 1 FROM appointments
        WHERE appointment_id = ? AND screen_type = ?
        LIMIT 1
    """, (appointment_id, screen_type))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists

def is_pre_screen_completed(db, appointment_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT status FROM appointments
        WHERE appointment_id = ? AND screen_type = 'PRE-SCREEN'
    """, (appointment_id,))
    row = cursor.fetchone()
    cursor.close()
    return row and row[0] == "Completed"


def get_available_screen_types(db, appointment_id):
    used_types = pd.read_sql("SELECT DISTINCT screen_type FROM appointments WHERE appointment_id = ?", db, params=[appointment_id])['screen_type'].tolist()
    possible = ["PRE-SECREEN", "POST-SCREEN",'ON-CONSULT','ON-REQUEST']  # or dynamic from DB
    return [s for s in possible if s not in used_types]


def get_full_name_from_username(username):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
      # <-- ensures dictionary-like access
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None




def main():
    set_full_page_background('images/black_strip.jpg')
    # alter_screen_table_add_tools_columns()
    db = create_connection()
    # bulk_mode = st.toggle("Bulk Assign Mode", value=True)
    tools_list = ["PHQ-4", "PHQ-9", "GAD-7", 'CAPS-14','SSQ ','HSQ', 'SNAP-IV-C',"DASS-21", 'BDI', "SRQ"]
    screen_types = ['ON-CONSULT','ON-REQUEST']
    col1, col2 = st.columns([1.5, 2])
    username = st.session_state.get("user_name")
    created_by = get_full_name_from_username(username)
    st.write(created_by)
    

    appointment = st.session_state.get("appointment_id")
    with col2.form('Assign Tools'):
        tools_to_assign = st.multiselect("🧰 Select Tools", tools_list)
        scheduled_date = st.date_input("📅 Scheduled Date").strftime("%Y-%m-%d")
        if st.form_submit_button("✅ Assign Tools"):
            if not tools_to_assign:
                st.error("Please select tools to assign.")
            else:
                added, skipped = assign_tools_to_screen(
                    # st.session_state.action_id,
                    st.session_state.appointment_id,
                    st.session_state.user_id,
                    created_by,
                    tools_to_assign,
                    scheduled_date,)
                st.success(f"✅ Tools assigned: {added} | ⛔ Skipped: {skipped} (already pending)")
                send_notifications(st.session_state.full_name, ' & '.join(tools_to_assign), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    with col1.form("remove_tool_form"):
        appointment_id = st.session_state.get("appointment_id")
        # action_id = st.session_state.get("action_id")
        tools_in_db_df = fetch_screen_tools(appointment_id, db)
        if not tools_in_db_df.empty:
            tools_in_db = tools_in_db_df['tool'].tolist()
            tool_to_remove = st.selectbox("Select a Tool to Remove", tools_in_db)
        else:
            st.warning(f'No assigned tools yet for {appointment_id}')
            tool_to_remove = None 
        remove = st.form_submit_button(":red[Delete]")
        if remove and tool_to_remove:
            remove_requested_tool(db, appointment_id, tool_to_remove)

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
