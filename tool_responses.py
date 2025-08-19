DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
import phq9_qn, gad7_qn, dass21_qn, phq4_qn, bdi_qn, srq_qn
import phq9_responses, gad7_responses, dass21_responses, phq4_responses, bdi_responses, srq_responses
import os, base64, caps_form
import caps_responses, snap_responses, ssq_responses, hsq_responses, ssq_qn, snap,hsq_qn

def set_full_page_background(image_path):
    try:
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found.")
            return

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        st.markdown(f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error setting background: {e}")

# -------------------- DB Connection --------------------
def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row 
        return db
    except sqlite3.Error as e:
        st.error(f"Database connection failed: {e}")
        return None



import json
import streamlit as st

def fetch_requested_tools(db, appointment_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT screening_tools FROM appointments
        WHERE appointment_id = ?
    """, (appointment_id,))
    row = cursor.fetchone()

    if row:
        try:
            screening_tools_raw = row[0]
            screening_tools = json.loads(screening_tools_raw) if isinstance(screening_tools_raw, str) else screening_tools_raw

            tools = list(screening_tools.keys())
            tool_statuses = screening_tools

            return tools, tool_statuses

        except Exception as e:
            st.error(f"Error parsing screening_tools: {e}")
            return [], {}
    return [], {}




tools_template_dict = {
    'PHQ-9': phq9_qn.main,
    'GAD-7':gad7_qn.main,
    'DASS-21': dass21_qn.main,
    'PHQ-4': phq4_qn.main,
    'CAPS-14':caps_form.main,
    'SSQ':ssq_qn.main,
    'HSQ':hsq_qn.main,
    'SNAP-IV-C': snap.main,
}
tool_modules = {
    'PHQ-9': phq9_responses.main,
    'GAD-7':gad7_responses.main,
    'Functioning': 'Noted',
    'DASS-21': dass21_responses.main, 
    'PHQ-4':phq4_responses.main,

    'CAPS-14': caps_responses.main,
    'SSQ':ssq_responses.main,
    'HSQ':hsq_responses.main,
    'SNAP-IV-C': snap_responses.main,}


def update_tool_status_in_appointments(db, appointment_id, tool_name, new_status):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT screening_tools FROM appointments WHERE appointment_id = ?", (appointment_id,))
        row = cursor.fetchone()

        if row:
            screening_tools_raw = row[0]
            screening_tools = json.loads(screening_tools_raw) if isinstance(screening_tools_raw, str) else screening_tools_raw

            if tool_name in screening_tools:
                screening_tools[tool_name]["status"] = new_status
                cursor.execute("""
                    UPDATE appointments SET screening_tools = ? WHERE appointment_id = ?
                """, (json.dumps(screening_tools), appointment_id))
                db.commit()
                return True
            else:
                st.warning(f"Tool '{tool_name}' not found in appointment.")
    except Exception as e:
        st.error(f"Failed to update tool status: {e}")

    return False


# -------------------- Check if Tool is Completed --------------------
def is_tool_completed(db, tool, appointment_id):
    table_map = {
        "PHQ-4": "PHQ4_forms",
        "PHQ-9": "PHQ9_forms",
        "GAD-7": "GAD7_forms",
        "DASS-21": "DASS21_forms", 
        "BDI": "BDI_forms", 
        "SRQ": "SRQ_forms",
        "CAPS-14": "CAPS_forms",
        "HSQ": "HSQ_forms",
        "SSQ": "SSQ_forms",
        "SNAP-IV-C": "SNAPIVC_forms"}

    table_name = table_map.get(tool)
    if not table_name:
        return False
    try:
        cursor = db.cursor()
        cursor.execute(f"""
            SELECT responses_dict FROM {table_name}
            WHERE appointment_id = ?
        """, (appointment_id,))
        row = cursor.fetchone()
        return bool(row and row["responses_dict"])
    except Exception as e:
        pass
    return False


# -------------------- Main Interface --------------------
def main():
    db = create_connection()
    appointment_id = st.session_state.get("appointment_id")
    if not appointment_id:
        st.warning("No appointment_id found in session.")
        return
    set_full_page_background('images/black_strip.jpg')
    tools, tool_statuses = fetch_requested_tools(db, appointment_id)
    
    if not tools:
        st.warning("No tools assigned.")
        return
    for tool in tools:
        if tool_statuses.get(tool) != "Completed" and is_tool_completed(db, tool, appointment_id):
            update_tool_status_in_appointments(db, appointment_id, tool, "Completed")
            tool_statuses[tool] = "Completed"

    tabs = st.tabs(tools)
    for idx, tool in enumerate(tools):
        with tabs[idx]:
            status = tool_statuses.get(tool, "Pending")
            if status == "Completed":
                response_func = tool_modules.get(tool)
                if response_func:
                    response_func()
                else:
                    st.warning("No response module found.")
            else:
                fill_func = tools_template_dict.get(tool)
                if fill_func:
                    submitted = fill_func()
                    if submitted:
                        update_tool_status_in_appointments(db, appointment_id, tool, "Completed")
                        tool_statuses[tool] = "Completed"
                        st.success(f"{tool} marked as Completed. Refresh to view response.")
                else:
                    st.warning("No form template found for this tool.")

    db.close()
if __name__ == "__main__":
    main()
