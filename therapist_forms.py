DB_PATH = "users_db.db"
import streamlit as st
import json
import pandas as pd
import os
import importlib
from datetime import datetime
import phq9_qn
import gad7_qn, dass21_qn, dass21_responses, phq4_qn, phq4_responses
import bcrypt
import base64
from streamlit_card import card
import sqlite3

from streamlit_option_menu import option_menu
import session_notes
from streamlit_javascript import st_javascript
import phq9_responses, gad7_responses

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

class_list = ['','S1', 'S2', 'S3', 'S4', 'S5', 'S6']
stream_list = ['',"EAST", "SOUTH", 'WEST', 'NORTH']
gender_list = ['','MALE','FEMALE']

tool_modules = {
    'PHQ-9': phq9_qn.main,
    'GAD-7':gad7_qn.main,
    'DASS-21': dass21_qn.main,
    'PHQ-4': phq4_qn.main,
}

def fetch_requested_tools(db, appointment_id):
    try:
        cursor = db.cursor()
        fetch_query = """
        SELECT tool_name, tool_status FROM screen
        WHERE appointment_id = ?
        """
        cursor.execute(fetch_query, (appointment_id,))
        result = cursor.fetchall()
        tools_status = {row[0]: row[1] for row in result}
    except Exception as e:
        print(f"Database error: {e}")
        return {}
    finally:
        cursor.close()
    return tools_status

def update_tool_status(db, appointment_id, tool_name, new_status):
    cursor = db.cursor()
    update_query = """
    UPDATE screen
    SET tool_status = ?
    WHERE appointment_id = ? AND tool_name = ?
    """
    cursor.execute(update_query, (new_status, appointment_id, tool_name))
    db.commit()
    cursor.close()

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

def insert_functioning_response(db, appointment_id, user_id, difficulty_level):
    cursor = db.cursor()

    difficulty_to_score = {
        "Extremely difficult": 1,
        "Very difficult": 2,
        "Somewhat difficult": 3,
        "Not difficult at all": 4}

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

def display_functioning_questionnaire(db, appointment_id, user_id):
    completed_response = check_functioning_completed(db, appointment_id)
    if completed_response:
        st.success(f"Functioning completed ✅")
    else:
        st.info("If you checked off any problems, how difficult have these problems made it for you?")
        difficulty_level = st.radio(
            "Choose difficulty level:",
            ('Not difficult at all', 'Somewhat difficult', 'Very difficult', 'Extremely difficult'))

        if st.button("Submit Functioning Response"):
            success = insert_functioning_response(db, appointment_id, user_id, difficulty_level)
            if success:
                st.success("Functioning response recorded successfully ✅!")
                st.rerun() 


