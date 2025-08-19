import streamlit as st
import json
import sqlite3
DB_PATH = "users_db.db"

def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row 
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to SQLite DB: {e}")
        return None

bdi_questions = [
    "Sadness",
    "Pessimism",
    "Past Failure",
    "Loss of Pleasure",
    "Guilty Feelings",
    "Punishment Feelings",
    "Self-Dislike",
    "Self‑Criticalness",
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

def fetch_captured_responses(db, action_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT responses_dict FROM BDI_forms WHERE action_id = ?", (action_id,))
        row = cursor.fetchone()
        cursor.close()
        if row and row["responses_dict"]:
            return json.loads(row["responses_dict"])
        return []
    except Exception as e:
        st.error(f"Failed to fetch responses: {e}")
        return []

def generate_responses_markdown(answered_questions):
    response_values = {
        "Not at all": 0,
        "Mildly; it didn’t bother me much": 1,
        "Moderately; I felt like I had to put in a little effort": 2,
        "Severely; I could barely stand it": 3
    }
    formatted = "\n".join(
        f"<span style='color:white'>{i+1}. \"{bdi_questions[i]}\"</span>\n"
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
            with st.expander("BDI-II RESPONSES", expanded=True):
                st.markdown(generate_responses_markdown(responses), unsafe_allow_html=True)
        else:
            st.warning("BDI-II responses not yet filled.")
    else:
        st.warning("Screen ID is missing in session state.")
    db.close()

if __name__ == "__main__":
    main()
