DB_PATH = "users_db.db"
import streamlit as st
from datetime import datetime
import sqlite3

import json
import streamlit as st
from typing import Dict
import pandas as pd
import json
import sqlite3

from streamlit_option_menu import option_menu
from typing import List, Dict

def display_session_notes(note):
    st.markdown("""
        <style>
            .preview-container {
                background-color: #EAEAEA;
                border: 2px solid #B0B0B0;
                padding: 15px;IYI
                border-radius: 20px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
                margin-bottom: 15px;
                max-width: 100%;
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
                flex-wrap: wrap;
                margin-bottom: 10px;
            }
            .label {
                font-family: 'Times New Roman', serif;
                font-size: 16px;
                font-weight: bold;
                color: #0056b3;
                font-style: italic;
                flex: 0 0 180px;
                margin-right: 10px;
            }
            .text {
                font-family: 'Times New Roman', serif;
                font-size: 16px;
                color: #333;
                font-style: italic;
                flex: 1;
                word-break: break-word;
            }

            @media screen and (max-width: 600px) {
                .label {
                    flex: 0 0 100%;
                    margin-bottom: 5px;
                }
                .text {
                    flex: 0 0 100%;
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
            <div class="header">📌 SESSION NOTE PREVIEW</div>
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
            unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error setting background: {e}")

def create_session_notes_table(db):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS session_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id TEXT,
        appointment_date TEXT,
        appointment_time TEXT,
        current_concerns TEXT,
        case_summary TEXT,
        working_diagnosis TEXT,
        intervention TEXT,
        follow_up TEXT,
        refer TEXT,
        remarks TEXT,
        clinician_name TEXT);
    """
    cursor = db.cursor()
    cursor.execute(create_table_sql)
    db.commit()


def insert_session_note(db, appointment_id, note_data: Dict, clinician_name):
    cursor = db.cursor()
    check_sql = "SELECT COUNT(*) FROM session_notes WHERE appointment_id = ?"
    cursor.execute(check_sql, (appointment_id,))
    existing_count = cursor.fetchone()[0]
    if existing_count > 0:
        return {"success": False, "message": f"Session notes already exist for appointment {appointment_id}"}

    appointment_time_str = note_data.get('appointment_time').strftime('%H:%M:%S')
    sql = """
    INSERT INTO session_notes (
        appointment_id,
        appointment_date,
        appointment_time,
        current_concerns,
        case_summary,
        working_diagnosis,
        intervention,
        follow_up,
        refer,
        remarks,
        clinician_name
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    """
    cursor.execute(sql, (
        appointment_id,
        note_data.get('appointment_date'),
        appointment_time_str,
        note_data.get('current_concerns'),
        note_data.get('case_summary'),
        note_data.get('working_diagnosis'),
        note_data.get('intervention'),
        note_data.get('follow_up'),
        note_data.get('refer'),
        note_data.get('remarks'),
        clinician_name
    ))
    db.commit()
    return {"success": True, "message": "Session note successfully saved!", "note_id": cursor.lastrowid}

def fetch_session_notes(db, appointment_id):
    cursor = db.cursor()
    query = """
    SELECT * FROM session_notes WHERE appointment_id = ?
    """
    cursor.execute(query, (appointment_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def update_session_note(conn, appointment_id, updated_note):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE session_notes
            SET
                appointment_date = ?,
                appointment_time = ?,
                current_concerns = ?,
                case_summary = ?,
                working_diagnosis = ?,
                intervention = ?,
                follow_up = ?,
                refer = ?,
                remarks = ?,
                clinician_name = ?
            WHERE appointment_id = ?
        ''', (
            updated_note["appointment_date"],
            updated_note["appointment_time"],
            updated_note["current_concerns"],
            updated_note["case_summary"],
            updated_note["working_diagnosis"],
            updated_note["intervention"],
            updated_note["follow_up"],
            updated_note["refer"],
            updated_note["remarks"],
            updated_note["clinician_name"],
            appointment_id
        ))
        conn.commit()
        return {"success": True, "message": "Note updated"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def fetch_all_therapists():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT DISTINCT full_name
            FROM users
            WHERE role = 'Therapist'
            ORDER BY full_name
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        st.error(f"Error fetching therapists: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

import os, base64

def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None

###### FOLLOW UP SCETION #####
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
      # ✅ Enables dictionary-like access
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



def main():
    db = create_connection()
    create_session_notes_table(db)
    create_follow_ps_table(db)
    username = st.session_state.get("user_name")
    therapist_name = get_full_name_from_username(username)
    set_full_page_background('images/black_strip.jpg')
    if "appointment_id" in st.session_state:
        appointment_id = st.session_state["appointment_id"]

    therapists = fetch_all_therapists()
    col1, col2 = st.columns([1, 3.5])
    with col1:
        notes_menu = option_menu(
            menu_title='',
            orientation='vertical',
            menu_icon='',
            options=['Add_Notes', 'Edit'],
            icons=["book", "pencil-square"],
            styles={
                "container": {"padding": "8!important", "background-color": 'black', 'border': '0.01px dotted red'},
                "icon": {"color": "red", "font-size": "12px"},
                "nav-link": {"color": "#d7c4c1", "font-size": "12px", "font-weight": 'bold', "text-align": "left", "--hover-color": "#d32f2f"},
                "nav-link-selected": {"background-color": "#1976d2"},
            },
            key="notes_menu")
    if notes_menu == 'Add_Notes':
        session_note = fetch_session_notes(db, appointment_id)
        if session_note:
            with col2:
                st.info("Session notes already exist for this appointment. You can only view them here or use the Edit option to make changes.")
                display_session_notes(session_note)
        else:
            with col2.expander("➕ SESSION NOTES FORM", expanded=True):
                appointment_date = datetime.today().date()
                appointment_time = datetime.now().time()
                current_concerns = st.text_area("🗨️ Current Concerns", placeholder="What are the main issues raised today?")
                case_summary = st.text_area("🧾 Case Summary", placeholder="Summarize today's session...")
                working_diagnosis = st.multiselect("🧠 Working Diagnosis", ['Depression', 'Anxiety', 'Acute stress reaction', 'PTSD'])
                intervention = st.multiselect("🧩 Intervention", ['Psychoeducation', 'CBT', 'Group session', 'Indiviual counselling'])

                follow_up_required = st.radio("📅 :red[SCHEDULE Follow-Up?]", ["No", "Yes"], horizontal=True)
                if follow_up_required == "Yes":
                    next_review_date = st.date_input("Next Review Date")
                    follow_up_reason = st.multiselect("Follow-Up Reason", ['CBT', 'Group session', 'Individual counselling'])
                    default_follow_up = [therapist_name] if therapist_name in therapists else []
                    follow_up_person = st.multiselect("By who?", therapists, default=default_follow_up)


                    # follow_up_person = st.multiselect("By who?", therapists, default=therapist_name)
                    follow_up = f"Yes | Date: {next_review_date}, Reason: {', '.join(follow_up_reason)}, By: {', '.join(follow_up_person)}"
                else:
                    follow_up = "Not required"

                refer_required = st.radio(":red[🔁 REFER CLIENT?]", ["No", "Yes"], horizontal=True)
                if refer_required == "Yes":
                    refer_to = st.selectbox("Refer to", therapists)
                    refer_reason = st.selectbox("Reason for Referral", ['Psychiatric consult', 'Psychotherapy', 'Follow-up'])
                    refer = f"Yes | To: {refer_to}, Reason: {refer_reason}"
                else:
                    refer = "Not required"

                remarks = st.text_area("📝 Remarks", placeholder="Any remarks/comments?")
                clinician_name = st.text_input('Therapist', value = therapist_name)

                if st.button("Submit Session Note"):
                    session_note_data = {
                        'appointment_date': appointment_date,
                        'appointment_time': appointment_time,
                        'current_concerns': current_concerns,
                        'case_summary': case_summary,
                        'working_diagnosis': ", ".join(working_diagnosis),
                        'intervention': ", ".join(intervention),
                        'follow_up': follow_up,
                        'refer': refer,
                        'remarks': remarks
                    }
                    response = insert_session_note(db, appointment_id, session_note_data, clinician_name)
                    if response["success"]:
                        st.success(response["message"])

                        if follow_up_required == "Yes":
                            reason_str = ", ".join(follow_up_reason)
                            assigned_to_str = ", ".join(follow_up_person)
                            cursor = db.cursor()
                            cursor.execute("SELECT user_id, name FROM appointments WHERE appointment_id = ?", (appointment_id,))
                            result = cursor.fetchone()
                            if result:
                                client_user_id = result["user_id"]
                                client_full_name = result["name"]
                                follow_up_result = insert_follow_up(
                                    db=db,
                                    user_id=client_user_id,
                                    full_name=client_full_name,
                                    appointment_id=appointment_id,
                                    follow_up_date=next_review_date,
                                    reason=reason_str,
                                    assigned_to=assigned_to_str
                                )
                                if follow_up_result["success"]:
                                    st.success("Follow-up successfully scheduled.")
                                else:
                                    st.error(f"Failed to schedule follow-up: {follow_up_result['message']}")
                            else:
                                st.error("Could not find client information for follow-up scheduling.")


    elif notes_menu == 'Edit':
        session_note = fetch_session_notes(db, appointment_id)
        if session_note:
            with col2.expander(f"✏️ Edit Session Note: {appointment_id}", expanded=True):
                appointment_date = st.date_input(
                    "Appointment Date",
                    value=datetime.strptime(session_note["appointment_date"], "%Y-%m-%d").date()
                )
                appointment_time = st.time_input(
                    "Appointment Time",
                    value=datetime.strptime(session_note["appointment_time"], "%H:%M:%S").time()
                )
                current_concerns = st.text_area("🗨️ Current Concerns", value=session_note["current_concerns"])
                case_summary = st.text_area("🧾 Case Summary", value=session_note["case_summary"])

                # multiselects restore from comma-separated values
                working_diagnosis = st.multiselect(
                    "🧠 Working Diagnosis",
                    ['Depression', 'Anxiety', 'Acute stress reaction', 'PTSD'],
                    default=[x.strip() for x in session_note["working_diagnosis"].split(",")] if session_note["working_diagnosis"] else []
                )
                intervention = st.multiselect(
                    "🧩 Intervention",
                    ['Psychoeducation', 'CBT', 'Group session', 'Individual counselling'],
                    default=[x.strip() for x in session_note["intervention"].split(",")] if session_note["intervention"] else []
                )

                # -------------------------
                # Follow-up restore logic
                # -------------------------
                follow_up_required = "Yes" if session_note["follow_up"].startswith("Yes") else "No"
                follow_up_required = st.radio(
                    "📅 :red[SCHEDULE Follow-Up?]",
                    ["No", "Yes"],
                    index=1 if follow_up_required == "Yes" else 0,
                    horizontal=True
                )

                if follow_up_required == "Yes":
                    # parse stored follow-up string
                    next_review_date, follow_up_reason, follow_up_person = None, [], []
                    try:
                        parts = dict([p.strip().split(":", 1) for p in session_note["follow_up"].split(",") if ":" in p])
                        if "Date" in parts:
                            next_review_date = datetime.strptime(parts["Date"].strip(), "%Y-%m-%d").date()
                        if "Reason" in parts:
                            follow_up_reason = [x.strip() for x in parts["Reason"].split(",")]
                        if "By" in parts:
                            follow_up_person = [x.strip() for x in parts["By"].split(",")]
                    except Exception:
                        pass

                    next_review_date = st.date_input("Next Review Date", value=next_review_date or datetime.today().date())
                    follow_up_reason = st.multiselect(
                        "Follow-Up Reason",
                        ['CBT', 'Group session', 'Individual counselling'],
                        default=follow_up_reason
                    )
                    follow_up_person = st.multiselect("By who?", therapists, default=follow_up_person)

                    follow_up = f"Yes | Date: {next_review_date}, Reason: {', '.join(follow_up_reason)}, By: {', '.join(follow_up_person)}"
                else:
                    follow_up = "Not required"

                # -------------------------
                # Referral restore logic
                # -------------------------
                refer_required = "Yes" if session_note["refer"].startswith("Yes") else "No"
                refer_required = st.radio(
                    ":red[🔁 REFER CLIENT?]",
                    ["No", "Yes"],
                    index=1 if refer_required == "Yes" else 0,
                    horizontal=True
                )

                if refer_required == "Yes":
                    refer_to, refer_reason = None, None
                    try:
                        parts = dict([p.strip().split(":", 1) for p in session_note["refer"].split(",") if ":" in p])
                        if "To" in parts:
                            refer_to = parts["To"].strip()
                        if "Reason" in parts:
                            refer_reason = parts["Reason"].strip()
                    except Exception:
                        pass

                    refer_to = st.selectbox("Refer to", therapists, index=therapists.index(refer_to) if refer_to in therapists else 0)
                    refer_reason = st.selectbox(
                        "Reason for Referral",
                        ['Psychiatric consult', 'Psychotherapy', 'Follow-up'],
                        index=['Psychiatric consult', 'Psychotherapy', 'Follow-up'].index(refer_reason) if refer_reason in ['Psychiatric consult', 'Psychotherapy', 'Follow-up'] else 0
                    )
                    refer = f"Yes | To: {refer_to}, Reason: {refer_reason}"
                else:
                    refer = "Not required"

                remarks = st.text_area("📝 Remarks", value=session_note["remarks"])
                clinician_name = st.text_input("Therapist", value=session_note.get("clinician_name", therapist_name))

                if st.button("Update Session Note"):
                    updated_note = {
                        "appointment_date": appointment_date,
                        "appointment_time": appointment_time.strftime("%H:%M:%S"),
                        "current_concerns": current_concerns,
                        "case_summary": case_summary,
                        "working_diagnosis": ", ".join(working_diagnosis),
                        "intervention": ", ".join(intervention),
                        "follow_up": follow_up,
                        "refer": refer,
                        "remarks": remarks,
                        "clinician_name": clinician_name
                    }
                    response = update_session_note(db, appointment_id, updated_note)
                    if response["success"]:
                        st.success(response["message"])
    else:
        st.warning("No session notes found to edit.")


    db.close()
if __name__ == "__main__":
    main()