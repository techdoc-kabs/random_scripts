import streamlit as st
import sqlite3
DB_PATH = "users_db.db"
import json

caps_items = [
    "Persistent sadness or irritability", "Loss of interest in favorite activities",
    "Excessive worry or fear", "Difficulty concentrating",
    "Sleep problems (too little / too much)", "Significant change in appetite or weight",
    "Frequent headaches or stomach aches", "Social withdrawal",
    "Thoughts of self‑harm", "Hyperactivity or impulsivity",
    "Oppositional or defiant behavior", "Substance use",
    "Experiencing bullying or violence", "Family history of mental illness"
]

response_map = {"No": 0, "Yes": 1}

def create_connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.row_factory = sqlite3.Row
    return db

def fetch_caps_data(db, appointment_id):
    try:
        query = "SELECT responses_dict, total_score, risk_level FROM CAPS_forms WHERE appointment_id = ?"
        row = db.execute(query, (appointment_id,)).fetchone()
        if row:
            responses = json.loads(row["responses_dict"])
            return responses, row["total_score"], row["risk_level"]
        return [], None, None
    except Exception as e:
        st.error(f"❌ Error fetching CAPS‑14 data: {e}")
        return [], None, None

def generate_responses_markup(responses):
    if not isinstance(responses, list):
        return ""
    return "\n".join(
        f"<span style='color:white'>{i + 1}. “{caps_items[i]}”</span><br>"
        f"<span style='color:#AA4A44'>{entry['response']} ({response_map.get(entry['response'], 'N/A')})</span><br><br>"
        for i, entry in enumerate(responses)
    )

def main():
    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.warning("⚠️ Appointment ID missing in session.")
        return

    db = create_connection()
    responses, total_score, risk_level = fetch_caps_data(db, appointment_id)
    db.close()

    if responses:
        with st.expander("🧠 CAPS‑14 RESPONSES", expanded=True):
            st.markdown(generate_responses_markup(responses), unsafe_allow_html=True)
            st.write("---")
            st.write(f"**Total Score:** {total_score} | **Risk Level:** *{risk_level}*")
    else:
        st.warning("⚠️ CAPS‑14 responses not yet filled.")

if __name__ == "__main__":
    main()
