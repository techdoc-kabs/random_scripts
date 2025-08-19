DB_PATH = "users_db.db"
import streamlit as st
import pandas as pd
from datetime import datetime
from pushbullet import Pushbullet
import threading 
import smtplib
from email.message import EmailMessage
import sqlite3


API_KEY = st.secrets["push_API_KEY"]
pb = Pushbullet(API_KEY)

def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def create_requested_tools_students_table(db):
    cursor = db.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS requested_tools_students (
        appointment_id TEXT,
        student_id TEXT,
        term TEXT,
        screen_type TEXT,
        tool_name TEXT,
        requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tool_status TEXT DEFAULT 'Pending',
        PRIMARY KEY (appointment_id, student_id, tool_name)
    )
    """
    cursor.execute(create_table_query)
    db.commit()
    cursor.close()

def insert_requested_tools_students(db, student_id, appointment_id, term, screen_type, tools_to_add):
    cursor = db.cursor()
    insert_query = """
    INSERT INTO requested_tools_students (student_id, appointment_id, term, screen_type, tool_name)
    VALUES (?, ?, ?, ?, ?)
    """
    for tool in tools_to_add:
        values = (student_id, appointment_id, term, screen_type, tool)
        try:
            cursor.execute(insert_query, values)
        except sqlite3.IntegrityError:
            st.warning(f"Tool '{tool}' is already requested for Appointment ID {appointment_id}.")
    db.commit()
    cursor.close()

def fetch_requested_tools_df(db, student_id, appointment_id):
    cursor = db.cursor()
    fetch_query = """
    SELECT student_id, appointment_id, term, screen_type, tool_name, tool_status 
    FROM requested_tools_students 
    WHERE student_id = ? AND appointment_id = ?
    """
    cursor.execute(fetch_query, (student_id, appointment_id))
    result = cursor.fetchall()
    tools_df = pd.DataFrame(result, columns=['Student ID', 'Appointment ID', 'Term', 'Screen Type', 'Tool Name', 'Status'])
    cursor.close()
    return tools_df

def remove_requested_tool(db, student_id, appointment_id, tool_to_remove):
    cursor = db.cursor()
    delete_query = """
    DELETE FROM requested_tools_students WHERE student_id = ? AND appointment_id = ? AND tool_name = ?
    """
    cursor.execute(delete_query, (student_id, appointment_id, tool_to_remove))
    db.commit()
    cursor.close()
    st.success(f"The tool '{tool_to_remove}' was successfully removed.")

def fetch_appointments_for_student_and_id(db, student_id, appointment_id):
    query = """
    SELECT * FROM screen_appointments WHERE student_id = ? AND appointment_id = ?
    """
    cursor = db.cursor()
    cursor.execute(query, (student_id, appointment_id))
    appointments = cursor.fetchall()
    cursor.close()
    return appointments

def fetch_student_by_id(db, student_id):
    cursor = db.cursor()
    query = """
    SELECT student_id, name, age, gender, student_class, stream, username, contact, email 
    FROM student_users WHERE student_id = ?
    """
    cursor.execute(query, (student_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

def fetch_appointments_students(db, search_input, selected_term=None, selected_screen_type=None):
    cursor = db.cursor()
    if search_input.strip().upper().startswith("SCREEN-") or search_input.isdigit():
        query = """
        SELECT id, student_id, name, appointment_id, appointment_date, appointment_time, appointment_type, term, screen_type, clinician_name
        FROM screen_appointments WHERE appointment_id = ?
        """
        params = (search_input.strip(),)
    else:
        name_parts = search_input.strip().split()
        query_conditions = []
        params = []

        if len(name_parts) == 2:
            first_name, last_name = name_parts
            query_conditions.append("name LIKE ?")
            query_conditions.append("name LIKE ?")
            params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
        else:
            query_conditions.append("name LIKE ?")
            params.append(f"%{search_input}%")

        if selected_term:
            query_conditions.append("term = ?")
            params.append(selected_term)
        if selected_screen_type:
            query_conditions.append("screen_type = ?")
            params.append(selected_screen_type)

        query = f"""
        SELECT id, student_id, name, appointment_id, appointment_date, appointment_time, appointment_type, term, screen_type, clinician_name
        FROM screen_appointments
        WHERE {" AND ".join(query_conditions)}
        """
    query += " ORDER BY appointment_date DESC, appointment_time DESC"
    cursor.execute(query, tuple(params))
    appointments = cursor.fetchall()
    cursor.close()
    return appointments

def fetch_requested_tools_for_student(db, student_id):
    cursor = db.cursor()
    fetch_query = """
    SELECT 
        a.appointment_id, 
        su.student_id, 
        su.name AS student_name, 
        su.student_class, 
        su.stream, 
        a.term,
        a.screen_type,
        rt.tool_name, 
        rt.tool_status 
    FROM 
        requested_tools_students rt
    JOIN 
        screen_appointments a ON rt.appointment_id = a.appointment_id
    JOIN 
        student_users su ON a.student_id = su.student_id
    WHERE 
        su.student_id = ?
    """
    cursor.execute(fetch_query, (student_id,))
    result = cursor.fetchall()
    tools_df = pd.DataFrame(result, columns=['appointment_id', 'student_id', 'student_name', 'student_class', 'stream', 'term', 'screen_type', 'tool_name', 'tool_status'])
    cursor.close()
    return tools_df

def fetch_all_appointments_students(db):
    cursor = db.cursor()
    query = """SELECT student_id, name, appointment_id, screen_type, term FROM screen_appointments"""
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(result, columns=['student_id', 'name', 'appointment_id', 'screen_type', 'term']) if result else pd.DataFrame()

def fetch_filtered_appointments(db):
    cursor = db.cursor()
    query = """SELECT student_id, name, appointment_id, screen_type, term FROM screen_appointments"""
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(result, columns=['student_id', 'name', 'appointment_id', 'screen_type', 'term'])
    if df.empty:
        st.warning("No appointments found.")
        return df
    return df

def fetch_student_email_by_name(name):
    conn = create_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        query = "SELECT email FROM student_users WHERE name = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def fetch_student_contact_by_name(name):
    conn = create_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        query = "SELECT contact FROM student_users WHERE name = ?"
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
    student_email = fetch_student_email_by_name(name)
    
    if student_email:
        send_email_notification(name, tools, date, student_email)
    phone_number = fetch_student_contact_by_name(name)
    if phone_number:
        send_sms_notification(phone_number, message)




def display_functioning_questionnaire(db, appointment_id, student_id):
    completed_response = check_functioning_completed(db, appointment_id)
    if completed_response:
        st.success(f"Functioning completed ✅")
    else:
        st.info("If you checked off any problems, how difficult have these problems made it for you?")
        difficulty_level = st.radio(
            "Choose difficulty level:",
            ('Not difficult at all', 'Somewhat difficult', 'Very difficult', 'Extremely difficult')
        )

        if st.button("Submit Functioning Response"):
            success = insert_functioning_response(db, appointment_id, student_id, difficulty_level)
            if success:
                st.success("Functioning response recorded successfully ✅!")
                st.rerun() 


def check_functioning_completed(db, appointment_id):
    cursor = db.cursor()
    query = "SELECT difficulty_level FROM functioning_responses WHERE appointment_id = ?"
    cursor.execute(query, (appointment_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

def insert_functioning_response(db, appointment_id, student_id, difficulty_level):
    cursor = db.cursor()
    insert_query = """
    INSERT INTO functioning_responses (appointment_id, student_id, difficulty_level)
    VALUES (?, ?, ?)
    """
    try:
        cursor.execute(insert_query, (appointment_id, student_id, difficulty_level))
        db.commit()
        return True
    except Exception as err:
        st.error(f"Error inserting response: {err}")
        return False
    finally:
        cursor.close()   

# ###### DRIVER CODE ######
# def main():
#     db = create_connection()
#     create_requested_tools_students_table(db)
#     if 'appointment_id' in st.session_state:
#         appointment_id = st.session_state.appointment_id
#     if 'student_id' in st.session_state:
#         student_id = st.session_state.student_id
    
#     if 'clinician_name' in st.session_state:
#         clinician_name = st.session_state.clinician_name
    
#     if 'selected_term' in st.session_state:
#         selected_term = st.session_state.selected_term

#     if 'selected_screen_type' in st.session_state:
#         selected_screen_type = st.session_state.selected_screen_type     
        
   
#         student_name = st.session_state.get('student_name')
#         if not student_name and 'student_id' in st.session_state:
#             student_row = fetch_student_by_id(db, st.session_state.student_id)
#             if student_row:
#                 student_name = student_row['name']
#                 st.session_state.student_name = student_name 
#                 appointments = fetch_appointments_for_student_and_id(db, student_id, appointment_id)
#                 tools = ['PHQ-4','PHQ-9', 'GAD-7','DASS-21', 'SRQ', 'BDI', 'CAGE', 'SAD PERSONS SCALE']
#                 tools_for_student_df = fetch_requested_tools_for_student(db, student_id)
#                 tools_in_db_df = fetch_requested_tools_df(db, student_id, appointment_id)
#                 tools_in_appointment = dict(zip(tools_in_db_df['Tool Name'], tools_in_db_df['Status']))
#                 tools_for_student = dict(zip(tools_for_student_df['tool_name'], tools_for_student_df['tool_status']))
#                 col1, col2 = st.columns(2)
#                 with col1.form("tool_form"):
#                     selected_tools = st.multiselect("Render Tool", tools)
#                     add = st.form_submit_button(":green[Add]")
#                     if add:
#                         tools_to_add = []
#                         blocked_tools = []
#                         pre_screen_exists = any(
#                             (row['student_id'] == student_id and  
#                              row['term'] == selected_term and 
#                              row['screen_type'] == 'PRE-SCREEN' and  
#                              row['tool_status'] == 'Completed')  # ✅ Fix: Ensure "Completed" status
#                             for _, row in tools_for_student_df.iterrows())
#                         st.write(f"🔍 Debug: PRE-SCREEN Exists? {pre_screen_exists}")  # Debugging
#                         for tool in selected_tools:
#                             if tool in tools_in_appointment:
#                                 blocked_tools.append(f"{tool} (Already exists on {appointment_id})")
#                             elif tool in tools_for_student and tools_for_student[tool] == "Pending":
#                                 blocked_tools.append(f"{tool} is still pending on a previous appointment")
#                             elif selected_screen_type == 'POST-SCREEN' and not pre_screen_exists:
#                                 blocked_tools.append(f"{tool} cannot be added to POST-SCREEN without a PRE-SCREEN in this term")
#                             else:
#                                 tools_to_add.append(tool)
#                         if blocked_tools:
#                             st.warning(f"Can't add: {', '.join(blocked_tools)}")
#                         if tools_to_add:
#                             if not student_name:
#                                 student_row = fetch_student_by_id(db, student_id)
#                                 if student_row:
#                                     student_name = student_row['name']
#                                     st.session_state.student_name = student_name

#                             insert_requested_tools_students(db, student_id, appointment_id, selected_term, selected_screen_type, tools_to_add)
#                             st.success(f"Requested {', '.join(tools_to_add)} for {appointment_id} as a {selected_screen_type}")
                            
#                             send_notifications(student_name, ' & '.join(tools_to_add), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
#                             tools_in_db_df = fetch_requested_tools_df(db, student_id, appointment_id)
#                             tools_in_appointment = dict(zip(tools_in_db_df['Tool Name'], tools_in_db_df['Status']))
                

#                 with st.expander(f'SCREEN HISTORY FOR - {student_id}', expanded=True):
#                     df = fetch_requested_tools_for_student(db, student_id)
#                     df.index = df.index + 1
#                     st.write(df[['appointment_id', 'student_class', 'term', 'screen_type', 'tool_name', 'tool_status']])
#                 with col2.form("remove_tool_form"):
#                     tools_in_db = tools_in_db_df['Tool Name'].tolist()
#                     if tools_in_db:
#                         tool_to_remove = st.selectbox("Select a Tool to Remove", tools_in_db)
#                         remove = st.form_submit_button(":red[Delete]")
#                         if remove:
#                             remove_requested_tool(db, student_id, appointment_id, tool_to_remove)
#                             tools_in_db_df = fetch_requested_tools_df(db, student_id, appointment_id)
#     db.close()
# if __name__ == "__main__":
#     main()

def main():
    db = create_connection()
    create_requested_tools_students_table(db)

    # STEP 1: If session_state not populated, show search UI
    if not all(k in st.session_state for k in ['student_id', 'appointment_id', 'selected_term', 'selected_screen_type']):
        st.subheader("🔍 Search Student Appointment")
        search_input = st.text_input("Enter student name or Appointment ID")

        if search_input:
            matching = fetch_appointments_students(db, search_input)
            if matching:
                options = [
                    f"{row['appointment_id']} | {row['name']} | {row['term']} | {row['screen_type']}"
                    for row in matching
                ]
                selected = st.selectbox("Select Appointment", options)
                if selected:
                    selected_row = matching[options.index(selected)]
                    st.session_state.student_id = selected_row['student_id']
                    st.session_state.student_name = selected_row['name']
                    st.session_state.appointment_id = selected_row['appointment_id']
                    st.session_state.selected_term = selected_row['term']
                    st.session_state.selected_screen_type = selected_row['screen_type']
                    st.rerun()
            else:
                st.warning("No matching appointment found.")
        db.close()
        return  # ⛔ Stop here if no student selected yet

    # STEP 2: Normal flow once student & appointment are set
    appointment_id = st.session_state.appointment_id
    student_id = st.session_state.student_id
    clinician_name = st.session_state.get('clinician_name', 'Unknown')
    selected_term = st.session_state.selected_term
    selected_screen_type = st.session_state.selected_screen_type
    student_name = st.session_state.get('student_name')

    if not student_name:
        student_row = fetch_student_by_id(db, student_id)
        if student_row:
            student_name = student_row['name']
            st.session_state.student_name = student_name

    appointments = fetch_appointments_for_student_and_id(db, student_id, appointment_id)
    tools = ['PHQ-4', 'PHQ-9', 'GAD-7', 'DASS-21', 'SRQ', 'BDI', 'CAGE', 'SAD PERSONS SCALE']
    tools_for_student_df = fetch_requested_tools_for_student(db, student_id)
    tools_in_db_df = fetch_requested_tools_df(db, student_id, appointment_id)
    tools_in_appointment = dict(zip(tools_in_db_df['Tool Name'], tools_in_db_df['Status']))
    tools_for_student = dict(zip(tools_for_student_df['tool_name'], tools_for_student_df['tool_status']))

    col1, col2 = st.columns(2)
    with col1.form("tool_form"):
        selected_tools = st.multiselect("Render Tool", tools)
        add = st.form_submit_button(":green[Add]")
        if add:
            tools_to_add = []
            blocked_tools = []
            pre_screen_exists = any(
                (row['student_id'] == student_id and
                 row['term'] == selected_term and
                 row['screen_type'] == 'PRE-SCREEN' and
                 row['tool_status'] == 'Completed')
                for _, row in tools_for_student_df.iterrows()
            )
            st.write(f"🔍 Debug: PRE-SCREEN Exists? {pre_screen_exists}")
            for tool in selected_tools:
                if tool in tools_in_appointment:
                    blocked_tools.append(f"{tool} (Already exists on {appointment_id})")
                elif tool in tools_for_student and tools_for_student[tool] == "Pending":
                    blocked_tools.append(f"{tool} is still pending on a previous appointment")
                elif selected_screen_type == 'POST-SCREEN' and not pre_screen_exists:
                    blocked_tools.append(f"{tool} cannot be added to POST-SCREEN without a PRE-SCREEN in this term")
                else:
                    tools_to_add.append(tool)

            if blocked_tools:
                st.warning(f"Can't add: {', '.join(blocked_tools)}")
            if tools_to_add:
                insert_requested_tools_students(db, student_id, appointment_id, selected_term, selected_screen_type, tools_to_add)
                st.success(f"Requested {', '.join(tools_to_add)} for {appointment_id} as a {selected_screen_type}")
                send_notifications(student_name, ' & '.join(tools_to_add), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                tools_in_db_df = fetch_requested_tools_df(db, student_id, appointment_id)
                tools_in_appointment = dict(zip(tools_in_db_df['Tool Name'], tools_in_db_df['Status']))

    with st.expander(f'SCREEN HISTORY FOR - {student_id}', expanded=True):
        df = fetch_requested_tools_for_student(db, student_id)
        df.index = df.index + 1
        st.write(df[['appointment_id', 'student_class', 'term', 'screen_type', 'tool_name', 'tool_status']])

    with col2.form("remove_tool_form"):
        tools_in_db = tools_in_db_df['Tool Name'].tolist()
        if tools_in_db:
            tool_to_remove = st.selectbox("Select a Tool to Remove", tools_in_db)
            remove = st.form_submit_button(":red[Delete]")
            if remove:
                remove_requested_tool(db, student_id, appointment_id, tool_to_remove)
                tools_in_db_df = fetch_requested_tools_df(db, student_id, appointment_id)

    # Optional reset button
    # if st.button("🔁 Search Another Student"):
    #     for k in ['student_id', 'student_name', 'appointment_id', 'selected_term', 'selected_screen_type']:
    #         st.session_state.pop(k, None)
    #     st.rerun()

    db.close()

if __name__ == "__main__":
    main()
