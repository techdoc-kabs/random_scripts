DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime

# PHQ-9 questions
phq9_questions = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading or watching television",
    "Moving or speaking so slowly that other people could have noticed, or being so fidgety/restless more than usual",
    "Thoughts that you would be better off dead or of hurting yourself"
]

response_map = {
    "Not at all": 0,
    "Several Days": 1,
    "More Than Half the Days": 2,
    "Nearly Every Day": 3
}

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def create_PHQ9_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS PHQ9_forms (
            appointment_id    TEXT PRIMARY KEY,
            user_id           TEXT,
            name              TEXT,
            client_type       TEXT,
            screen_type       TEXT,
            phq9_score      INTEGER,
            suicide_response  INTEGER,
            suicide_risk      TEXT,
            depression_status  TEXT,
            responses_dict    TEXT,
            assessment_date   TEXT,
            assessed_by       TEXT DEFAULT 'SELF',
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()



def check_existing_entry(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM PHQ9_forms WHERE appointment_id = ?", (appointment_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking existing PHQ-9 entry: {e}")
        return False
    finally:
        cursor.close()

def calculate_phq9_score(responses):
    return sum(response_map.get(r["response"], 0) for r in responses)

def interpret_phq9_score(score):
    if score >= 20:
        return "Severe depression"
    elif score >= 15:
        return "Moderately Severe depression"
    elif score >= 10:
        return "Moderate depression"
    elif score >= 5:
        return "Mild depression"
    elif score >= 1:
        return "Minimal depression"
    else:
        return "No depression"

def get_suicide_metrics(responses_dict):
    q9 = next((r for r in responses_dict if r["question_id"] == "Q9"), None)
    suicide_response_val = q9["response_value"] if q9 else -1
    if suicide_response_val == 0:
        risk = "Low risk"
    elif suicide_response_val == 1:
        risk = "Moderate risk"
    elif suicide_response_val >= 2:
        risk = "High risk"
    else:
        risk = "Unknown"
    return suicide_response_val, risk

def generate_responses_dict(responses):
    return [
        {
            "question_id": entry["question"],
            "question": phq9_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

def insert_into_PHQ9_forms(db, appointment_id, user_id, name, client_type,
                           screen_type, phq9_score, suicide_response, suicide_risk,
                           depression_status, responses_dict, assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO PHQ9_forms (
                appointment_id, user_id, name, client_type, screen_type,
                phq9_score, suicide_response, suicide_risk, depression_status,
                responses_dict, assessment_date, assessed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_id, user_id, name, client_type, screen_type,
            phq9_score, suicide_response, suicide_risk, depression_status,
            json.dumps(responses_dict), assessment_date, assessed_by
        ))
        db.commit()
        st.success("PHQ-9 response submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"❌ Could not insert PHQ-9 responses: {e}")
    finally:
        cursor.close()

def capture_PHQ_9_responses():
    responses = []
    answered = set()
    with st.form("PHQ-9"):
        st.write("PATIENT HEALTH QUESTIONNAIRE-9 (PHQ-9)")
        st.markdown("#### Over the last 2 weeks, how often have you been bothered by the following problems?")
        for i, question in enumerate(phq9_questions, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:20px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=["Not Selected", "Not at all", "Several Days", "More Than Half the Days", "Nearly Every Day"],
                index=0,
                key=f"q{i}_{st.session_state.get('appointment_id', 'default')}_{st.session_state.get('unique_session_key', 'default')}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != "Not Selected":
                answered.add(i)
        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(phq9_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

def fetch_screen_data_by_appointment_id(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT appointment_id, user_id, name, client_type, screen_type, created_by, screening_tools
            FROM appointments
            WHERE appointment_id = ?
            AND actions LIKE '%"screen": true%'
            LIMIT 1
        """, (appointment_id,))
        row = cursor.fetchone()
        if not row:
            st.warning(f"No screening data found for appointment ID: {appointment_id}")
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


def fetch_screen_data_by_appointment_id(db, appointment_id):
    if not appointment_id:
        st.warning("No appointment ID provided to fetch screening data.")
        return {}

    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT appointment_id, user_id, name, client_type, screen_type, created_by, screening_tools, actions
            FROM appointments
            WHERE appointment_id = ?
            LIMIT 1
        """, (appointment_id,))
        row = cursor.fetchone()

        if not row:
            st.warning(f"No appointment found for ID: {appointment_id}")
            return {}

        # Parse actions JSON
        actions_raw = row["actions"] if "actions" in row.keys() else None
        try:
            actions = json.loads(actions_raw) if actions_raw else {}
        except:
            actions = {}

        # Check if screening exists in any form
        if "screen" not in actions:
            st.warning(f"No screening action found for appointment ID: {appointment_id}")
            return {}

        # Return clean data
        return {
            "appointment_id": row["appointment_id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "client_type": row["client_type"],
            "screen_type": row["screen_type"],
            "created_by": row["created_by"],
            "screening_tools": row["screening_tools"],
            "actions": actions
        }

    except Exception as e:
        st.error(f"Error fetching appointment data: {e}")
        return {}

    finally:
        cursor.close()

def main():
    db = create_connection()
    create_PHQ9_forms_table(db)

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

    responses = capture_PHQ_9_responses()
    if responses:
        if check_existing_entry(db, appointment_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict = generate_responses_dict(responses)
        phq9_score = calculate_phq9_score(responses)
        depression_status = interpret_phq9_score(phq9_score)
        suicide_response, suicide_risk = get_suicide_metrics(responses_dict)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_PHQ9_forms(
            db, appointment_id, user_id, name, client_type,
            screen_type, phq9_score, suicide_response, suicide_risk,
            depression_status, responses_dict, assessment_date, assessed_by
        )

    db.close()

if __name__ == "__main__":
    main()
