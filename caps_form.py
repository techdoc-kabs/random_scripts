import streamlit as st
import sqlite3

from datetime import datetime
import json
DB_PATH = "users_db.db"
caps_items = [
    "Persistent sadness or irritability",
    "Loss of interest in favorite activities",
    "Excessive worry or fear",
    "Difficulty concentrating",
    "Sleep problems (too little / too much)",
    "Significant change in appetite or weight",
    "Frequent headaches or stomach aches",
    "Social withdrawal",
    "Thoughts of self‑harm",
    "Hyperactivity or impulsivity",
    "Oppositional or defiant behavior",
    "Substance use",
    "Experiencing bullying or violence",
    "Family history of mental illness"
]

response_map = {"No": 0, "Yes": 1}

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def create_caps_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS CAPS_forms (
            appointment_id TEXT PRIMARY KEY,
            user_id TEXT,
            client_name TEXT,
            client_type TEXT,
            screen_type TEXT,
            total_score INTEGER,
            risk_level TEXT,
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
        cursor.execute("SELECT COUNT(*) FROM CAPS_forms WHERE appointment_id = ?", (appointment_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking for existing CAPS entry: {e}")
        return False
    finally:
        cursor.close()

def calculate_caps_score(responses):
    return sum(response_map.get(r["response"], 0) for r in responses)

def determine_risk_level(score):
    if score >= 8:
        return "High"
    elif score >= 4:
        return "Moderate"
    else:
        return "Low"

def generate_responses_dict(responses):
    return [
        {
            "question_id": entry["question"],
            "question": caps_items[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

def insert_into_caps_forms(db, appointment_id, user_id, client_name, client_type,
                           screen_type, total_score, risk_level, responses_dict,
                           assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        insert_query = """
            INSERT INTO CAPS_forms (
                appointment_id, user_id, client_name, client_type, screen_type,
                total_score, risk_level, responses_dict, assessment_date, assessed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            appointment_id, user_id, client_name, client_type, screen_type,
            total_score, risk_level, json.dumps(responses_dict), assessment_date, assessed_by
        )
        cursor.execute(insert_query, values)
        db.commit()
        st.success("CAPS-14 responses submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred while saving CAPS-14 responses: {e}")
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

def capture_caps_responses():
    responses = []
    answered = set()
    with st.form("CAPS-14"):
        st.write("CHILD & ADOLESCENT PSYCHIATRY SCREEN (CAPS-14)")
        st.markdown("#### Please respond to each item below:")
        for i, question in enumerate(caps_items, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:20px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=["Not Selected", "Yes", "No"],
                index=0,
                key=f"caps_q{i}_{st.session_state.get('appointment_id', 'default')}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != "Not Selected":
                answered.add(i)
        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(caps_items):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

def main():
    db = create_connection()
    create_caps_table(db)

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.error("No appointment ID found in session state.")
        st.stop()

    metadata = fetch_appointment_data(db, appointment_id)
    if not metadata:
        st.stop()

    if check_existing_entry(db, appointment_id):
        st.warning("CAPS-14 responses already submitted for this appointment.")
        return

    responses = capture_caps_responses()
    if responses:
        responses_dict = generate_responses_dict(responses)
        total_score = calculate_caps_score(responses)
        risk_level = determine_risk_level(total_score)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_caps_forms(
            db, appointment_id, metadata["user_id"], metadata["client_name"],
            metadata["client_type"], metadata["screen_type"],
            total_score, risk_level, responses_dict,
            assessment_date, metadata["created_by"]
        )

    db.close()

if __name__ == "__main__":
    main()
