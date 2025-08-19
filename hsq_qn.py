DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime

# Questions for Home Situations Questionnaire (HSQ)
home_questions = [
    "Has difficulty following family rules or expectations",
    "Often argues with family members",
    "Shows lack of interest in family activities",
    "Avoids helping with chores or responsibilities at home",
    "Has trouble managing emotions at home",
    "Often refuses to do what parents or caregivers ask",
    "Has difficulty getting along with siblings",
    "Frequently loses temper at home",
    "Appears restless or unsettled at home",
    "Has difficulty concentrating on tasks at home"
]

response_map = {
    "Not at all": 0,
    "Several Days": 1,
    "More Than Half the Days": 2,
    "Nearly Every Day": 3
}

# ───────────────────────────────
# DB Connection
# ───────────────────────────────
def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to SQLite DB: {e}")
        return None

def create_HSQ_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS HSQ_forms (
            appointment_id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            client_type TEXT,
            screen_type TEXT,
            total_score INTEGER,
            severity TEXT,
            responses_dict TEXT,
            assessment_date TEXT,
            assessed_by TEXT DEFAULT 'SELF',
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

def check_existing_entry(db, appointment_id):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM HSQ_forms WHERE appointment_id = ?", (appointment_id,))
    exists = cursor.fetchone()[0] > 0
    cursor.close()
    return exists

# ───────────────────────────────
# Score & Responses
# ───────────────────────────────
def calculate_total_score(responses):
    return sum(response_map.get(r["response"], 0) for r in responses if r["response"] != "Not Selected")

def interpret_severity(score):
    if score >= 24:
        return "Severe"
    elif score >= 18:
        return "Moderate"
    elif score >= 10:
        return "Mild"
    else:
        return "Minimal"

def generate_responses_dict(responses):
    return [
        {
            "question_id": f"Q{i+1}",
            "question": home_questions[i],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], None)
        }
        for i, entry in enumerate(responses)
    ]

# ───────────────────────────────
# Insert into DB
# ───────────────────────────────
def insert_into_HSQ_forms(db, appointment_id, user_id, name, client_type, screen_type,
                         total_score, severity, responses_dict, assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO HSQ_forms (
                appointment_id, user_id, name, client_type, screen_type,
                total_score, severity, responses_dict, assessment_date, assessed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_id, user_id, name, client_type, screen_type,
            total_score, severity, json.dumps(responses_dict), assessment_date, assessed_by
        ))
        db.commit()
        st.success("HSQ responses submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"❌ Could not insert HSQ responses: {e}")
    finally:
        cursor.close()

# ───────────────────────────────
# Form UI
# ───────────────────────────────
def capture_HSQ_responses():
    responses = []
    answered = set()
    unique_key = st.session_state.get('unique_session_key', 'default')

    with st.form("HSQ_form_"):
        st.header("HOME SITUATIONS QUESTIONNAIRE (HSQ)")
        st.markdown("#### Over the last 2 weeks, how often have you been bothered by the following problems at home?")

        for i, question in enumerate(home_questions, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:18px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=["Not Selected", "Not at all", "Several Days", "More Than Half the Days", "Nearly Every Day"],
                index=0,
                key=f"hsq_q{i}_{st.session_state.get('appointment_id', 'default')}_{unique_key}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != "Not Selected":
                answered.add(i)

        submitted = st.form_submit_button("Submit HSQ Responses")
        if submitted:
            if len(answered) != len(home_questions):
                st.warning("Please answer all questions before submitting.")
                return None
            return responses

# ───────────────────────────────
# Main Function
# ───────────────────────────────
def main():
    db = create_connection()
    if db is None:
        return

    create_HSQ_forms_table(db)

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.error("No appointment ID found in session.")
        st.stop()

    cursor = db.cursor()
    cursor.execute("SELECT user_id, name, client_type, screen_type, created_by FROM appointments WHERE appointment_id = ?", (appointment_id,))
    row = cursor.fetchone()
    cursor.close()

    if not row:
        st.error("Appointment not found in DB.")
        st.stop()

    user_id = row["user_id"]
    name = row["name"]
    client_type = row["client_type"]
    screen_type = row["screen_type"]
    assessed_by = row["created_by"] if "created_by" in row.keys() else "SELF"

    responses = capture_HSQ_responses()

    if responses:
        if check_existing_entry(db, appointment_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict = generate_responses_dict(responses)
        total_score = calculate_total_score(responses)
        severity = interpret_severity(total_score)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_HSQ_forms(
            db, appointment_id, user_id, name, client_type, screen_type,
            total_score, severity, responses_dict, assessment_date, assessed_by
        )

    db.close()

if __name__ == "__main__":
    main()
