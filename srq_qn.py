DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

from datetime import datetime
import json

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def create_SQR_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS SQR_forms (
            action_id         TEXT,
            appointment_id    TEXT,
            user_id           TEXT,
            client_name       TEXT,
            client_type       TEXT,
            screen_type       TEXT,
            total_score       INTEGER,
            level             TEXT,
            responses_dict    TEXT,
            assessment_date   TEXT,
            assessed_by       TEXT DEFAULT 'SELF',
            FOREIGN KEY(action_id) REFERENCES screen(action_id),
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

def insert_into_SQR_forms(db, action_id, appointment_id, user_id, client_name, client_type,
                          screen_type, total_score, level,
                          responses_dict, assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        insert_query = """
        INSERT INTO SQR_forms (
            action_id, appointment_id, user_id, client_name, client_type, screen_type,
            total_score, level, responses_dict, assessment_date, assessed_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            action_id, appointment_id, user_id, client_name, client_type, screen_type,
            total_score, level, json.dumps(responses_dict), assessment_date, assessed_by
        )
        cursor.execute(insert_query, values)
        db.commit()
        st.success("SQR response submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred: {e}")
    finally:
        cursor.close()

sqr_questions = [
    "I see myself as resilient when faced with challenges.",
    "I can express my feelings in a healthy way.",
    "I believe I have talents and skills that make me unique.",
    "I can work well with others in a team.",
    "I handle stress and frustration effectively.",
    "I set goals and work towards achieving them.",
    "I feel confident in solving problems on my own.",
    "I show empathy to others and care about their feelings.",
    "I feel proud of who I am.",
    "I stay hopeful even during tough times."
]

def check_existing_entry(db, action_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM SQR_forms WHERE action_id = ?", (action_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking for duplicates: {e}")
        return False
    finally:
        cursor.close()

def calculate_scores(responses):
    response_map = {
        "Never": 0,
        "Sometimes": 1,
        "Often": 2,
        "Always": 3
    }
    return sum(response_map.get(r["response"], 0) for r in responses)

def interpret_sqr_score(score):
    if score <= 10:
        return "Low Strength"
    elif score <= 20:
        return "Moderate Strength"
    else:
        return "High Strength"

def generate_responses_dict(responses):
    response_map = {
        "Never": 0,
        "Sometimes": 1,
        "Often": 2,
        "Always": 3
    }
    return [
        {
            "question_id": entry["question"],
            "question": sqr_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

def capture_SQR_responses():
    responses = []
    answered = set()
    options = ["Never", "Sometimes", "Often", "Always"]

    with st.form("SQR"):
        st.write("STRENGTHS & QUALITIES REFLECTION (SQR)")
        st.markdown("#### Reflect on the statements below and select how often they apply to you:")
        for i, question in enumerate(sqr_questions, start=1):
            st.markdown(f"<span style='color:darkgreen; font-size:20px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=options,
                index=0,
                key=f"sqr_q{i}_{st.session_state.get('appointment_id','default')}_{st.session_state.get('unique_session_key','default')}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != options[0]:
                answered.add(i)

        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(sqr_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

def fetch_screen_data_by_action_id(db, action_id):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT action_id, appointment_id, user_id, client_name, client_type, screen_type, created_by
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
    create_SQR_forms_table(db)

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
    created_by = data['created_by']
    responses   = capture_SQR_responses()

    if responses:
        if check_existing_entry(db, action_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict   = generate_responses_dict(responses)
        total_score      = calculate_scores(responses)
        level            = interpret_sqr_score(total_score)
        assessment_date  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_SQR_forms(
            db, action_id, appointment_id, user_id, client_name, client_type,
            screen_type, total_score, level,
            responses_dict, assessment_date, created_by
        )

    db.close()

if __name__ == "__main__":
    main()
