DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime

# SNAP-IV-C Questionnaire questions (18 ADHD + 8 ODD)
snap_iv_c_questions = [
    # Inattention (1–9)
    "Often fails to give close attention to details or makes careless mistakes",
    "Often has difficulty sustaining attention in tasks or play activities",
    "Often does not seem to listen when spoken to directly",
    "Often does not follow through on instructions and fails to finish tasks",
    "Often has difficulty organizing tasks and activities",
    "Often avoids tasks that require sustained mental effort",
    "Often loses things necessary for tasks or activities",
    "Is often easily distracted by extraneous stimuli",
    "Is often forgetful in daily activities",
    # Hyperactivity/Impulsivity (10–18)
    "Often fidgets or squirms in seat",
    "Often leaves seat in classroom or in other situations",
    "Often runs about or climbs excessively",
    "Often has difficulty playing or engaging in leisure activities quietly",
    "Is often 'on the go' or acts as if 'driven by a motor'",
    "Often talks excessively",
    "Often blurts out answers before questions have been completed",
    "Often has difficulty awaiting turn",
    "Often interrupts or intrudes on others",
    # ODD (19–26)
    "Often loses temper",
    "Often argues with adults",
    "Often actively defies or refuses to comply with requests",
    "Often deliberately annoys people",
    "Often blames others for mistakes or misbehavior",
    "Is often touchy or easily annoyed",
    "Is often angry and resentful",
    "Is often spiteful or vindictive"
]

# Response map
response_map = {
    "Not at all": 0,
    "Several Days": 1,
    "More Than Half the Days": 2,
    "Nearly Every Day": 3
}

# ───────────────────────────────────────────────
#  Database Helpers
# ───────────────────────────────────────────────

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def create_snap_iv_c_forms_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS snap_iv_c_forms (
            appointment_id   TEXT PRIMARY KEY,
            user_id          TEXT,
            name             TEXT,
            client_type      TEXT,
            screen_type      TEXT,
            inatt_mean       REAL,
            hyper_mean       REAL,
            odd_mean         REAL,
            overall_mean     REAL,
            responses_dict   TEXT,
            assessment_date  TEXT,
            assessed_by      TEXT DEFAULT 'SELF',
            FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
        )
    """)
    db.commit()

def check_existing_entry(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM snap_iv_c_forms WHERE appointment_id = ?", (appointment_id,))
        return cursor.fetchone()[0] > 0
    except Exception as e:
        st.error(f"Error checking existing entry: {e}")
        return False
    finally:
        cursor.close()

# ───────────────────────────────────────────────
#  Scoring Logic
# ───────────────────────────────────────────────

def calculate_snap_iv_c_scores(responses):
    values = [response_map.get(r["response"], 0) for r in responses]

    inatt_values = values[:9]   # Q1-Q9
    hyper_values = values[9:18] # Q10-Q18
    odd_values   = values[18:]  # Q19-Q26

    inatt_mean = sum(inatt_values) / len(inatt_values)
    hyper_mean = sum(hyper_values) / len(hyper_values)
    odd_mean   = sum(odd_values) / len(odd_values)
    overall_mean = sum(values) / len(values)

    return inatt_mean, hyper_mean, odd_mean, overall_mean

def generate_snap_iv_c_responses_dict(responses):
    return [
        {
            "question_id": entry["question"],
            "question": snap_iv_c_questions[int(entry["question"][1:]) - 1],
            "response": entry["response"],
            "response_value": response_map.get(entry["response"], "N/A")
        }
        for entry in responses
    ]

# ───────────────────────────────────────────────
#  Insert Logic
# ───────────────────────────────────────────────

def insert_into_snap_iv_c_forms(db, appointment_id, user_id, name, client_type,
                                screen_type, inatt_mean, hyper_mean, odd_mean,
                                overall_mean, responses_dict,
                                assessment_date, assessed_by):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO snap_iv_c_forms (
                appointment_id, user_id, name, client_type, screen_type,
                inatt_mean, hyper_mean, odd_mean, overall_mean,
                responses_dict, assessment_date, assessed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_id, user_id, name, client_type, screen_type,
            inatt_mean, hyper_mean, odd_mean, overall_mean,
            json.dumps(responses_dict), assessment_date, assessed_by
        ))
        db.commit()
        st.success("SNAP-IV-C Questionnaire submitted successfully!")
    except Exception as e:
        db.rollback()
        st.error(f"❌ Could not insert responses: {e}")
    finally:
        cursor.close()

# ───────────────────────────────────────────────
#  Capture Responses
# ───────────────────────────────────────────────

def capture_snap_iv_c_responses():
    responses = []
    answered = set()
    with st.form("SNAP-IV-C Questionnaire"):
        st.write("### SNAP-IV-C Questionnaire")
        for i, question in enumerate(snap_iv_c_questions, start=1):
            st.markdown(f"<span style='color:steelblue; font-size:20px; font-weight:bold'>{i}. {question}</span>", unsafe_allow_html=True)
            selected = st.radio(
                label="",
                options=["Not Selected", "Not at all", "Several Days", "More Than Half the Days", "Nearly Every Day"],
                index=0,
                key=f"snap_q{i}"
            )
            responses.append({'question': f'Q{i}', 'response': selected})
            if selected != "Not Selected":
                answered.add(i)
        submitted = st.form_submit_button("Save responses")
        if submitted:
            if len(answered) != len(snap_iv_c_questions):
                st.warning("Please complete all questions before submitting.")
                return None
            return responses

# ───────────────────────────────────────────────
#  Fetch Appointment Data
# ───────────────────────────────────────────────

def fetch_screen_data_by_appointment_id(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT appointment_id, user_id, name, client_type, screen_type, created_by
            FROM appointments
            WHERE appointment_id = ?
            LIMIT 1
        """, (appointment_id,))
        row = cursor.fetchone()
        if not row:
            st.warning(f"No data found for appointment ID: {appointment_id}")
            return {}
        return {
            "appointment_id": row["appointment_id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "client_type": row["client_type"],
            "screen_type": row["screen_type"],
            "created_by": row["created_by"],
        }
    except Exception as e:
        st.error(f"Error fetching appointment data: {e}")
        return {}
    finally:
        cursor.close()

# ───────────────────────────────────────────────
#  Main
# ───────────────────────────────────────────────

def main():
    db = create_connection()
    create_snap_iv_c_forms_table(db)

    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.error("No appointment ID found in session.")
        st.stop()

    data = fetch_screen_data_by_appointment_id(db, appointment_id)
    if not data:
        st.stop()

    user_id = data["user_id"]
    name = data["name"]
    client_type = data["client_type"]
    screen_type = data["screen_type"]
    assessed_by = data.get("created_by", "SELF")

    responses = capture_snap_iv_c_responses()
    if responses:
        if check_existing_entry(db, appointment_id):
            st.warning("An entry for this appointment already exists.")
            return

        responses_dict = generate_snap_iv_c_responses_dict(responses)
        inatt_mean, hyper_mean, odd_mean, overall_mean = calculate_snap_iv_c_scores(responses)
        assessment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_into_snap_iv_c_forms(
            db, appointment_id, user_id, name, client_type,
            screen_type, inatt_mean, hyper_mean, odd_mean,
            overall_mean, responses_dict, assessment_date, assessed_by
        )

    db.close()

if __name__ == "__main__":
    main()
