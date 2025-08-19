DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime

# DASS-21 questions (21 items)
dass21_questions = [
    "I found it hard to wind down",
    "I was aware of dryness of my mouth",
    "I couldn’t seem to experience any positive feeling at all",
    "I experienced breathing difficulty (e.g., excessively rapid breathing, breathlessness, etc.)",
    "I found it difficult to work up the initiative to do things",
    "I tended to over-react to situations",
    "I experienced trembling (e.g., in the hands)",
    "I felt that I was using a lot of nervous energy",
    "I was worried about situations in which I might panic and make a fool of myself",
    "I felt that I had nothing to look forward to",
    "I found myself getting agitated",
    "I found it difficult to relax",
    "I felt down-hearted and blue",
    "I was intolerant of anything that kept me from getting on with what I was doing",
    "I felt I was close to panic",
    "I was unable to become enthusiastic about anything",
    "I felt I wasn’t worth much as a person",
    "I felt that I was rather touchy",
    "I was aware of the action of my heart in the absence of physical exertion (e.g., sense of heart rate increase, heart missing a beat)",
    "I felt scared without any good reason",
    "I felt that life was meaningless"
]

# DASS-21 response options mapping
dass21_response_map = {
    "Did not apply to me at all": 0,
    "Applied to me to some degree, or some of the time": 1,
    "Applied to me to a considerable degree, or a good part of time": 2,
    "Applied to me very much, or most of the time": 3
}

# Indices of questions for subscales (0-based)
depression_indices = [2, 4, 10, 12, 15, 16, 19]  # Q3,5,11,13,16,17,20
anxiety_indices = [1, 3, 6, 8, 18]               # Q2,4,7,9,19
stress_indices = [0, 5, 7, 9, 11, 13, 14, 17, 20]  # Q1,6,8,10,12,14,15,18,21

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def create_dass21_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS dass21_forms (
            appointment_id   TEXT PRIMARY KEY,
            user_id          TEXT,
            name             TEXT,
            client_type      TEXT,
            screen_type      TEXT,
            depression_score INTEGER,
            depression_status TEXT,
            anxiety_score    INTEGER,
            anxiety_status   TEXT,
            stress_score     INTEGER,
            stress_status    TEXT,
            total_score      INTEGER,
            responses_dict   TEXT,
            assessment_date  TEXT,
            assessed_by      TEXT DEFAULT 'SELF',
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

def check_existing_entry(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM dass21_forms WHERE appointment_id = ?", (appointment_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking existing entry: {e}")
        return False
    finally:
        cursor.close()

def calculate_scores(responses):
    vals = [dass21_response_map.get(r["response"], 0) for r in responses]
    depression = sum(vals[i] for i in depression_indices) * 2
    anxiety = sum(vals[i] for i in anxiety_indices) * 2
    stress = sum(vals[i] for i in stress_indices) * 2
    total = depression + anxiety + stress
    return depression, anxiety, stress, total

def interpret_severity(depression, anxiety, stress):
    def severity_level(score, cutoffs):
        for level, (low, high) in cutoffs.items():
            if low <= score <= high:
                return level
        return "Extremely Severe"

    depression_cutoffs = {
        "Normal": (0, 9),
        "Mild": (10, 13),
        "Moderate": (14, 20),
        "Severe": (21, 27),
        "Extremely Severe": (28, 42)
    }
    anxiety_cutoffs = {
        "Normal": (0, 7),
        "Mild": (8, 9),
        "Moderate": (10, 14),
        "Severe": (15, 19),
        "Extremely Severe": (20, 42)
    }
    stress_cutoffs = {
        "Normal": (0, 14),
        "Mild": (15, 18),
        "Moderate": (19, 25),
        "Severe": (26, 33),
        "Extremely Severe": (34, 42)
    }

    dep_sev = severity_level(depression, depression_cutoffs)
    anx_sev = severity_level(anxiety, anxiety_cutoffs)
    str_sev = severity_level(stress, stress_cutoffs)

    return dep_sev, anx_sev, str_sev

def generate_responses_dict(responses):
    return [
        {
            "question_id": entry["question"],
            "question": dass21_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": dass21_response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

def insert_into_dass21_forms(db, appointment_id, user_id, name, client_type,
                             screen_type, depression_score, depression_status,
                             anxiety_score, anxiety_status, stress_score, stress_status,
                             total_score, responses_dict, assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO dass21_forms (
                appointment_id, user_id, name, client_type, screen_type,
                depression_score, depression_status,
                anxiety_score, anxiety_status,
                stress_score, stress_status,
                total_score, responses_dict, assessment_date, assessed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_id, user_id, name, client_type, screen_type,
            depression_score, depression_status,
            anxiety_score, anxiety_status,
            stress_score, stress_status,
            total_score, json.dumps(responses_dict), assessment_date, assessed_by
        ))
        db.commit()
        st.success("DASS-21 responses submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"❌ Could not insert DASS-21 responses: {e}")
    finally:
        cursor.close()

def capture_dass21_responses():
    responses = []
    answered = set()
    with st.form("DASS-21"):
        st.write("### Depression Anxiety Stress Scales - 21 Items (DASS-21)")
        for i, question in enumerate(dass21_questions, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:18px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=[
                    "Did not apply to me at all",
                    "Applied to me to some degree, or some of the time",
                    "Applied to me to a considerable degree, or a good part of time",
                    "Applied to me very much, or most of the time"
                ],
                index=0,
                key=f"dass21_q{i}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != "Not Selected":
                answered.add(i)
        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(dass21_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

def fetch_screen_data_by_appointment_id(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT appointment_id, user_id, name, client_type, screen_type, created_by
            FROM appointments
            WHERE appointment_id = ?
            LIMIT 1
        """, (appointment_id,))
        row = cursor.fetchone()
        if not row:
            st.warning(f"No data found for appointment ID: {appointment_id}")
            return {}
        return {
            "appointment_id": row["appointment_id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "client_type": row["client_type"],
            "screen_type": row["screen_type"],
            "created_by": row["created_by"],
        }
    except Exception as e:
        st.error(f"Error fetching appointment data: {e}")
        return {}
    finally:
        cursor.close()

def main():
    db = create_connection()
    create_dass21_forms_table(db)

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.error("No appointment ID found in session.")
        st.stop()

    data = fetch_screen_data_by_appointment_id(db, appointment_id)
    if not data:
        st.stop()

    user_id = data["user_id"]
    name = data["name"]
    client_type = data["client_type"]
    screen_type = data["screen_type"]
    assessed_by = data.get("created_by", "SELF")

    responses = capture_dass21_responses()
    if responses:
        if check_existing_entry(db, appointment_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict = generate_responses_dict(responses)
        depression_score, anxiety_score, stress_score, total_score = calculate_scores(responses)
        depression_status, anxiety_status, stress_status = interpret_severity(depression_score, anxiety_score, stress_score)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_dass21_forms(
            db, appointment_id, user_id, name, client_type,
            screen_type, depression_score, depression_status,
            anxiety_score, anxiety_status, stress_score, stress_status,
            total_score, responses_dict, assessment_date, assessed_by
        )

    db.close()

if __name__ == "__main__":
    main()
