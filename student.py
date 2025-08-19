DB_PATH = "users_db.db"
import streamlit as st
from streamlit_card import card
import sqlite3

import LogIn, SignUp
import student_forms_page
import base64
import os
from streamlit_javascript import st_javascript
import impact, entire_file, results_filled_mlt,consult_mobile
import appointments
import appoint_screen_refined, appoint_consult, lab, lab_req

def set_background(image_path, width="500px", height="500px", border_color="red", border_width="5px"):
    try:
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found.")
            return
        
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        st.markdown(f"""
        <style>
        .image-container {{
            width: {width};
            height: {height};
            background-image: url('data:image/jpeg;base64,{encoded_string}');
            background-size: cover;
            background-position: right;
            border: {border_width} {border_color};
            margin: 0 auto;
            border-radius : 10%;
            position: fixed;
            top: 1;
        }}
        </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="image-container"></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading background image: {e}")


def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

if "username" not in st.session_state:
    st.session_state["username"] = None

if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = None 


def set_custom_background(bg_color="skyblue", sidebar_img=None):
    page_bg_img = f"""
        <style>
        [data-testid="stAppViewContainer"] > .main {{
            background-color: {bg_color};
            background-size: 140%;
            background-position: top left;
            background-repeat: repeat;
            background-attachment: local;
            padding-top: 0px;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            {"background-image: url('data:image/png;base64," + sidebar_img + "');" if sidebar_img else ""}
            background-position: center; 
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0);
            padding-top: 0px;
        }}
        [data-testid="stToolbar"] {{
            right: 2rem;
        }}
        </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)



def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
          # enables dict-like access
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

def fetch_student_record(username):
    try:
        db = create_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM student_users WHERE username = ?", (username,))
        record = cursor.fetchone()
        db.close()
        return dict(record) if record else None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None

