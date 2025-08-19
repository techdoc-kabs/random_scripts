import streamlit as st
import sqlite3
from datetime import datetime
import json


DB_PATH = "users_db.db"
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def create_BDI_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS BDI_forms (
            action_id         TEXT,
            appointment_id    TEXT,
            user_id           TEXT,
            client_name       TEXT,
            client_type       TEXT,
            screen_type       TEXT,
            total_score       INTEGER,
            severity          TEXT,
            responses_dict    TEXT,
            assessment_date   TEXT,
            assessed_by       TEXT DEFAULT 'SELF',
            FOREIGN KEY(action_id) REFERENCES screen(action_id),
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

def insert_into_BDI_forms(db, action_id, appointment_id, user_id, client_name, client_type,
                          screen_type, total_score, severity,
                          responses_dict, assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        insert_query = """
        INSERT INTO BDI_forms (
            action_id, appointment_id, user_id, client_name, client_type, screen_type,
            total_score, severity, responses_dict, assessment_date, assessed_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            action_id, appointment_id, user_id, client_name, client_type, screen_type,
            total_score, severity, json.dumps(responses_dict), assessment_date, assessed_by
        )
        cursor.execute(insert_query, values)
        db.commit()
        st.success("BDI-II response submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred: {e}")
    finally:
        cursor.close()

bdi_questions = [
    "Sadness",
    "Pessimism",
    "Past Failure",
    "Loss of Pleasure",
    "Guilty Feelings",
    "Punishment Feelings",
    "Self-Dislike",
    "Self-Criticalness",
    "Suicidal Thoughts or Wishes",
    "Crying",
    "Agitation",
    "Loss of Interest",
    "Indecisiveness",
    "Worthlessness",
    "Loss of Energy",
    "Changes in Sleeping Pattern",
    "Irritability",
    "Changes in Appetite",
    "Concentration Difficulty",
    "Tiredness or Fatigue",
    "Loss of Interest in Sex"
]

def check_existing_entry(db, action_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM BDI_forms WHERE action_id = ?", (action_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking for duplicates: {e}")
        return False
    finally:
        cursor.close()

def calculate_scores(responses):
    response_map = {
        "Not at all": 0,
        "Mildly; it didn’t bother me much": 1,
        "Moderately; I felt like I had to put in a little effort": 2,
        "Severely; I could barely stand it": 3
    }
    return sum(response_map.get(r["response"], 0) for r in responses)

def interpret_bdi_score(score):
    if score <= 13:
        return "Minimal"
    elif score <= 19:
        return "Mild"
    elif score <= 28:
        return "Moderate"
    else:
        return "Severe"

def generate_responses_dict(responses):
    response_map = {
        "Not at all": 0,
        "Mildly; it didn’t bother me much": 1,
        "Moderately; I felt like I had to put in a little effort": 2,
        "Severely; I could barely stand it": 3
    }
    return [
        {
            "question_id": entry["question"],
            "question": bdi_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

def capture_BDI_responses():
    responses = []
    answered = set()
    options = [
        "Not at all",
        "Mildly; it didn’t bother me much",
        "Moderately; I felt like I had to put in a little effort",
        "Severely; I could barely stand it"
    ]

    with st.form("BDI-II"):
        st.write("BECK DEPRESSION INVENTORY-II (BDI-II)")
        st.markdown("#### Over the past two weeks, choose the statement that best describes how you have been feeling:")
        for i, question in enumerate(bdi_questions, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:20px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=options,
                index=0,
                key=f"bdi_q{i}_{st.session_state.get('appointment_id','default')}_{st.session_state.get('unique_session_key','default')}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != options[0]:
                answered.add(i)

        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(bdi_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

def fetch_screen_data_by_action_id(db, action_id):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT action_id, appointment_id, user_id, client_name, client_type, screen_type
            FROM screen
            WHERE action_id = ?
        """, (action_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        st.error(f"Error fetching screen data: {e}")
        return None

def main():
    db = create_connection()
    create_BDI_forms_table(db)

    if "action_id" not in st.session_state:
        st.error("Missing action_id in session.")
        st.stop()

    action_id = st.session_state["action_id"]
    data = fetch_screen_data_by_action_id(db, action_id)
    if not data:
        st.error("Could not fetch screen data.")
        st.stop()

    appointment_id = data["appointment_id"]
    user_id       = data["user_id"]
    client_name   = data["client_name"]
    client_type   = data["client_type"]
    screen_type   = data["screen_type"]

    assessed_by = st.text_input('Assessed by', value='SELF')
    responses   = capture_BDI_responses()

    if responses:
        if check_existing_entry(db, action_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict   = generate_responses_dict(responses)
        total_score      = calculate_scores(responses)
        severity         = interpret_bdi_score(total_score)
        assessment_date  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_BDI_forms(
            db, action_id, appointment_id, user_id, client_name, client_type,
            screen_type, total_score, severity,
            responses_dict, assessment_date, assessed_by
        )

    db.close()

if __name__ == "__main__":
    main()
