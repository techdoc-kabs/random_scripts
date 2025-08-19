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


## HELPER FXNS  #######
def styled_tasks_heading():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #6EE7B7, #3B82F6, #9333EA, #F59E0B);
        width: 100%;
        padding: 1.2rem 0.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        margin-bottom: 1rem;
        animation: fadeIn 5s ease-in-out;
    ">
        <h3 style="
            font-size: 2.3rem;
            font-family: 'Trebuchet MS', sans-serif;
            color: #ffffff;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            margin: 0;
        ">📝 TASKS</h3>
        <p style="
            font-size: 1.1rem;
            color: #f0f8ff;
            margin-top: 0.4rem;
            font-style: italic;
        ">Stay on track. Complete your screenings, view progress, and take action!</p>
    </div>

    <style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)
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


def check_existing_entry(db, appointment_id):
    try:
        cursor = db.cursor()
        query = "SELECT COUNT(*) FROM PHQ_9forms WHERE appointment_id = ?"
        cursor.execute(query, (appointment_id,))
        result = cursor.fetchone()[0]
        return result > 0
    except Exception as e:
        st.error(f"An error occurred while checking for duplicates: {e}")
        return False
    finally:
        cursor.close()


def check_functioning_completed(db, appointment_id):
    cursor = db.cursor()
    query = "SELECT difficulty_level FROM functioning_responses WHERE appointment_id = ?"
    cursor.execute(query, (appointment_id,))
    result = cursor.fetchone()
    cursor.close()
    return result


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def table_exists(db, table_name):
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    result = cursor.fetchone()
    cursor.close()
    return result is not None


#### FXNING RESPONSES ########

def create_functioning_responses_table(db):
    cursor = db.cursor()
    create_table_query = """
        CREATE TABLE IF NOT EXISTS functioning_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            difficulty_level TEXT NOT NULL CHECK(difficulty_level IN ('Not difficult at all', 'Somewhat difficult', 'Very difficult', 'Extremely difficult')),
            fnx_score INTEGER NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    try:
        cursor.execute(create_table_query)
        db.commit()
        print("Table 'functioning_responses' ensured.")
    except Exception as err:
        print(f"Error creating table: {err}")
    finally:
        cursor.close()



def insert_functioning_response(db, appointment_id, user_id, difficulty_level):
    cursor = db.cursor()
    difficulty_to_score = {
        "Extremely difficult": 1,
        "Very difficult": 2,
        "Somewhat difficult": 3,
        "Not difficult at all": 4
    }
    fnx_score = difficulty_to_score.get(difficulty_level)
    if fnx_score is None:
        st.error("Invalid difficulty level.")
        return False

    insert_query = """
    INSERT INTO functioning_responses (appointment_id, user_id, difficulty_level, fnx_score)
    VALUES (?, ?, ?, ?)
    """
    try:
        cursor.execute(insert_query, (appointment_id, user_id, difficulty_level, fnx_score))
        db.commit()
        return True
    except Exception as err:
        st.error(f"Error inserting response: {err}")
        return False
    finally:
        cursor.close()




tool_modules = {
    'PHQ-9': phq9_qn.main,
    'GAD-7':gad7_qn.main,
    'DASS-21': dass21_qn.main,
    'PHQ-4': phq4_qn.main,

    'CAPS-14':caps_form.main,
    'SSQ':ssq_qn.main,
    'HSQ':hsq_qn.main,
    'SNAP-IV-C': snap.main,
}
response_modules = {
    'PHQ-9': phq9_responses.main,
    'GAD-7':gad7_responses.main,
    'Functioning': 'Noted',
    'DASS-21': dass21_responses.main, 
    'PHQ-4':phq4_responses.main,

     'CAPS-14':caps_responses.main,
    'SSQ':ssq_responses.main,
    'HSQ':hsq_responses.main,
    'SNAP-IV-C':snap_responses.main,}


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
        "SNAP-IV-C": "SNAPIVC_forms"
    }
    table_name = table_map.get(tool)
    if not table_name:
        return False
    try:
        cursor = db.cursor()
        cursor.execute(f"SELECT responses_dict FROM {table_name} WHERE appointment_id = ?", (appointment_id,))
        row = cursor.fetchone()
        return bool(row and row["responses_dict"])
    except Exception:
        return False

def parse_screening_tools(screening_json):
    try:
        tools = json.loads(screening_json)
        return {tool: data.get("status", "Pending") for tool, data in tools.items()}
    except Exception:
        return {}


def display_functioning_questionnaire(db, appointment_id, student_id):
    completed_response = check_functioning_completed(db, appointment_id)
    if completed_response:
        st.success(f"Functioning completed ✅")
    else:
        st.info("If you checked off any problems, how difficult have these problems made it for you?")
        difficulty_level = st.radio(
            "Choose difficulty level:",
            ('Not difficult at all', 'Somewhat difficult', 'Very difficult', 'Extremely difficult'))

        if st.button("Submit Functioning Response"):
            success = insert_functioning_response(db, appointment_id, student_id, difficulty_level)
            if success:
                st.success("Functioning response recorded successfully ✅!")
                st.rerun() 

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

def parse_screening_tools(screening_json):
    try:
        tools = json.loads(screening_json)
        return {tool: data.get("status", "Pending") for tool, data in tools.items()}
    except Exception:
        return {}
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
                "scheduled_date": datetime.today().strftime("%Y-%m-%d")
            }

        cursor.execute("UPDATE appointments SET screening_tools = ? WHERE appointment_id = ?",
                       (json.dumps(tools_dict), appointment_id))
        db.commit()
        return True
    except Exception as e:
        st.error(f"Failed to update tool status: {e}")
        return False
    finally:
        cursor.close()

def get_requested_tools(db, appointment_id):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT screening_tools FROM appointments
            WHERE appointment_id = ? AND actions LIKE '%"screen": true%'
            ORDER BY appointment_id DESC
            LIMIT 1
        """, (appointment_id,))
        row = cursor.fetchone()
        if row:
            tools_json = row["screening_tools"]
            if tools_json:
                tools_dict = json.loads(tools_json)
                return {tool: info.get("status", "Pending") for tool, info in tools_dict.items()}
        return {}
    except Exception as e:
        st.error(f"Error fetching requested tools: {e}")
        return {}
    finally:
        cursor.close()

