DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

from datetime import datetime
import json

gad7_questions = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it's hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen"
]

response_map = {
    "Not at all": 0,
    "Several Days": 1,
    "More Than Half the Days": 2,
    "Nearly Every Day": 3
}

def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to SQLite DB: {e}")
        return None

def create_gad7_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS GAD7_forms (
            appointment_id TEXT PRIMARY KEY,
            user_id TEXT,
            client_name TEXT,
            client_type TEXT,
            screen_type TEXT,
            gad_score INTEGER,
            anxiety_status TEXT,
            responses_dict TEXT,
            assessment_date TEXT,
            assessed_by TEXT DEFAULT 'SELF',
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

def check_existing_entry(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM GAD7_forms WHERE appointment_id = ?", (appointment_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking existing GAD-7 entry: {e}")
        return False
    finally:
        cursor.close()

def calculate_gad7_score(responses):
    return sum(response_map.get(r["response"], 0) for r in responses)

def interpret_gad7_score(score):
    if score >= 15:
        return "Severe anxiety"
    elif score >= 10:
        return "Moderate anxiety"
    elif score >= 5:
        return "Mild anxiety"
    else:
        return "Minimal anxiety"

def generate_responses_dict(responses):
    return [
        {
            "question_id": entry["question"],
            "question": gad7_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

def insert_into_gad7_forms(db, appointment_id, user_id, client_name, client_type,
                           screen_type, gad_score, anxiety_status, responses_dict,
                           assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO GAD7_forms (
                appointment_id, user_id, client_name, client_type, screen_type,
                gad_score, anxiety_status, responses_dict, assessment_date, assessed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_id, user_id, client_name, client_type, screen_type,
            gad_score, anxiety_status, json.dumps(responses_dict), assessment_date, assessed_by
        ))
        db.commit()
        st.success("GAD-7 responses submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred saving GAD-7 responses: {e}")
    finally:
        cursor.close()

def fetch_appointment_data(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT appointment_id, user_id, name AS client_name,
                   client_type, screen_type, created_by
            FROM appointments
            WHERE appointment_id = ? AND actions LIKE '%"screen": true%'
            LIMIT 1
        """, (appointment_id,))
        row = cursor.fetchone()
        if not row:
            st.warning(f"No screening data found for appointment ID: {appointment_id}")
            return {}
        return dict(row)
    except Exception as e:
        st.error(f"Error fetching appointment data: {e}")
        return {}
    finally:
        cursor.close()

def capture_gad7_responses():
    responses = []
    answered = set()
    with st.form("GAD-7"):
        st.write("GENERALIZED ANXIETY DISORDER 7 (GAD-7)")
        st.markdown("#### Over the last 2 weeks, how often have you been bothered by the following problems?")
        for i, question in enumerate(gad7_questions, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:20px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=["Not Selected", "Not at all", "Several Days", "More Than Half the Days", "Nearly Every Day"],
                index=0,
                key=f"gad7_q{i}_{st.session_state.get('appointment_id', 'default')}_{st.session_state.get('unique_session_key', 'default')}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != "Not Selected":
                answered.add(i)
        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(gad7_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

def main():
    db = create_connection()
    if not db:
        st.stop()
    create_gad7_table(db)

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.error("No appointment ID found in session state.")
        st.stop()

    metadata = fetch_appointment_data(db, appointment_id)
    if not metadata:
        st.stop()

    if check_existing_entry(db, appointment_id):
        st.warning("GAD-7 responses already submitted for this appointment.")
        return

    responses = capture_gad7_responses()
    if responses:
        responses_dict = generate_responses_dict(responses)
        gad_score = calculate_gad7_score(responses)
        anxiety_status = interpret_gad7_score(gad_score)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_gad7_forms(
            db, appointment_id, metadata["user_id"], metadata["client_name"],
            metadata["client_type"], metadata["screen_type"],
            gad_score, anxiety_status, responses_dict,
            assessment_date, metadata["created_by"]
        )

    db.close()

if __name__ == "__main__":
    main()
