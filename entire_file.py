DB_PATH = "users_db.db"
import streamlit as st
import json
import pandas as pd
import os
# import requested_tools
from datetime import datetime
import seaborn as sns
import sqlite3

import screen_results
from streamlit_javascript import st_javascript
from streamlit_option_menu import option_menu
import base64

def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None
def fetch_users(db, search_input):
    cursor = db.cursor()
    if search_input.strip().upper().startswith("STUD-") or search_input.isdigit():
        query = """
        SELECT user_id, full_name, age, sex, class, stream
        FROM users
        WHERE user_id = ?
        """
        cursor.execute(query, (search_input.strip(),))
    else: 
        name_parts = search_input.strip().split()
        query_conditions = []
        params = []

        if len(name_parts) == 2:
            first_name, last_name = name_parts
            query_conditions.append("full_name LIKE ?")
            query_conditions.append("full_name LIKE ?")
            params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
        else:
            query_conditions.append("full_name LIKE ?")
            params.append(f"%{search_input}%")
        query = f"""
        SELECT user_id, full_name, age, sex, class, stream
        FROM users
        WHERE {" OR ".join(query_conditions)}
        """
        cursor.execute(query, tuple(params))
    return cursor.fetchall()

def fetch_appointments_for_student(db, user_id):
    cursor = db.cursor()
    query = """
    SELECT appointment_id,user_id, name, appointment_type, created_at
    FROM appointments
    WHERE user_id = ?
    """
    cursor.execute(query, (user_id,))
    appointments = cursor.fetchall()
    return appointments


