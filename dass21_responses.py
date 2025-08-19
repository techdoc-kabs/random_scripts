DB_PATH = "users_db.db"
import streamlit as st
import json
import sqlite3


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

def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row 
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to SQLite DB: {e}")
        return None

def fetch_dass21_data(db, appointment_id):
    try:
        cursor = db.cursor()
        query = """
            SELECT responses_dict, depression_score, depression_status, 
                   anxiety_score, anxiety_status, stress_score, stress_status, total_score
            FROM dass21_forms WHERE appointment_id = ?
        """
        cursor.execute(query, (appointment_id,))
        row = cursor.fetchone()
        cursor.close()
        return row
    except Exception as e:
        st.error(f"Failed to fetch DASS-21 data: {e}")
        return None

def generate_responses_markdown(responses):
    response_values = {
        "Did not apply to me at all": 0,
        "Applied to me to some degree, or some of the time": 1,
        "Applied to me to a considerable degree, or a good part of time": 2,
        "Applied to me very much, or most of the time": 3
    }
    if not isinstance(responses, list):
        st.error("Invalid data format for responses.")
        return ""
    formatted_responses = "\n".join(
        f"<span style='color:white'>{i + 1}. \"{dass21_questions[i]}\"</span>\n"
        f"<span style='color:#AA4A44'>{entry['response']} ({response_values.get(entry['response'], 'N/A')})</span>\n"
        for i, entry in enumerate(responses)
    )
    return formatted_responses

def main():
    db = create_connection()
    appointment_id = st.session_state.get("appointment_id")

    if not appointment_id:
        st.warning("Appointment ID is missing in session state.")
        return

    data = fetch_dass21_data(db, appointment_id)
    if data:
        with st.expander('DASS-21 RESPONSES', expanded=True):
            responses = json.loads(data["responses_dict"])
            formatted = generate_responses_markdown(responses)
            st.markdown(formatted, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown(f"**Depression Score:** {data['depression_score']} | **Status:** {data['depression_status']}")
            st.markdown(f"**Anxiety Score:** {data['anxiety_score']} | **Status:** {data['anxiety_status']}")
            st.markdown(f"**Stress Score:** {data['stress_score']} | **Status:** {data['stress_status']}")
            st.markdown(f"**Total Score:** {data['total_score']}")

    else:
        st.warning("DASS-21 responses not yet filled.")

    db.close()

if __name__ == "__main__":
    main()
