DB_PATH = "users_db.db"
import streamlit as st
import json
import sqlite3

import pandas as pd

def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row 
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to SQLite DB: {e}")
        return None

snap_iv_c_questions = [
    "Often fails to give close attention to details or makes careless mistakes",
    "Often has difficulty sustaining attention in tasks or play activities",
    "Often does not seem to listen when spoken to directly",
    "Often does not follow through on instructions and fails to finish tasks",
    "Often has difficulty organizing tasks and activities",
    "Often avoids tasks that require sustained mental effort",
    "Often loses things necessary for tasks or activities",
    "Is often easily distracted by extraneous stimuli",
    "Is often forgetful in daily activities",
    "Often fidgets or squirms in seat",
    "Often leaves seat in classroom or in other situations",
    "Often runs about or climbs excessively",
    "Often has difficulty playing or engaging in leisure activities quietly",
    "Is often 'on the go' or acts as if 'driven by a motor'",
    "Often talks excessively",
    "Often blurts out answers before questions have been completed",
    "Often has difficulty awaiting turn",
    "Often interrupts or intrudes on others",
    "Often loses temper",
    "Often argues with adults",
    "Often actively defies or refuses to comply with requests",
    "Often deliberately annoys people",
    "Often blames others for mistakes or misbehavior",
    "Is often touchy or easily annoyed",
    "Is often angry and resentful",
    "Is often spiteful or vindictive"
]

def fetch_captured_responses(db, appointment_id):
    try:
        cursor = db.cursor()
        query = """
            SELECT responses_dict, inatt_mean, hyper_mean, odd_mean, overall_mean
            FROM snap_iv_c_forms 
            WHERE appointment_id = ?
        """
        cursor.execute(query, (appointment_id,))
        row = cursor.fetchone()
        cursor.close()

        if row:
            responses = []
            try:
                responses = json.loads(row["responses_dict"]) if row["responses_dict"] else []
            except json.JSONDecodeError:
                st.error("Error decoding the responses.")
            return responses, row["inatt_mean"], row["hyper_mean"], row["odd_mean"], row["overall_mean"]

        return [], None, None, None, None
    except Exception as e:
        st.error(f"Failed to fetch SNAP-IV-C responses: {e}")
        return [], None, None, None, None

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
        f"<span style='color:white'>{i + 1}. \"{snap_iv_c_questions[i]}\"</span><br>"
        f"<span style='color:#AA4A44'>{entry['response']} ({response_values.get(entry['response'], 'N/A')})</span><br>"
        for i, entry in enumerate(answered_questions)
    )
    return formatted_responses

def main():
    db = create_connection()
    appointment_id = st.session_state.get("appointment_id")

    if appointment_id:
        responses, inatt_mean, hyper_mean, odd_mean, overall_mean = fetch_captured_responses(db, appointment_id)
        if responses:
            with st.expander('SNAP-IV-C RESPONSES', expanded=True):
                # Display summary table
                summary_df = pd.DataFrame([{
                    "Inattention Mean": inatt_mean,
                    "Hyperactivity Mean": hyper_mean,
                    "Oppositional Mean": odd_mean,
                    "Overall Mean": overall_mean
                }])
                st.table(summary_df)

                # Display responses
                formatted = generate_responses_markdown(responses)
                st.markdown(formatted, unsafe_allow_html=True)
        else:
            st.warning("SNAP-IV-C responses not yet filled.")
    else:
        st.warning("Appointment ID is missing in session state.")
    db.close()

if __name__ == "__main__":
    main()
