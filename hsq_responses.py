DB_PATH = "users_db.db"
import streamlit as st
import json
import sqlite3


# ───────────────────────────────
# DB Connection
# ───────────────────────────────
def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to SQLite DB: {e}")
        return None

# ───────────────────────────────
# HSQ Questions
# ───────────────────────────────
home_questions = [
    "Difficulty following household rules",
    "Gets into frequent arguments with family members",
    "Avoids helping with household chores",
    "Has trouble maintaining a routine at home",
    "Displays anger or frustration frequently",
    "Finds it difficult to relax at home",
    "Avoids spending time with family",
    "Shows defiance or refusal to comply with instructions"
]

# ───────────────────────────────
# Fetch Responses
# ───────────────────────────────
def fetch_captured_responses(db, appointment_id):
    try:
        cursor = db.cursor()
        query = "SELECT responses_dict FROM HSQ_forms WHERE appointment_id = ?"
        cursor.execute(query, (appointment_id,))
        row = cursor.fetchone()
        cursor.close()

        if row and row["responses_dict"]:
            try:
                return json.loads(row["responses_dict"])
            except json.JSONDecodeError:
                st.error("Error decoding the HSQ responses.")
                return []
        return []
    except Exception as e:
        st.error(f"Failed to fetch Home Situations responses: {e}")
        return []

# ───────────────────────────────
# Format Responses
# ───────────────────────────────
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

    formatted_list = []
    for i, entry in enumerate(answered_questions):
        question_text = home_questions[i] if i < len(home_questions) else f"Question {i+1}"
        response = entry.get('response', 'N/A')
        score = response_values.get(response, 'N/A')
        formatted_list.append(
            f"<span style='color:white'>{i + 1}. {question_text}</span>"
            f"<span style='color:#AA4A44'>Response: {response} (Score: {score})</span>"
        )

    return "<br><br>".join(formatted_list)

# ───────────────────────────────
# Main
# ───────────────────────────────
def main():
    db = create_connection()
    if db is None:
        return

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.warning("Appointment ID is missing in session state.")
        db.close()
        return

    responses = fetch_captured_responses(db, appointment_id)
    if responses:
        with st.expander('HOME SITUATIONS RESPONSES', expanded=True):
            formatted = generate_responses_markdown(responses)
            st.markdown(formatted, unsafe_allow_html=True)
    else:
        st.warning("Home Situations responses not yet filled.")

    db.close()

if __name__ == "__main__":
    main()
