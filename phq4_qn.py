DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

from datetime import datetime
import json

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def create_PHQ4_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS PHQ4_forms (
            appointment_id    TEXT,
            user_id           TEXT,
            name              TEXT,
            client_type       TEXT,
            screen_type       TEXT,
            total_score       INTEGER,
            anxiety_score     INTEGER,
            depression_score  INTEGER,
            severity          TEXT,
            responses_dict    TEXT,
            assessment_date   TEXT,
            assessed_by       TEXT DEFAULT 'SELF',
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id),
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

def insert_into_PHQ4_forms(db, appointment_id, user_id, name, client_type,
                           screen_type, total_score, anxiety_score, depression_score, severity,
                           responses_dict, assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        insert_query = """
        INSERT INTO PHQ4_forms (
            appointment_id, user_id, name, client_type, screen_type,
            total_score, anxiety_score, depression_score, severity,
            responses_dict, assessment_date, assessed_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            appointment_id, user_id, name, client_type, screen_type,
            total_score, anxiety_score, depression_score, severity,
            json.dumps(responses_dict), assessment_date, assessed_by
        )
        cursor.execute(insert_query, values)
        db.commit()
        st.success("PHQ-4 response submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred: {e}")
    finally:
        cursor.close()

phq4_questions = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless"
]

def check_existing_entry(db, appointment_id):
    try:
        cursor = db.cursor()
        query = "SELECT COUNT(*) FROM PHQ4_forms WHERE appointment_id = ?"
        cursor.execute(query, (appointment_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking for duplicates: {e}")
        return False
    finally:
        cursor.close()

def calculate_scores(responses):
    response_map = {
        "Not at all": 0,
        "Several Days": 1,
        "More Than Half the Days": 2,
        "Nearly Every Day": 3
    }
    anxiety_score = sum(response_map.get(r["response"], 0) for r in responses[:2])
    depression_score = sum(response_map.get(r["response"], 0) for r in responses[2:])
    total_score = anxiety_score + depression_score
    return total_score, anxiety_score, depression_score

def interpret_phq4_score(score):
    if score >= 9:
        return "Severe"
    elif score >= 6:
        return "Moderate"
    elif score >= 3:
        return "Mild"
    else:
        return "Normal"

def generate_responses_dict(responses):
    response_map = {
        "Not at all": 0,
        "Several Days": 1,
        "More Than Half the Days": 2,
        "Nearly Every Day": 3
    }
    return [
        {
            "question_id": entry["question"],
            "question": phq4_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

def capture_PHQ_4_responses():
    responses = []
    answered = set()
    with st.form("PHQ-4"):
        st.write("PATIENT HEALTH QUESTIONNAIRE-4 (PHQ-4)")
        st.markdown("#### Over the last 2 weeks, how often have you been bothered by the following problems?")
        for i, question in enumerate(phq4_questions, start=1):
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
            if len(answered) != len(phq4_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses


def fetch_screen_data_by_appointment_id(db, appointment_id):
    if not appointment_id:
        st.warning("No appointment ID provided to fetch screening data.")
        return {}
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
        screening_tools_json = row["screening_tools"]
        try:
            tools_data = json.loads(screening_tools_json) if screening_tools_json else {}
        except json.JSONDecodeError:
            st.error(f"Screening tools JSON is malformed for appointment ID: {appointment_id}")
            tools_data = {}
        return {
            "appointment_id": row["appointment_id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "client_type": row["client_type"],
            "screen_type": row["screen_type"],
            "created_by": row["created_by"],
            "screening_tools": tools_data}

    except Exception as e:
        st.error(f"❌ Could not fetch screen data from database: {e}")
        return {}
    finally:
        cursor.close()



def main():
    db = create_connection()
    create_PHQ4_forms_table(db)
    appointment_id = st.session_state.get("appointment_id")
    data = fetch_screen_data_by_appointment_id(db, appointment_id)

    if not data:
        st.error("Could not fetch screen data from database.")
        st.stop()

    appointment_id = data["appointment_id"]
    user_id = data["user_id"]
    name = data["name"]
    client_type = data["client_type"]
    screen_type = data["screen_type"]

    assessed_by = data['created_by']
    responses = capture_PHQ_4_responses()

    if responses:
        if check_existing_entry(db, appointment_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict = generate_responses_dict(responses)
        total_score, anxiety_score, depression_score = calculate_scores(responses_dict)
        severity = interpret_phq4_score(total_score)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_PHQ4_forms(
            db, appointment_id, user_id, name, client_type,
            screen_type, total_score, anxiety_score, depression_score, severity,
            responses_dict, assessment_date, assessed_by
        )

    db.close()

if __name__ == "__main__":
    main()
