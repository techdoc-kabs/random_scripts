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
import session_notes
def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

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



def fetch_appointment_details(db, appointment_id):
    cursor = db.cursor()
    query = """
    SELECT 
        a.appointment_id,
        a.user_id,
        u.full_name,
        u.age,
        u.sex,
        a.client_type,
        a.appointment_type,
        u.class,
        u.stream,
        a.created_at,
        a.assigned_therapist
    FROM appointments a
    JOIN users u ON a.user_id = u.user_id
    WHERE a.appointment_id = ?
    """
    cursor.execute(query, (appointment_id,))
    row = cursor.fetchone()
    return dict(row) if row else None




def main(appointment_id):
    db = create_connection()
    set_full_page_background('images/black_strip.jpg')

    appointment_id = st.session_state.get('appointment_id')

    selected_record = fetch_appointment_details(db, appointment_id)
    if not selected_record:
        st.error("⚠️ Appointment not found.")
        db.close()
        return

    def format_line(label, value):
        return f"<div style='margin-bottom:6px;'><span style='color:#c0392b; font-weight:bold;'>{label}:</span> <span style='color:#27ae60;'>{value}</span></div>"

    with st.sidebar.expander('CLIENT', expanded=True):
        profile_fields = [
            ("User ID", selected_record.get('user_id', 'N/A')),
            ("Appointment ID", appointment_id),
            ("Name", selected_record.get('full_name', 'N/A')),
            ("Age", selected_record.get('age', 'N/A')),
            ("Gender", selected_record.get('sex', 'N/A')),
            ("Client_Type", selected_record.get('client_type', 'N/A')),
            ("Class", selected_record.get('class', 'N/A')),
            ("Stream", selected_record.get('stream', 'N/A')),
            ("Appointment Date", selected_record.get('created_at', 'N/A')),
            ("Therapist", selected_record.get('assigned_therapist', 'N/A')),
        ]
        profile_html = ''.join([format_line(label, value) for label, value in profile_fields])
        st.markdown(profile_html, unsafe_allow_html=True)

    st.session_state["user_id"] = selected_record["user_id"]

    
    tabs = st.tabs(['Notes', 'Results'])
    with tabs[0]:
    # if file_menu == 'Session_notes':
        notes = fetch_session_notes(db, appointment_id)
        if notes:
            display_session_notes(notes)
        else:
            st.warning(f'📝 No clinical notes found for {appointment_id}.')
    with tabs[1]:
    # elif file_menu == 'Screen_results':
        import screen_results
        screen_results.main()

    db.close()

if __name__ == "__main__":
    appointment_id = st.session_state.get("appointment_id", "").strip()
    main(appointment_id)
