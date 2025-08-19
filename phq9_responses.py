DB_PATH = "users_db.db"
import streamlit as st
import json
import sqlite3


def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row 
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to SQLite DB: {e}")
        return None

phq9_questions = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading the newspaper or watching television",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead, or of hurting yourself in some way"
]

def fetch_captured_responses(db, appointment_id):
    try:
        cursor = db.cursor()
        query = "SELECT responses_dict FROM PHQ9_forms WHERE appointment_id = ?"
        cursor.execute(query, (appointment_id,))
        row = cursor.fetchone()
        cursor.close()

        if row and row["responses_dict"]:
            try:
                return json.loads(row["responses_dict"])
            except json.JSONDecodeError:
                st.error("Error decoding the responses.")
                return []
        return []
    except Exception as e:
        st.error(f"Failed to fetch PHQ-9 responses: {e}")
        return []

def generate_responses_markdown(answered_questions):
    response_values = {
        "Not at all": 0,
        "Several Days": 1,
        "More Than Half the Days": 2,
        "Nearly Every Day": 3
    }
    if not isinstance(answered_questions, list):
        st.error("Invalid data format for responses.")
        return ""
    formatted_responses = "\n".join(
        f"<span style='color:white'>{i + 1}. \"{phq9_questions[i]}\"</span>\n"
        f"<span style='color:#AA4A44'>{entry['response']} ({response_values.get(entry['response'], 'N/A')})</span>\n"
        for i, entry in enumerate(answered_questions)
    )
    return formatted_responses

##### DRIVER FUNCTION #####
def main():
    db = create_connection()
    appointment_id = st.session_state.get("appointment_id")
    if appointment_id:
        responses = fetch_captured_responses(db, appointment_id)
        if responses:
            with st.expander('PHQ-9 RESPONSES', expanded=True):
                formatted = generate_responses_markdown(responses)
                st.markdown(formatted, unsafe_allow_html=True)
        else:
            st.warning("PHQ-9 responses not yet filled.")
    else:
        st.warning("Appointment ID is missing in session state.")
    db.close()

if __name__ == "__main__":
    main()