def fetch_student_details_by_username(username):
    connection = create_connection() 
    student_details = {}
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM student_users WHERE username = ?", (username,))
            record = cursor.fetchone()
            if record:
                student_details = dict(record)
        except sqlite3.Error as e:
            st.error(f"Error fetching student details: {e}")
        finally:
            cursor.close()
            connection.close()
    return student_details


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def fetch_appointment_details_by_username(username):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                SELECT a.appointment_id, a.name, a.appointment_type, a.screen_type, a.term, 
                       a.appointment_date, a.appointment_time, a.clinician_name, a.reason, 
                       s.student_class, s.stream,
                       GROUP_CONCAT(DISTINCT r.tool_status) AS tool_status
                FROM screen_appointments a
                JOIN student_users s ON a.student_id = s.student_id
                LEFT JOIN requested_tools_students r ON a.appointment_id = r.appointment_id
                WHERE s.username = ?
                GROUP BY a.appointment_id
            """
            cursor.execute(query, (username,))
            records = cursor.fetchall()
            return [dict(row) for row in records]
        except sqlite3.Error as e:
            st.error(f"Error fetching appointment details: {e}")
        finally:
            cursor.close()
            connection.close()
    return []

def fetch_students(db, search_input):
    cursor = db.cursor()
    if search_input.strip().upper().startswith("STUD-") or search_input.isdigit():
        query = """
        SELECT student_id, name, age, gender, student_class, stream, date
        FROM student_users
        WHERE student_id = ?
        """
        cursor.execute(query, (search_input.strip(),))
    else: 
        name_parts = search_input.strip().split()
        query_conditions = []
        params = []

        if len(name_parts) == 2:
            first_name, last_name = name_parts
            query_conditions.append("name LIKE ?")
            query_conditions.append("name LIKE ?")
            params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
        else:
            query_conditions.append("name LIKE ?")
            params.append(f"%{search_input}%")
        query = f"""
        SELECT student_id, name, age, gender, student_class, stream
        FROM student_users
        WHERE {" OR ".join(query_conditions)}
        """
        cursor.execute(query, tuple(params))
    return [dict(row) for row in cursor.fetchall()]


def create_user_sessions_table():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    login_time DATETIME,
                    logout_time DATETIME,
                    duration INTEGER,
                    status TEXT CHECK(status IN ('active', 'inactive')) DEFAULT 'inactive',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)
            connection.commit()
            print("user_sessions table created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating user_sessions table: {e}")
        finally:
            cursor.close()
            connection.close()


def render_task_menu(page_title, task_menu):
    device_width = st_javascript("window.innerWidth", key="device_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = 3 if not is_mobile else 1
    card_height = "150px" if is_mobile else "200px"
    card_width = "100%" 
    font_size_title = "50px" if is_mobile else "70px"
    font_size_text = "25px"
    card_colors = [
        "linear-gradient(135deg, #1abc9c, #16a085)",
        "linear-gradient(135deg, #3498db, #2980b9)",
        "linear-gradient(135deg, #9b59b6, #8e44ad)",
        "linear-gradient(135deg, #e67e22, #d35400)",
        "linear-gradient(135deg, #e74c3c, #c0392b)",
        "linear-gradient(135deg, #f39c12, #f1c40f)",
        "linear-gradient(135deg, #2ecc71, #27ae60)",
        "linear-gradient(135deg, #34495e, #2c3e50)",
    ]
    
    cols = st.columns(num_cols_app, gap='small')
    for index, task in enumerate(task_menu):
        color = card_colors[index % len(card_colors)]  
        with cols[index % num_cols_app]:
            if card(
                title=task["title"],
                text=task["text"],
                key=f"task-{task['text']}",
                styles={
                    "card": {
                        "width": card_width,
                        "height": card_height,
                        "border-radius": "2px",
                        "background": color,
                        "color": "white",
                        "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.25)",
                        "border": "2px solid #600000",
                        "text-align": "center",
                        "margin": "0px"
                    },
                    "text": {"font-family": "serif", "font-size": font_size_text},
                    "title": {"font-family": "serif", "font-size": font_size_title},
                },
            ):
                st.session_state.selected_task = task["text"]
                st.rerun()


def show_page_menu():
    device_width = st_javascript("window.innerWidth", key="device_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = 3 if not is_mobile else 1
    card_height = "150px" if is_mobile else "200px"
    card_width = "100%"
    font_size_title = "50px" if is_mobile else "70px"
    font_size_text = "25px"
    card_colors = [
        "linear-gradient(135deg, #1abc9c, #16a085)",
        "linear-gradient(135deg, #3498db, #2980b9)",
        "linear-gradient(135deg, #9b59b6, #8e44ad)",
        "linear-gradient(135deg, #e67e22, #d35400)",
        "linear-gradient(135deg, #e74c3c, #c0392b)",
        "linear-gradient(135deg, #f39c12, #f1c40f)",
        "linear-gradient(135deg, #2ecc71, #27ae60)",
        "linear-gradient(135deg, #34495e, #2c3e50)",
    ]
    
    pages = [
        {"title": '🎋',"text": "Schedules"},
        {"title": '📝',"text": "Tasks"},
        {"title": "📊","text": "Reports"},
        {"title": "📚","text": "Files"},
        {"title": "📈","text": "Analysis"},
        {"title": "🗓️","text": "Activities"},
        {"title": "🙋‍♀️","text": "Support"},
        {"title": "💬", "text": "Blogs"},
        {"title": "📦","text": "Archives"}
    ]

    cols = st.columns(num_cols_app, gap='small')
    for index, page in enumerate(pages):
        color = card_colors[index % len(card_colors)] 
        with cols[index % num_cols_app]:
            if card(
                title=page["title"],
                text=page["text"],
                key=f"page-{page['text']}",
                styles={
                    "card": {
                        "width": card_width,
                        "height": card_height,
                        "border-radius": "2px",
                        "background": color,
                        "color": "white",
                        "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.25)",
                        "border": "0.1px solid #600000",
                        "text-align": "center",
                        "margin": "0px",
                    },
                    "text": {"font-family": "serif", "font-size": font_size_text},
                    "title": {"font-family": "serif", "font-size": font_size_title},
                },
            ):
                st.session_state.selected_page = page["title"]
                st.rerun()

def show_task_menu(page_title):
    task_menu = [
        {"title": '📝', "text": "Screening"},
        {"title": "🧑‍⚕️", "text": "Special consult"},
        {"title": "🛗", "text": "Group sessions"},
        ]
    render_task_menu(page_title, task_menu)


def show_schedule_menu(page_title):
    schedule_menu = [
        {"title": '💢', "text": "Assign Tools"},
        {"title": "🧑‍⚕️", "text": "Special consult"},  
        {"title": "🛗", "text": "Group sessions"}, ] 
    render_schedule_menu(page_title, schedule_menu)

def render_schedule_menu(page_title, schedule_menu):
    device_width = st_javascript("window.innerWidth", key="device_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = 3 if not is_mobile else 1
    card_height = "150px" if is_mobile else "220px"
    card_width = "100%" if is_mobile else "100%"
    font_size_title = "50px" if is_mobile else "70px"
    font_size_text = "25px"
    card_colors = [
        "linear-gradient(135deg, #1abc9c, #16a085)",
        "linear-gradient(135deg, #3498db, #2980b9)",
        "linear-gradient(135deg, #9b59b6, #8e44ad)",
        "linear-gradient(135deg, #e67e22, #d35400)",
        "linear-gradient(135deg, #e74c3c, #c0392b)",
        "linear-gradient(135deg, #f39c12, #f1c40f)",
        "linear-gradient(135deg, #2ecc71, #27ae60)",
        "linear-gradient(135deg, #34495e, #2c3e50)",]
    schedule_menu = [
        {"title": '💢', "text": "Assign Tools"},
        {"title": "🧑‍⚕️", "text": "Special consult"},  
        {"title": "🛗", "text": "Group sessions"}, ] 
    
    cols = st.columns(num_cols_app, gap='small')
    for index, schedule in enumerate(schedule_menu):
        color = card_colors[index % len(card_colors)] 
        with cols[index % num_cols_app]:
            if card(
                title=schedule["title"],
                text=schedule["text"],
                key=f"report-{schedule['text']}",
                styles={
                    "card": {
                        "width": card_width,
                        "height": card_height,
                        "border-radius": "2px",
                        "background": color,
                        "color": "white",
                        "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.25)",
                        "border": "1px solid transparent",
                        "text-align": "center",
                        "margin": "0px",
                    },
                    "text": {"font-family": "serif", "font-size": font_size_text},
                    "title": {"font-family": "serif", "font-size": font_size_title},
                },
            ):
                st.session_state.selected_schedule = schedule["text"]
                st.rerun()


def show_schedule_menu(page_title):
    schedule_menu = [
        {"title": '📝', "text": "Screening"},
        {"title": "🩺", "text": "Special consult"},
        {"title": "🛗", "text": "Group sessions"},
       
    ]
    render_schedule_menu(page_title, schedule_menu)


def app_router(page, task=None, report=None, schedule=None):
    if task:
        if task == "Screening":
            student_forms_page.main()
        elif task == "Special consult":
            consult_mobile.main()
        elif task == "Follow-Up":
            st.info("📌 Follow-Up Page - Coming soon!")
        elif task == "Group sessions":
            st.info("👥 Group Sessions - Coming soon!")
        return

    if schedule:
        if schedule == "Assign Tools":
            appoint_screen_refined.main()
        elif schedule == "Special consult":
            appoint_consult.main()
        
        elif schedule == "Group sessions":
            st.info('Coming soon')
        return


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






def main():
    db = create_connection()
    create_user_sessions_table()
    set_full_page_background('std2.jpg')
    for key in ['student_name', 'student_id', 'appointment_id', 'selected_appointment', 'selected_page', 'selected_task', 'selected_report','selected_schedule']:
        if key not in st.session_state:
            st.session_state[key] = None

    if not st.session_state.get("username"):
        login_page()
        return
    fetch_student_record(st.session_state["username"])
    if not st.session_state.selected_page:
        show_page_menu()
        return

    if st.session_state.selected_page == "📚":
        if st.button("🔙 Page Menu"):
            st.session_state.selected_page = None
            st.rerun()
        entire_file.main()
        return

    

    elif st.session_state.selected_page == "🗓️":
        if st.button("🔙 Page Menu"):
            st.session_state.selected_page = None
            st.rerun()
        # lab.main()
        lab_req.main()
        return



    if st.session_state.selected_page == "📊":
        if st.button("🔙 Page Menu"):
            st.session_state.selected_page = None
            st.rerun()
        impact.main()
        return


    if st.session_state.selected_page == "📈":
        if st.button("🔙 Page Menu"):
            st.session_state.selected_page = None
            st.rerun()
        results_filled_mlt.main()
        return

    
    if st.session_state.selected_page == "🎋":
        if st.session_state.selected_schedule:
            if st.button("🔙 Schedule Menu"):
                st.session_state.selected_schedule = None
                st.rerun()
            app_router(st.session_state.selected_page, schedule=st.session_state.selected_schedule)
        else:
            if st.button("🔙 Page Menu"):
                st.session_state.selected_page = None
                st.rerun()
            show_schedule_menu(st.session_state.selected_page)
        return

    if st.session_state.selected_page == "📝":
        if st.session_state.selected_task:
            if st.button("🔙 Task Menu"):
                st.session_state.selected_task = None
                st.rerun()
            app_router(st.session_state.selected_page, task=st.session_state.selected_task)
        else:
            if st.button("🔙 Page Menu"):
                st.session_state.selected_page = None
                st.rerun()
            show_task_menu(st.session_state.selected_page)
        return
    st.warning("⚠️ Under development.")
    if st.button("🔙 Page Menu"):
        st.session_state.selected_page = None
        st.rerun()
if __name__ == "__main__":
    main()


