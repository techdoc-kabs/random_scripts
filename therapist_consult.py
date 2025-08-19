DB_PATH = "users_db.db"
import streamlit as st
import json
import pandas as pd
import os
import importlib
from datetime import datetime
import phq9_qn
import gad7_qn, caps_responses, snap_responses, ssq_responses, hsq_responses, ssq_qn, snap,hsq_qn
import bcrypt
import base64
from streamlit_card import card
import sqlite3

import bcrypt
from streamlit_option_menu import option_menu
from streamlit_javascript import st_javascript
import phq9_responses, gad7_responses, dass21_responses, dass21_qn, phq4_qn, phq4_responses, caps_form
import json
import session_notes
DB = "users_db.db"
###### DESIGNS S#####

def set_full_page_background(image_path):
    try:
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found.")
            return

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        st.markdown(
            f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Error setting background: {e}")

def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None



######## FETCHT REQUESTED TOOLS ########

def fetch_requested_tools(db, appointment_id):
    table_name = "appointments"
    if not table_exists(db, table_name):
        st.warning(f"Table '{table_name}' does not exist.")
        return {}
    try:
        cursor = db.cursor()
        fetch_query = """
            SELECT screening_tools
            FROM appointments
            WHERE appointment_id = ?
            AND actions LIKE '%"screen": true%'
            ORDER BY appointment_id DESC
            LIMIT 1
        """
        cursor.execute(fetch_query, (appointment_id,))
        result = cursor.fetchone()
        if not result:
            return {}

        screening_tools_json = result["screening_tools"]
        tools_dict = json.loads(screening_tools_json) if screening_tools_json else {}
        tools_status = {tool: info.get("status", "Pending") for tool, info in tools_dict.items()}
        return tools_status

    except Exception as e:
        st.error(f"Database error fetching requested tools: {e}")
        return {}
    finally:
        cursor.close()

##### UPDATE REUESTED TOOLS ######
def update_tool_status(db, appointment_id, tool_name, new_status):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT screening_tools FROM appointments WHERE appointment_id = ?", (appointment_id,))
        row = cursor.fetchone()
        tools_dict = json.loads(row["screening_tools"] or '{}') if row else {}

        if tool_name in tools_dict:
            tools_dict[tool_name]["status"] = new_status
            tools_dict[tool_name]["response_date"] = datetime.today().strftime("%Y-%m-%d")
        else:
            tools_dict[tool_name] = {
                "status": new_status,
                "response_date": datetime.today().strftime("%Y-%m-%d"),
                "scheduled_date": datetime.today().strftime("%Y-%m-%d")}

        cursor.execute("UPDATE appointments SET screening_tools = ? WHERE appointment_id = ?",
                       (json.dumps(tools_dict), appointment_id))
        db.commit()
        return True
    except Exception as e:
        st.error(f"Failed to update tool status: {e}")
        return False
    finally:
        cursor.close()


###### FETCH THERPISTS COSULTS ####3

def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None

def get_available_client_types(db):
    query = "SELECT DISTINCT client_type FROM appointments WHERE client_type IS NOT NULL"
    df = pd.read_sql(query, db)
    types = df["client_type"].dropna().unique().tolist()
    types.sort()
    return ["All"] + types



def fetch_clients_by_search(db, therapist_name, search_input, selected_client_type, action_filter=None):
    cursor = db.cursor()
    query = """
        SELECT appointment_id, user_id, name, client_type, actions, assigned_therapist, appointment_date
        FROM appointments
        WHERE assigned_therapist LIKE ?
    """
    params = [f'%"{therapist_name}"%']
    if selected_client_type != "All":
        query += " AND client_type = ?"
        params.append(selected_client_type)

    cursor.execute(query, tuple(params))
    appointments = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    def therapist_assigned_to_action(assigned_str):
        try:
            assigned = json.loads(assigned_str) if assigned_str else {}
            if action_filter is None:
                return any(therapist_name in therapists for therapists in assigned.values())
            else:
                return therapist_name in assigned.get(action_filter, [])
        except:
            return False
    def action_is_true(actions_str):
        try:
            actions = json.loads(actions_str) if actions_str else {}
            return actions.get(action_filter, False) is True if action_filter else True
        except:
            return False
    filtered = []
    for row in appointments:
        appt = dict(zip(columns, row))
        if action_filter: 
            if therapist_assigned_to_action(appt.get("assigned_therapist", "")) and action_is_true(appt.get("actions", "")):
                filtered.append(appt)
        else:
            filtered.append(appt) 
    final_results = []
    for appt in filtered:
        user_id = appt['user_id']
        cursor.execute("SELECT age, sex, class, stream FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        if user_row:
            appt.update({
                "age": user_row[0],
                "sex": user_row[1],
                "class": user_row[2],
                "stream": user_row[3],
                "full_name": appt["name"],
            })
        else:
            appt.update({
                "age": "N/A",
                "sex": "N/A",
                "class": "N/A",
                "stream": "N/A",
                "full_name": appt["name"],
            })
        final_results.append(appt)
    if search_input.strip():
        term = search_input.strip().lower()
        final_results = [
            r for r in final_results
            if term in str(r["appointment_id"]).lower() or term in r["full_name"].lower()]
    return final_results



def fetch_therapist_clients_by_action(therapist_name, action_filter=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM appointments WHERE assigned_therapist LIKE ?"
    param = f'%"{therapist_name}"%'
    df = pd.read_sql(query, conn, params=(param,))
    conn.close()
    def therapist_assigned(assigned_json):
        try:
            assigned = json.loads(assigned_json) if isinstance(assigned_json, str) else {}
            if action_filter is None:
                return any(therapist_name in v for v in assigned.values())
            else:
                return therapist_name in assigned.get(action_filter, [])
        except Exception:
            return False
    def action_is_true(actions_json):
        try:
            actions = json.loads(actions_json) if isinstance(actions_json, str) else {}
            if action_filter is None:
                return True  # No filtering on action
            return actions.get(action_filter, False) is True
        except Exception:
            return False
    filtered_df = df[df['assigned_therapist'].apply(therapist_assigned) & df['actions'].apply(action_is_true)]
    filtered_df.index = range(1, len(filtered_df) + 1)
    return filtered_df


def fetch_appointment_by_name_and_therapist(name, therapist):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM appointments WHERE name = ?", (name,))
    rows = cursor.fetchall()

    col_names = [description[0] for description in cursor.description]
    conn.close()

    for row in rows:
        row_dict = dict(zip(col_names, row))

        try:
            actions = json.loads(row_dict.get("actions", "{}"))
            assigned = json.loads(row_dict.get("assigned_therapist", "{}"))

            consult_true = actions.get("consult") == True
            therapist_assigned = therapist in assigned.get("consult", [])

            if consult_true and therapist_assigned:
                return row_dict  # ✅ Return first match immediately

        except json.JSONDecodeError:
            continue

    return None 


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
from datetime import datetime
import json

def update_consult_completion_status(conn, appointment_id, new_status):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT statuses FROM appointments WHERE appointment_id = ?", (appointment_id,))
        row = cursor.fetchone()
        if not row:
            return False

        statuses_raw = row[0] or "{}"
        try:
            statuses = json.loads(statuses_raw) if isinstance(statuses_raw, str) else statuses_raw
        except:
            statuses = {}
        if not isinstance(statuses.get("consult"), dict):
            statuses["consult"] = {}
        statuses["consult"]["status"] = new_status
        if new_status == "Complete":
            statuses["consult"]["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            statuses["consult"]["completed_at"] = None
        cursor.execute(
            "UPDATE appointments SET statuses = ? WHERE appointment_id = ?",
            (json.dumps(statuses), appointment_id)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating consult status: {e}")
        return False
    finally:
        cursor.close()


def main():
    default_keys = {
        "results": [],
        "appointment_id": None,
        "selected_record": None,
        "selected_appointment": None,
        "selected_tool": None,
        "selected_page": "screening_menu",
        "last_search_input": "",
        "open_records": {}
    }
    for key, default in default_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default
    db = create_connection()
    set_full_page_background('images/black_strip.jpg')
    username = st.session_state.get("user_name")
    therapist_name = username
    if not therapist_name:
        st.error("Therapist full name not found.")
        return

    device_width = st_javascript("window.innerWidth", key="device_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = 3 if not is_mobile else 1
    appointment_card_height = "150px" if is_mobile else "200px"
    appointment_card_width = "100%"
    appointment_font_size_title = "18px" if is_mobile else "22px"
    appointment_font_size_text = "16px" if is_mobile else "18px"
    num_cols_tool = 3 if not is_mobile else 1
    tool_card_width = "100%"
    tool_card_height = "100px" if is_mobile else "150px"
    tool_font_size_title = "20px" if is_mobile else "30px"
    tool_font_size_text = "16px" if is_mobile else "20px"
    client_types = get_available_client_types(db)
    df = fetch_therapist_clients_by_action(username, action_filter='consult')
    with st.expander('APPOINTMENTS', expanded=True):
        if not df.empty:
            st.markdown("""
            <style>
            .header-row {
                background-color: #1565c0;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 20px;
            }
            .data-row {
                padding: 6px 10px;
                border-radius: 5px;
            }
            .row-even { background-color: #2c2c2c; }
            .row-odd { background-color: #1e1e1e; }
            .status-complete { color: #2ecc71; font-weight: bold; }
            .status-pending { color: #e67e22; font-weight: bold; }
            </style>
            """, unsafe_allow_html=True)
            with st.sidebar.expander('FILTER OPTIONS', expanded=True):
                selected_client_type = st.selectbox("Client Type", client_types)
                status_filter = st.selectbox("🔎 Filter by Status", ["All", "Pending", "Completed"], index=0)
            header = st.columns([2, 1.5, 1.8, 0.8, 0.8])
            header[0].markdown("<div class='header-row'>👤 Client Name</div>", unsafe_allow_html=True)
            header[1].markdown("<div class='header-row'>📋 Status</div>", unsafe_allow_html=True)
            header[2].markdown("<div class='header-row'>🕒 Completed At</div>", unsafe_allow_html=True)
            header[4].markdown("<div class='header-row'>⚙️ Action</div>", unsafe_allow_html=True)
            header[3].markdown("<div class='header-row'>📄 File</div>", unsafe_allow_html=True)
            for idx, row in enumerate(df.itertuples(index=False)):
                appointment_id = row.appointment_id
                name = row.name
                raw_statuses = getattr(row, "statuses", "{}") or "{}"
                if isinstance(raw_statuses, dict):
                    status_dict = raw_statuses
                else:
                    try:
                        loaded = json.loads(raw_statuses)
                        status_dict = loaded if isinstance(loaded, dict) else {}
                    except Exception:
                        status_dict = {}

                # Ensure "consult" is a dictionary
                consult_data = status_dict.get("consult")
                if not isinstance(consult_data, dict):
                    consult_data = {}
                    status_dict["consult"] = consult_data

                current_status = consult_data.get("status", "Pending")
                is_complete = current_status == "Complete"
                completed_at = consult_data.get("completed_at")

                # --- Apply status filter ---
                if status_filter == "Pending" and is_complete:
                    continue
                if status_filter == "Complete" and not is_complete:
                    continue

                display_status = "✅ Completed" if is_complete else "⏳ Pending"
                status_class = "status-complete" if is_complete else "status-pending"
                completed_display = completed_at if (is_complete and completed_at and completed_at.lower() != "none") else "-"
                row_class = "row-even" if idx % 2 == 0 else "row-odd"

                row_cols = st.columns([2, 1.5, 1.8, 0.8, 0.8])
                with row_cols[0]:
                    st.markdown(f"<div class='data-row {row_class}' style='color:#ecf0f1;'>{name}</div>", unsafe_allow_html=True)
                with row_cols[1]:
                    st.markdown(f"<div class='data-row {row_class}'><span class='{status_class}'>{display_status}</span></div>", unsafe_allow_html=True)
                with row_cols[2]:
                    st.markdown(f"<div class='data-row {row_class}' style='color:#bdc3c7;'>{completed_display}</div>", unsafe_allow_html=True)

                # --- Action Buttons ---
                with row_cols[4]:
                    if is_complete:
                        if st.button("↩️ Undo", key=f"undo_{appointment_id}"):
                            update_consult_completion_status(db, appointment_id, "Pending")
                            st.warning(f"{appointment_id} reverted to ⏳ Pending")
                            st.rerun()
                    else:
                        if st.button("✅ Finish", key=f"finish_{appointment_id}"):
                            update_consult_completion_status(db, appointment_id, "Complete")
                            st.success(f"{appointment_id} marked as ✅ Completed")
                            st.rerun()

                # --- Open/Close Record ---
                with row_cols[3]:
                    record_key = str(appointment_id)
                    is_open = st.session_state.open_records.get(record_key, False)
                    toggle_btn_label = "🔁 Close" if is_open else "🔗 Open"
                    if st.button(toggle_btn_label, key=f"toggle_open_{appointment_id}"):
                        if is_open:
                            st.session_state.open_records[record_key] = False
                            st.session_state["results"] = []  # Clear results
                            st.session_state["appointment_id"] = None
                            st.session_state.selected_tool = None
                        else:
                            st.session_state.open_records[record_key] = True
                        st.rerun()

                # --- Fetch Results if Record is Open ---
                if st.session_state.open_records.get(str(appointment_id), False):
                    results = fetch_clients_by_search(db, therapist_name, name, selected_client_type)
                    if results:
                        st.session_state["results"] = results
                        st.session_state["appointment_id"] = appointment_id  # Store appointment_id

    # --- Display Student Profile & Tools ---
    if st.session_state["results"] and len(st.session_state["results"]) > 0:
        selected_record = st.session_state["results"]

        def format_line(label, value):
            return f"<div style='margin-bottom:6px;'><span style='color:#c0392b; font-weight:bold;'>{label}:</span> <span style='color:#27ae60;'>{value}</span></div>"

        profile_html = ""
        profile_fields = [
            ("Student ID", selected_record[0]['user_id']),
            ("Appointment ID", selected_record[0]['appointment_id']),
            ("Appointment date", selected_record[0]['appointment_date']),
            ("Name", selected_record[0]['full_name']),
            ("Age", f"{selected_record[0]['age']} Years"),
            ("Gender", selected_record[0]['sex']),
            ("Class", selected_record[0]['class']),
            ("Stream", selected_record[0]['stream']),
        ]
        for label, value in profile_fields:
            profile_html += format_line(label, value)

        # Show profile
        if is_mobile:
            with st.expander("STUDENT PROFILE", expanded=True):
                st.markdown(profile_html, unsafe_allow_html=True)
        else:
            with st.sidebar.expander("STUDENT PROFILE", expanded=True):
                st.markdown(profile_html, unsafe_allow_html=True)

        # --- Appointment details ---
        appointment_id = st.session_state.get("appointment_id")
        if appointment_id:
            task_reslt = option_menu(
                menu_title='',
                orientation='horizontal',
                menu_icon='',
                options=['Screen', 'Results', 'Notes'],
                icons=['book', 'bar-chart', 'printer'],
                styles={
                    "container": {"padding": "8!important", "background-color": 'black', 'border': '0.01px dotted red'},
                    "icon": {"color": "red", "font-size": "15px"},
                    "nav-link": {"color": "#d7c4c1", "font-size": "15px", "font-weight": 'bold', "text-align": "left", "margin": "0px", "--hover-color": "red"},
                    "nav-link-selected": {"background-color": "green"},
                },
                key="task_reslt"
            )

            if task_reslt == 'Screen':
                screen_men = st.tabs(['ASSESSEMENTS', 'ADMINSITER_TOOL'])
                with screen_men[0]:
                    import tool_responses
                    tool_responses.main()
                with screen_men[1]:
                    import therapist_screen
                    therapist_screen.main()

            elif task_reslt == 'Results':
                import screen_results
                screen_results.main()

            elif task_reslt == 'Notes':
                session_notes.main()
        else:
            st.error("No appointment_id found in session.")
    db.close()


if __name__ == '__main__':
    main()
