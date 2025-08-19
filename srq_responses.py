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

srq_questions = [
    "Do you often have headaches?",
    "Is your appetite poor?",
    "Do you sleep badly?",
    "Are you easily frightened?",
    "Do your hands shake?",
    "Do you feel nervous, tense, or worried?",
    "Is your digestion poor?",
    "Do you have trouble thinking clearly?",
    "Do you feel unhappy?",
    "Do you cry more than usual?",
    "Do you find it difficult to enjoy your daily activities?",
    "Do you find it difficult to make decisions?",
    "Is your daily work suffering?",
    "Are you unable to play a useful part in life?",
    "Have you lost interest in things?",
    "Do you feel that you are a worthless person?",
    "Has the thought of ending your life been on your mind?",
    "Do you feel tired all the time?",
    "Do you have uncomfortable feelings in your stomach?",
    "Are you easily tired?"
]

def fetch_captured_responses(db, action_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT responses_dict FROM SRQ_forms WHERE action_id = ?", (action_id,))
        row = cursor.fetchone()
        cursor.close()
        if row and row["responses_dict"]:
            return json.loads(row["responses_dict"])
        return []
    except Exception as e:
        st.error(f"Failed to fetch SRQ responses: {e}")
        return []

def generate_responses_markdown(answered_questions):
    response_values = {
        "No": 0,
        "Yes": 1
    }
    formatted = "\n".join(
        f"<span style='color:white'>{i+1}. \"{srq_questions[i]}\"</span>\n"
        f"<span style='color:#AA4A44'>{entry['response']} ({response_values.get(entry['response'], 'N/A')})</span>\n"
        for i, entry in enumerate(answered_questions)
    )
    return formatted

def main():
    db = create_connection()
    action_id = st.session_state.get("action_id")
    if action_id:
        responses = fetch_captured_responses(db, action_id)
        if responses:
            with st.expander("SRQ RESPONSES", expanded=True):
                st.markdown(generate_responses_markdown(responses), unsafe_allow_html=True)
        else:
            st.warning("SRQ responses not yet filled.")
    else:
        st.warning("Screen ID is missing in session state.")
    db.close()

if __name__ == "__main__":
    main()