def fetch_session_notes(db, appointment_id):
    cursor = db.cursor()
    query = """
    SELECT * FROM session_notes WHERE appointment_id = ?
    """
    cursor.execute(query, (appointment_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

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

def display_session_notes(note):
    st.markdown("""
        <style>
            .preview-container {
                background-color: #EAEAEA;
                border: 2px solid #B0B0B0;
                padding: 15px;
                border-radius: 20px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
                margin-bottom: 15px;
                max-width: 100%;
                box-sizing: border-box;
            }
            .header {
                font-family: 'Times New Roman', serif;
                font-size: 22px;
                font-weight: bold;
                color: #222;
                margin-bottom: 15px;
                text-align: center;
            }
            .line {
                display: flex;
                flex-direction: row;
                flex-wrap: wrap;
                margin-bottom: 12px;
            }
            .label, .text {
                font-family: 'Times New Roman', serif;
                font-size: 16px;
                font-style: italic;
                line-height: 1.4;
            }
            .label {
                font-weight: bold;
                color: #0056b3;
                width: 180px;
                min-width: 120px;
                margin-right: 10px;
                flex-shrink: 0;
            }
            .text {
                color: #333;
                flex-grow: 1;
                word-break: break-word;
            }

            /* Force mobile layout stack on small screens */
            @media only screen and (max-width: 700px) {
                .line {
                    flex-direction: column;
                }
                .label, .text {
                    width: 100% !important;
                    margin: 0 0 5px 0;
                }
            }
        </style>
    """, unsafe_allow_html=True)

    appointment_date = note.get("appointment_date", "N/A")
    appointment_time = note.get("appointment_time", "N/A")
    try:
        formatted_time = datetime.strptime(appointment_time, "%H:%M:%S").strftime("%H:%M")
    except:
        formatted_time = appointment_time

    st.markdown(f"""
        <div class="preview-container">
            <div class="header">📌 SESSION NOTES</div>
            <div class="line"><span class="label">🕐 Date & Time:</span><span class="text">{appointment_date} at {formatted_time}</span></div>
            <div class="line"><span class="label">🗨️ Current Concerns:</span><span class="text">{note.get('current_concerns')}</span></div>
            <div class="line"><span class="label">🧾 Case Summary:</span><span class="text">{note.get('case_summary')}</span></div>
            <div class="line"><span class="label">🧠 Working Diagnosis:</span><span class="text">{note.get('working_diagnosis')}</span></div>
            <div class="line"><span class="label">🧩 Intervention:</span><span class="text">{note.get('intervention')}</span></div>
            <div class="line"><span class="label">📅 Follow-Up:</span><span class="text">{note.get('follow_up')}</span></div>
            <div class="line"><span class="label">🔁 Referral Plan:</span><span class="text">{note.get('refer')}</span></div>
            <div class="line"><span class="label">📝 Remarks:</span><span class="text">{note.get('remarks')}</span></div>
            <div class="line"><span class="label">👤 Clinician:</span><span class="text">{note.get('clinician_name')}</span></div>
        </div>
    """, unsafe_allow_html=True)

def main():
    db = create_connection()
    set_full_page_background('images/black_strip.jpg')
    # # Session state defaults
    st.session_state.setdefault("user_id", "")
    st.session_state.setdefault("appointment_id", "")
    device_width = st_javascript("window.innerWidth", key="file_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    # Search student
    container = st.sidebar if not is_mobile else st
    container.subheader("STUDENT DETAILS")
    with container.expander("🔍SEARCH", expanded=True):
        search_input = st.text_input("Enter Name or Student ID", "")
    results = fetch_users(db, search_input) if search_input.strip() else []

    selected_record = None
    if results:
        # Selection dropdown
        selection_container = st.sidebar if not is_mobile else st
        with selection_container.expander("Select", expanded=True):
            st.write(f"**{len(results)} result(s) found**")
            options = {f"{r['full_name']} - {r['user_id']}": r for r in results}
            selected_option = st.selectbox("Select a record:", list(options.keys()))
            selected_record = options[selected_option]

    if selected_record:
        # Show profile
        def format_line(label, value):
            return f"<div style='margin-bottom:6px;'><span style='color:#c0392b; font-weight:bold;'>{label}:</span> <span style='color:#27ae60;'>{value}</span></div>"

        profile_fields = [
            ("Student ID", selected_record['user_id']),
            ("Name", selected_record['full_name']),
            ("Age", f"{selected_record['age']} Years"),
            ("Gender", selected_record['sex']),
            ("Class", selected_record['class']),
            ("Stream", selected_record['stream']),
        ]
        profile_html = ''.join([format_line(label, value) for label, value in profile_fields])

        profile_container = st.sidebar if not is_mobile else st
        with profile_container.expander("STUDENT PROFILE", expanded=True):
            st.markdown(profile_html, unsafe_allow_html=True)
        st.session_state["user_id"] = selected_record["user_id"]
        user_id = st.session_state["user_id"]
        file_menu = option_menu(
            menu_title='',
            orientation='horizontal',
            menu_icon='',
            options=['Session_notes', 'Screen_results'],
            icons=["book", "pencil-square"],
            styles={
                "container": {"padding": "8!important", "background-color": "black", "border": "2px solid red"},
                "icon": {"color": "red", "font-size": "17px"},
                "nav-link": {
                    "color": "#d7c4c1", "font-size": "17px", "font-weight": "bold",
                    "text-align": "left", "--hover-color": "#d32f2f"
                },
                "nav-link-selected": {"background-color": "green"},
            },
            key="file_menu"
        )
        appointments = fetch_appointments_for_student(db, user_id)
        if file_menu == 'Session_notes' and appointments:
            for idx, appointment in enumerate(appointments, start=1):
                appointment_id = appointment[0]
                appointment_date = appointment[4]
                with st.expander(f'📅 :blue[[{idx}]] :orange[{selected_record["full_name"]}] - :red[{appointment_id}] - :green[{appointment_date}]', expanded=False):
                    notes = fetch_session_notes(db, appointment_id)
                    if notes:
                        display_session_notes(notes)
                    else:
                        st.warning('No clinical notes')

        elif file_menu == 'Screen_results' and appointments:
               # for appointment in appointments:
                for idx, appointment in enumerate(appointments, start=1):
                    appointment_id = appointment[0]
                    appointment_date = appointment[4]
                    with st.expander(f'📅 :blue[[{idx}]] :orange[{selected_record["full_name"]}] - :red[{appointment_id}] - :green[{appointment_date}]', expanded=False):

                        st.session_state["appointment_id"] = appointment_id
                        
                        screen_results.main()


    db.close()

if __name__ == "__main__":
    main()