def fetch_appointment_details_by_name(client_name):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                SELECT action_id, appointment_id, client_name, appointment_type, screen_type, term,
                       created_at, class, stream, client_type, action_type,
                       assigned_to, tools, tools_statuses
                FROM screen
                WHERE client_name = ? AND action_type = 'screen'
                ORDER BY created_at DESC
            """
            cursor.execute(query, (client_name,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            records = []
            for row in rows:
                record = dict(zip(columns, row))

                # Extract appointment date and time from created_at
                created = record.get("created_at")
                if created:
                    try:
                        dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                        record["appointment_date"] = dt.strftime("%Y-%m-%d")
                        record["appointment_time"] = dt.strftime("%I:%M %p")
                    except:
                        record["appointment_date"] = "-"
                        record["appointment_time"] = "-"
                else:
                    record["appointment_date"] = "-"
                    record["appointment_time"] = "-"

                # Parse tools JSON
                try:
                    record["tools"] = json.loads(record["tools"]) if record["tools"] else []
                except Exception as e:
                    st.warning(f"Failed to parse tools for action_id {record['action_id']}: {e}")
                    record["tools"] = []

                # Parse tools_statuses JSON
                try:
                    record["tools_statuses"] = json.loads(record["tools_statuses"]) if record["tools_statuses"] else {}
                except Exception as e:
                    st.warning(f"Failed to parse tools_statuses for action_id {record['action_id']}: {e}")
                    record["tools_statuses"] = {}

                records.append(record)

            return records

        except Exception as e:
            st.error(f"Error fetching screening data: {e}")
        finally:
            cursor.close()
            connection.close()

    return []

def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


response_modules = {
    'PHQ-9': phq9_responses.main,
    'GAD-7':gad7_responses.main,
    'Functioning': 'Noted',
    'DASS-21':dass21_responses.main,
    'PHQ-4': phq4_responses.main,}

def fetch_students(db, search_input):
    cursor = db.cursor()

    if search_input.strip().upper().startswith("STUD-") or search_input.isdigit():
        query = """
        SELECT user_id, full_name, age, gender, class, stream, contact, email, registration_date
        FROM users
        WHERE user_id = ?
        """
        cursor.execute(query, (search_input.strip(),))
    else: 
        name_parts = search_input.strip().split()
        query_conditions = []
        params = []

        if len(name_parts) == 2:
            first_name, last_name = name_parts
            query_conditions.append("full_name LIKE ?")
            query_conditions.append("full_name LIKE ?")
            params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
        else:
            query_conditions.append("full_name LIKE ?")
            params.append(f"%{search_input}%")

        query = f"""
        SELECT user_id, full_name, age, gender, class, stream, contact, email, registration_date
        FROM users
        WHERE {" OR ".join(query_conditions)}
        """
        cursor.execute(query, tuple(params))

    rows = cursor.fetchall()
    return [dict(row) for row in rows]






##### TERAPIST #INFORMATION ##########
def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None

def fetch_therapist_consult_clients(therapist_name):
    conn = create_connection()
    query = """
        SELECT appointment_id, name, class, stream, term, client_type, assigned_date, assigned_therapist, actions, time_remaining, waiting_time
        FROM appointments
        WHERE assigned_therapist = ?"""
    df = pd.read_sql(query, conn, params=(therapist_name,))
    conn.close()
    def is_consult_action(actions_json):
        try:
            actions = json.loads(actions_json) if isinstance(actions_json, str) else {}
            return actions.get("consult", False) is True
        except:
            return False
    df = df[df['actions'].apply(is_consult_action)]
    df = df.drop(['actions', 'class', 'stream','term', 'assigned_therapist'], axis=1)
    df.index = df.index + 1
    return df

##### DRIVER CODE #########
def main():
    db = create_connection()
    set_full_page_background('images/black_strip.jpg')
    username = st.session_state.get("user_name")
    therapist_name = get_full_name_from_username(username)

    if not therapist_name:
        st.error("Therapist full name not found.")
        return
    df = fetch_therapist_consult_clients(therapist_name)
    if df.empty:
        st.warning("No consults assigned to you.")
    else:
        st.dataframe(df)
    device_width = st_javascript("window.innerWidth", key="device_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = 3 if not is_mobile else 1
    appointment_card_height = "150px" if is_mobile else "200px"
    appointment_card_width = "100%" if is_mobile else "100%"
    appointment_font_size_title = "18px" if is_mobile else "22px"
    appointment_font_size_text = "16px" if is_mobile else "18px"
    num_cols_tool = 3 if not is_mobile else 1
    tool_card_width = "100%"
    tool_card_height = "100px" if is_mobile else "150px"
    tool_font_size_title = "20px" if is_mobile else "30px"
    tool_font_size_text = "16px" if is_mobile else "20px"
    for key, default in {
        "selected_record": None,
        "selected_appointment": None,
        "selected_tool": None,
        "selected_page": "screening_menu",
        "last_search_input": ""
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    if is_mobile:
        with st.expander("🔍SEARCH", expanded=False):
            search_input = st.text_input("Enter Name or STD ID", "")
    else:
        with st.sidebar.expander("🔍SEARCH", expanded=True):
            search_input = st.text_input("Enter Name or STD ID", "")

    if search_input != st.session_state.last_search_input:
        st.session_state.selected_record = None
        st.session_state.selected_appointment = None
        st.session_state.selected_tool = None
        st.session_state.last_search_input = search_input
    results = []

    if st.session_state.selected_record is None and search_input.strip():
        results = fetch_students(db, search_input)
       
        if results:
            if is_mobile:
                with st.expander('Results', expanded=True):
                    st.write(f"**{len(results)} result(s) found**")
                    options = {f"{r['full_name']} - {r['user_id']}": r for r in results}
                    selected_option = st.selectbox("Select a record:", list(options.keys()))
                    st.session_state.selected_record = options[selected_option]
            else:
                with st.sidebar.expander('Results', expanded=True):
                    st.write(f"**{len(results)} result(s) found**")
                    options = {f"{r['full_name']} - {r['user_id']}": r for r in results}
                    selected_option = st.selectbox("Select a record:", list(options.keys()))
                    st.session_state.selected_record = options[selected_option]
        
        else:
            st.error(f'No record for {search_input} ')

    if st.session_state.selected_record:
        selected_record = st.session_state.selected_record
        def format_line(label, value):
            return f"<div style='margin-bottom:6px;'><span style='color:#c0392b; font-weight:bold;'>{label}:</span> <span style='color:#27ae60;'>{value}</span></div>"
        profile_html = ""
        profile_fields = [
            ("Student ID", selected_record['user_id']),
            ("Name", selected_record['full_name']),
            ("Age", f'{selected_record['age']} Years'),
            ("Gender", selected_record['gender']),
            ("Class", selected_record['class']),
            ("Stream", selected_record['stream']),
            ]
        for label, value in profile_fields:
            profile_html += format_line(label, value)
        if is_mobile:
            with st.expander("STUDENT PROFILE", expanded=True):
                st.markdown(profile_html, unsafe_allow_html=True)
        else:
            with st.sidebar.expander("STUDENT PROFILE", expanded=True):
                st.markdown(profile_html, unsafe_allow_html=True)
        appointment_details = sorted(
            fetch_appointment_details_by_name(selected_record['full_name']),
            key=lambda x: (x["appointment_date"], x["appointment_time"]),
            reverse=True)
        if st.session_state.selected_appointment is None:
            if appointment_details:
                cols = st.columns(num_cols_app, gap ='small')
                for index, appointment in enumerate(appointment_details):
                    with cols[index % num_cols_app]:
                        appointment_id = appointment["appointment_id"]
                        screen_type = appointment["screen_type"]
                        # tool_statuses = appointment["tool_status"].split(", ") if appointment["tool_status"] else []
                        tool_statuses = list(appointment.get("tools_statuses", {}).values())


                        appointment_color = f"#{hash(str(appointment_id)) % 0xFFFFFF:06x}"
                        status_text = "Completed ✅" if all(status.strip() == "Completed" for status in tool_statuses) else "Pending ⏳"
                        title = ordinal(len(appointment_details) - index)
                        st_stream = appointment['stream']
                        st_class = appointment['class']
                        term = appointment['term']
                        
                        hasClicked = card(
                            title=f'{title} - {screen_type}',
                            text=f"{appointment_id}\n{st_class}\n{st_stream}\n{term}\n{status_text}",
                            url=None,
                            styles={
                                "card": {
                                    "width": appointment_card_width,
                                    "height": appointment_card_height,
                                    "border-radius": "2px",
                                    "background": appointment_color,
                                    "color": "white",
                                    "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
                                    "border": "1px solid #600000",
                                    "text-align": "center",
                                    "margin": "0px"
                                },
                                "text": {"font-family": "serif", "font-size": appointment_font_size_text},
                                "title": {"font-family": "serif", "font-size": appointment_font_size_title}
                            },
                        )
                        if hasClicked:
                            st.session_state.selected_appointment = appointment
                            st.session_state.appointment_id = appointment_id
                            st.session_state.client_name = appointment["client_name"]
                            st.session_state.action_id = appointment["action_id"]  # ✅ this is the field causing the earlier error if missing
                            st.rerun()

        elif st.session_state.selected_tool is None:
            appointment_id = st.session_state.appointment_id
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
                key="task_reslt")

            if task_reslt == 'Screen':
                appointment_id = st.session_state.get("appointment_id")
                if appointment_id:
                    screen_men = st.tab(['Add Tool', 'Fill Tool'])
                    with screen_men[0]: 
                    
                        import tool_responses
                        tool_responses.main()
                    with screen_men[1]:
                        import therapist_screen
                        therapist_screen.main()
                

            elif task_reslt == 'Results':
                appointment_id = st.session_state.get("appointment_id")
                if appointment_id:
                    import screen_results
                    screen_results.main()   
                            
            elif task_reslt == 'Notes': 
                session_notes.main()

            if st.button("🔙 back"):
                st.session_state.selected_appointment = None
                st.rerun()

        else:
            selected_tool = st.session_state.selected_tool
            if st.button("🔙 back", key="return_btn"):
                st.session_state.selected_tool = None
                st.rerun()

            appointment_id = st.session_state.appointment_id
            user_id = st.session_state.selected_record['user_id']
            if selected_tool == "Functioning":
                display_functioning_questionnaire(db, appointment_id, user_id)
            else:
                tool_status = fetch_requested_tools(db, appointment_id).get(selected_tool, "Pending")
                if selected_tool not in tool_modules:
                    st.warning(f"No module found for the tool: {selected_tool}. Please contact support.")
                else:
                    module_function = tool_modules[selected_tool]
                    response_function = response_modules[selected_tool]
                    if tool_status == 'Pending':
                        st.info(f"Please fill out the {selected_tool} form:")
                        module_function()
                        if st.button(f"Submit to complete {selected_tool}"):
                            update_tool_status(db, appointment_id, selected_tool, 'Completed')
                            st.success(f"{selected_tool} response captured ✅!")
                    else:
                        st.success(f"{selected_tool} completed ✅")
                        response_function()
    db.close()

if __name__ == '__main__':
    main()