DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime

# SSQ questions
ssq_questions = [
    "I feel anxious when asked to speak in front of the class",
    "I worry about tests or exams even when I am well-prepared",
    "I avoid raising my hand because I am afraid of being wrong",
    "I feel nervous when I have to meet with a teacher",
    "I worry about what other students think of me",
    "I feel anxious when starting a new class or subject",
    "I have trouble concentrating because I feel nervous",
    "I feel tense during group activities",
    "I worry about being called on unexpectedly"
]

# Response mapping
response_map = {
    "Not at all": 0,
    "Sometimes": 1,
    "Often": 2,
    "Almost Always": 3
}

# Database connection
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

# Create SSQ table
def create_SSQ_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS SSQ_forms (
            appointment_id    TEXT PRIMARY KEY,
            user_id           TEXT,
            name              TEXT,
            client_type       TEXT,
            screen_type       TEXT,
            ssq_score         INTEGER,
            severity_level    TEXT,
            responses_dict    TEXT,
            assessment_date   TEXT,
            assessed_by       TEXT DEFAULT 'SELF',
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

# Check existing entry
def check_existing_entry(db, appointment_id):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM SSQ_forms WHERE appointment_id = ?", (appointment_id,))
    exists = cursor.fetchone()[0] > 0
    cursor.close()
    return exists

# Score calculation
def calculate_ssq_score(responses):
    return sum(response_map.get(r["response"], 0) for r in responses)

# Severity interpretation
def interpret_ssq_score(score):
    if score >= 20:
        return "Severe"
    elif score >= 15:
        return "Moderate"
    elif score >= 10:
        return "Mild"
    else:
        return "Minimal"

# Generate responses dict
def generate_responses_dict(responses):
    return [
        {
            "question_id": entry["question"],
            "question": ssq_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

# Insert into SSQ table
def insert_into_SSQ_forms(db, appointment_id, user_id, name, client_type,
                          screen_type, total_score, severity_level,
                          responses_dict, assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO SSQ_forms (
                appointment_id, user_id, name, client_type, screen_type,
                ssq_score, severity_level, responses_dict, assessment_date, assessed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_id, user_id, name, client_type, screen_type,
            total_score, severity_level, json.dumps(responses_dict),
            assessment_date, assessed_by
        ))
        db.commit()
        st.success("SSQ response submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"❌ Could not insert SSQ responses: {e}")
    finally:
        cursor.close()

# Form UI
def capture_SSQ_responses():
    responses = []
    answered = set()
    with st.form("SSQ_Form"):
        st.write("SCHOOL SITUATIONS QUESTIONNAIRE (SSQ)")
        st.markdown("#### Over the last few weeks, how often have you felt the following situations apply to you?")
        for i, question in enumerate(ssq_questions, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:20px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=["Not Selected", "Not at all", "Sometimes", "Often", "Almost Always"],
                index=0,
                key=f"q{i}_{st.session_state.get('appointment_id', 'default')}_{st.session_state.get('unique_session_key', 'default')}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != "Not Selected":
                answered.add(i)
        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(ssq_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

# Fetch screening data
def fetch_screen_data_by_appointment_id(db, appointment_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT appointment_id, user_id, name, client_type, screen_type, created_by
        FROM appointments
        WHERE appointment_id = ?
        AND actions LIKE '%"screen": true%'
        LIMIT 1
    """, (appointment_id,))
    row = cursor.fetchone()
    cursor.close()
    if not row:
        st.warning(f"No screening data found for appointment ID: {appointment_id}")
        return {}
    return dict(row)

# Main
def main():
    db = create_connection()
    create_SSQ_forms_table(db)

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.error("No appointment ID found in session.")
        st.stop()

    data = fetch_screen_data_by_appointment_id(db, appointment_id)
    if not data:
        st.stop()

    responses = capture_SSQ_responses()
    if responses:
        if check_existing_entry(db, appointment_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict = generate_responses_dict(responses)
        total_score = calculate_ssq_score(responses)
        severity_level = interpret_ssq_score(total_score)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_SSQ_forms(
            db, appointment_id, data["user_id"], data["name"], data["client_type"],
            data["screen_type"], total_score, severity_level,
            responses_dict, assessment_date, data.get("created_by", "SELF")
        )

    db.close()

if __name__ == "__main__":
    main()