def parse_screening_tools(screening_json):
    try:
        tools = json.loads(screening_json)
        return {tool: data.get("status", "Pending") for tool, data in tools.items()}
    except Exception:
        return {}

def fetch_appointments_details_by_username(username):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                SELECT 
                    s.appointment_id, s.user_id, s.name, s.appointment_type, s.screen_type, s.term,
                    s.appointment_date, s.appointment_time,
                    s.class, s.stream, s.client_type, s.actions,
                    s.assigned_therapist, s.screening_tools
                FROM appointments s
                JOIN users u ON s.user_id = u.user_id
                WHERE u.username = ? AND s.actions LIKE '%"screen": true%'
                ORDER BY s.created_at DESC
            """

            cursor.execute(query, (username,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            records = []
            for row in rows:
                record = dict(zip(columns, row))
                try:
                    record["tools_statuses"] = parse_screening_tools(record["screening_tools"])
                except Exception as e:
                    st.warning(f"Failed to parse screening_tools for appointment_id {record['appointment_id']}: {e}")
                    record["tools_statuses"] = {}
                records.append(record)
            return records
        except Exception as e:
            st.error(f"Error fetching screening data: {e}")
        finally:
            cursor.close()
            connection.close()
    return []


def update_screen_action_status(db, appointment_id):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT screening_tools, statuses FROM appointments WHERE appointment_id = ?", (appointment_id,))
        row = cursor.fetchone()
        if not row:
            return

        screening_tools = json.loads(row["screening_tools"] or '{}')
        statuses = json.loads(row["statuses"] or '{}')

        if screening_tools:
            any_incomplete = any(
                tool_data.get("status") not in ("Completed", "NA")
                for tool_data in screening_tools.values()
            )
            status_value = "Pending" if any_incomplete else "Completed"
            statuses["screen"] = {
                "status": status_value,
                "completion_date": datetime.today().strftime("%Y-%m-%d") if status_value == "Completed" else None
            }
        else:
            statuses["screen"] = {
                "status": "Pending",
                "completion_date": None}

        cursor.execute(
            "UPDATE appointments SET statuses = ? WHERE appointment_id = ?",
            (json.dumps(statuses), appointment_id)
        )
        db.commit()
    except Exception as e:
        st.error(f"Error updating screen status dynamically: {e}")
    finally:
        cursor.close()


def view_appointment_requests(client_name):
    set_full_page_background('images/black_strip.jpg')
    if not client_name:
        st.warning("⚠️ No client name provided.")
        return
    conn = create_connection()
    query = """
        SELECT 
            id,
            client_name,
            therapist_name,
            appointment_date,
            appointment_time,
            reason,
            created_at AS submitted_on,
            response,
            responder,
            response_date
        FROM appointment_requests
        WHERE client_name = ?
        ORDER BY appointment_date DESC, appointment_time DESC
    """
    df = pd.read_sql_query(query, conn, params=(client_name,))
    conn.close()

    if df.empty:
        st.info(f"📭 No appointments found for **{client_name}**.")
        return

    df.index = df.index + 1
    df["appointment_date"] = pd.to_datetime(df["appointment_date"], errors='coerce').dt.strftime('%Y-%m-%d')
    df["submitted_on"] = pd.to_datetime(df["submitted_on"], errors='coerce').dt.strftime('%Y-%m-%d').fillna('—')
    df["response_date"] = pd.to_datetime(df["response_date"], errors='coerce').dt.strftime('%Y-%m-%d').fillna('—')
    df["response"] = df["response"].fillna("—")
    df["responder"] = df["responder"].fillna("—")

    # CSS Styling
    st.markdown("""
        <style>
            .appt-table {
                border-collapse: collapse;
                width: 100%;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 15px;
                color: #eee;
            }
            .appt-table th, .appt-table td {
                border: 1px solid #444;
                padding: 10px 12px;
                text-align: left;
                vertical-align: top;
            }
            .appt-table th {
                background-color: #4A90E2;
                color: white;
                font-weight: 600;
            }
            .appt-table tbody tr:nth-child(even) {
                background-color: #1e1e1e;
            }
            .appt-table tbody tr:nth-child(odd) {
                background-color: #2c2c2c;
            }
            .therapist-cell { color: #8BC34A; font-weight: 600; }
            .reason-cell { color: #2196F3; font-style: italic; }
            .meta-cell { color: #bbbbbb; font-size: 13px; }
            .response-cell { color: #FFC107; }
            .responder-cell { color: #00BCD4; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)
    table_html = '<table class="appt-table">'
    table_html += """<thead>
            <tr>
                <th>#</th>
                <th>Booked Therapist</th>
                <th>Booked Date</th>
                <th>Booked Time</th>
                <th>Reason</th>
                <th>Date Submitted</th>
                <th>Response</th>
                <th>Responder</th>
                <th>Response Date</th>
            </tr>
        </thead>
        <tbody>
    """

    for idx, row in df.iterrows():
        table_html += f"""<tr>
                <td>{idx}</td>
                <td class="therapist-cell">{row['therapist_name']}</td>
                <td class="meta-cell">{row['appointment_date']}</td>
                <td class="meta-cell">{row['appointment_time']}</td>
                <td class="reason-cell">{row['reason']}</td>
                <td class="meta-cell">{row['submitted_on']}</td>
                <td class="response-cell">{row['response']}</td>
                <td class="responder-cell">{row['responder']}</td>
                <td class="meta-cell">{row['response_date']}</td>
            </tr>
        """

    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)



def main():
    db = create_connection()
    required_session_keys = ['user_name', "name", "selected_appointment", "appointment_id", "user_id"]
    for key in required_session_keys:
        if key not in st.session_state:
            st.session_state[key] = None
    create_functioning_responses_table(db)
    set_full_page_background('images/black_strip.jpg')
    username = st.session_state.get("user_name")
    client_name = st.session_state.get('name')
    








    device_width = st_javascript("window.innerWidth", key="device_width_")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 705
    num_cols_app = 3 if not is_mobile else 1
    appointment_card_height = "150px" if is_mobile else "200px"
    appointment_card_width = "100%"
    appointment_font_size_title = "18px" if is_mobile else "22px"
    appointment_font_size_text = "16px" if is_mobile else "18px"
    num_cols_tool = 4 if not is_mobile else 2
    tool_card_width = "100%"
    tool_card_height = "100px" if is_mobile else "150px"
    tool_font_size_title = "20px" if is_mobile else "25px"
    tool_font_size_text = "16px" if is_mobile else "18px"
    margin_right = "300px" if is_mobile else "0"
    font_css = f"""
    <style>
    /* Default tab appearance */
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {{
      font-size: 16px;
      font-weight: bold;
      color: white;
      padding: 4px 10px;
      margin: 0;
      border: 2px solid brown;
      border-radius: 3%;
      background-color: orange;
      box-sizing: border-box;
      transition: all 0.3s ease-in-out;
    }}

    /* Active tab: make it green */
    button[data-baseweb="tab"][aria-selected="true"] > div[data-testid="stMarkdownContainer"] > p {{
      background-color: green !important;
      border-color: darkgreen !important;
      color: white !important;
    }}

    /* Add spacing between tabs */
    div[role="tablist"] > button {{
      margin-right: {margin_right};
    }}

    /* Content area of each tab */
    section[role="tabpanel"] {{
      padding: 16px 24px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      font-size: 18px;
      color: #333333;
    }}

    /* Style tables */
    section[role="tabpanel"] table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 2px;
    }}

    section[role="tabpanel"] th, section[role="tabpanel"] td {{
      border: 1px solid #ddd;
      padding: 8px;
    }}

    section[role="tabpanel"] th {{
      background-color: #00897b;
      color: red;
      text-align: left;
    }}
    </style>
    """
    st.markdown(font_css, unsafe_allow_html=True)
    menu = st.tabs(['TASKS', 'RESPONSES'])

    with menu[1]:
        view_appointment_requests(client_name)



    with menu[0]:
        appointment_details = sorted(
            fetch_appointments_details_by_username(username),
            key=lambda x: (x["appointment_date"], x["appointment_time"]),
            reverse=True)
        col_back, _ = st.columns([1, 5])
        with col_back:
            if st.session_state.get("selected_tool"):
                if st.button("🔙 Back", key="back_to_tool_menu"):
                    st.session_state.selected_tool = None
                    st.rerun()
            elif st.session_state.get("selected_appointment"):
                if st.button("🔙 Back", key="back_to_appointments"):
                    st.session_state.selected_appointment = None
                    st.session_state.appointment_id = None
                    st.rerun()
        if st.session_state.get("selected_appointment") is None:
            if appointment_details:
                cols = st.columns(num_cols_app, gap="small")
                for index, appointment in enumerate(appointment_details):
                    with cols[index % num_cols_app]:
                        appointment_id = appointment["appointment_id"]
                        user_id = appointment["user_id"]
                        name = appointment["name"]
                        screen_type = appointment["screen_type"]

                        appointment_color = f"#{hash(str(appointment_id)) % 0xFFFFFF:06x}"
                        tool_statuses = list(appointment.get("tools_statuses", {}).values())
                        status_text = "Completed ✅" if all(status.strip() in ("Completed", "NA") for status in tool_statuses) else "Pending ⏳"

                        title = ordinal(len(appointment_details) - index)

                        hasClicked = card(
                            title=f'{title} - {screen_type}',
                            text=f"{appointment_id}\n{status_text}",
                            url=None,
                            styles={
                                "card": {
                                    "width": appointment_card_width,
                                    "height": appointment_card_height,
                                    "margin": "0px",
                                    "border-radius": "3px",
                                    "background": appointment_color,
                                    "color": "white",
                                    "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
                                    "border": "0.1px solid #600000",
                                    "text-align": "center",
                                },
                                "text": {"font-family": "serif", "font-size": appointment_font_size_text},
                                "title": {"font-family": "serif", "font-size": appointment_font_size_title}
                            },
                        )
                        if hasClicked:
                            st.session_state.selected_appointment = appointment
                            st.session_state.appointment_id = appointment_id
                            st.session_state.user_id = user_id
                            st.session_state.name = name
                            st.rerun()
            else:
                st.warning("No appointments found.")
            db.close()
            return
        if st.session_state.get("selected_tool") is None:
            selected_appointment = st.session_state.get("selected_appointment")
            user_id = selected_appointment["user_id"]
            appointment_id = selected_appointment["appointment_id"]
            name = selected_appointment["name"]
            st.session_state.user_id = user_id
            st.session_state.appointment_id = appointment_id
            st.session_state.name = name
            requested_tools = fetch_requested_tools(db, appointment_id)
            tools_list = list(requested_tools)
            if not tools_list:
                st.warning("No requested tools found.")
                db.close()
                return
            visible_tools = list(tools_list)
            if any(tool not in ("PHQ-4", "PHQ-9", "GAD-7") for tool in tools_list):
                visible_tools.append("Functioning")
            
            tool_colors = {tool: f"#{hex(hash(tool) % 0xFFFFFF)[2:].zfill(6)}" for tool in visible_tools}
            tool_images = {tool: f"images/{tool.lower()}.png" for tool in visible_tools}
            tool_cols = st.columns(num_cols_tool, gap="small")
            for index, tool in enumerate(visible_tools):
                if tool == "Functioning":
                    tool_status = check_functioning_completed(db, appointment_id)
                    tool_status = "Completed" if tool_status and tool_status[0] else "Pending"
                else:
                    tool_status = requested_tools.get(tool, "Pending")
                image_path = tool_images.get(tool, "brain.gif")
                try:
                    with open(image_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("utf-8")
                        image_data = f"data:image/png;base64,{encoded}"
                except FileNotFoundError:
                    image_data = None
                display_text = "Completed ✅" if tool_status == "Completed" else "Pending ⏳"
                with tool_cols[index % num_cols_tool]:
                    clicked = card(
                        title=tool,
                        text=display_text,
                        url=None,
                        styles={
                            "card": {
                                "width": tool_card_width,
                                "height": tool_card_height,
                                "margin": "0px",
                                "border-radius": "2px",
                                "background": tool_colors[tool],
                                "color": "white",
                                "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
                                "border": "0.1px solid #600000",
                                "text-align": "center",
                            },
                            "text": {"font-family": "serif", "font-size": tool_font_size_text},
                            "title": {"font-family": "serif", "font-size": tool_font_size_title}
                        },)
                    if clicked:
                        st.session_state.selected_tool = tool
                        st.rerun()
        else:
            selected_tool = st.session_state.selected_tool
            appointment_id = st.session_state.appointment_id
            user_id = st.session_state.get("user_id")
            requested_tools = get_requested_tools(db, appointment_id)
            tool_status = requested_tools.get(selected_tool, "Pending")
            if selected_tool == "Functioning":
                display_functioning_questionnaire(db, appointment_id, user_id)
            elif selected_tool in tool_modules:
                if tool_status == "Completed":
                    response_modules[selected_tool]()
                else:
                    tool_modules[selected_tool]()
                    with st.form(f"{selected_tool}_form"):
                        submit_btn = st.form_submit_button(f"✅ Submit to complete {selected_tool}")
                        if submit_btn:
                            if update_tool_status(db, appointment_id, selected_tool, "Completed"):
                                update_screen_action_status(db, appointment_id)
                                st.toast(f"{selected_tool} marked as Completed ✅", icon="✅")
                                st.session_state.selected_tool = None
                                st.rerun()
            else:
                st.warning(f"No module found for tool: {selected_tool}")
   
    
    


    db.close()
if __name__ == "__main__":
    main()
