DB_PATH = "users_db.db"
import streamlit as st
import json
from datetime import datetime

try:
    import mysql.connector
    from db_connection import get_mysql_connection
except ImportError as e:
    st.error(f"Required module missing: {e}")
    raise

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
    try:
        db = get_mysql_connection()
        return db
    except mysql.connector.Error as e:
        st.error(f"Failed to connect to MySQL DB: {e}")
        return None

def create_phq9_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PHQ9_forms (
            appointment_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255),
            client_name VARCHAR(255),
            client_type VARCHAR(100),
            screen_type VARCHAR(100),
            phq9_score INT,
            depression_status VARCHAR(50),
            suicide_response INT,
            suicide_risk VARCHAR(50),
            responses_dict TEXT,
            assessment_date DATETIME,
            assessed_by VARCHAR(255) DEFAULT 'SELF',
            FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()
    cursor.close()

def check_existing_entry(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM PHQ9_forms WHERE appointment_id = %s", (appointment_id,))
        exists = cursor.fetchone()[0] > 0
        cursor.close()
        return exists
    except Exception as e:
        st.error(f"Error checking existing PHQ-9 entry: {e}")
        return False

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
    else:
        return "Minimal depression"

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

def insert_into_phq9_forms(db, appointment_id, user_id, client_name, client_type,
                           screen_type, phq9_score, depression_status, responses_dict,
                           assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO PHQ9_forms (
                appointment_id, user_id, client_name, client_type, screen_type,
                phq9_score, depression_status, responses_dict, assessment_date, assessed_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            appointment_id, user_id, client_name, client_type, screen_type,
            phq9_score, depression_status, json.dumps(responses_dict), assessment_date, assessed_by
        ))
        db.commit()
        st.success("PHQ-9 responses submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred saving PHQ-9 responses: {e}")
    finally:
        cursor.close()

def fetch_appointment_data(db, appointment_id):
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT appointment_id, user_id, name AS client_name,
                   client_type, screen_type, created_by
            FROM appointments
            WHERE appointment_id = %s AND actions LIKE '%"screen": true%'
            LIMIT 1
        """, (appointment_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            st.warning(f"No screening data found for appointment ID: {appointment_id}")
            return {}
        return row
    except Exception as e:
        st.error(f"Error fetching appointment data: {e}")
        return {}

def capture_phq9_responses():
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
                key=f"phq9_q{i}_{st.session_state.get('appointment_id', 'default')}_{st.session_state.get('unique_session_key', 'default')}"
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

def main():
    db = create_connection()
    if not db:
        st.stop()
    create_phq9_table(db)

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.error("No appointment ID found in session state.")
        st.stop()

    metadata = fetch_appointment_data(db, appointment_id)
    if not metadata:
        st.stop()

    if check_existing_entry(db, appointment_id):
        st.warning("PHQ-9 responses already submitted for this appointment.")
        return

    responses = capture_phq9_responses()
    if responses:
        responses_dict = generate_responses_dict(responses)
        phq9_score = calculate_phq9_score(responses)
        depression_status = interpret_phq9_score(phq9_score)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_phq9_forms(
            db, appointment_id, metadata["user_id"], metadata["client_name"],
            metadata["client_type"], metadata["screen_type"],
            phq9_score, depression_status, responses_dict,
            assessment_date, metadata["created_by"]
        )

    db.close()

if __name__ == "__main__":
    main()
