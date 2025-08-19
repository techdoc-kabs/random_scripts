import streamlit as st
from streamlit_card import card
import student_tool_page
import streamlit as st
import base64
import os
import datetime
from datetime import datetime
import sqlite3

import cont
from streamlit_javascript import st_javascript
import contact_form
import time
import pandas as pd

DB_PATH = "users_db.db"
# device_width = st_javascript("window.innerWidth", key="menu_device_width")
def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

def fetch_student_record(username):
    try:
        db = create_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        db.close()
        if row:
            return dict(row)
        return None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None


def fetch_student_details_by_username(username):
    connection = create_connection()
    student_details = {}
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            record = cursor.fetchone()
            student_details = dict(record) if record else {}
        except Exception as e:
            st.error(f"Error fetching student details: {e}")
        finally:
            cursor.close()
            connection.close()
    return student_details


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

def student_menu():
    from streamlit_javascript import st_javascript
    device_width = st_javascript("window.innerWidth", key="scren_widith")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    cols_per_row = 4 if not is_mobile else 1
    card_height = "180px" if is_mobile else "220px"
    card_width = "100%" if is_mobile else "100%"
    font_size_title = "50px" if is_mobile else "90px"
    font_size_text = "20px" if is_mobile else "30px"
    with st.expander(f'#### :red[STUDENTS]', expanded= True):
        pages = [
    
    {"title": "📚",  "text":"Resources", "key": "content"},
    {"title": '📝',  "text":"Tasks", "key": "tasks"},
    {"title": "🙋‍♀️",  "text":"Find help", "key": "selfhelp"},
    {"title": "🎋",  "text":"Feedback", "key": "feedback"}
]

    rows = [pages[i:i + cols_per_row] for i in range(0, len(pages), cols_per_row)]
    card_colors = [
        "linear-gradient(135deg, #1abc9c, #16a085)",
        "linear-gradient(135deg, #3498db, #2980b9)",
        "linear-gradient(135deg, #9b59b6, #8e44ad)",
        "linear-gradient(135deg, #e67e22, #d35400)",
        "linear-gradient(135deg, #e74c3c, #c0392b)",
    ]
    rows = [pages[i:i + cols_per_row] for i in range(0, len(pages), cols_per_row)]
    for row_idx, row in enumerate(rows):
        cols = st.columns(cols_per_row, gap="small")
        for col_idx, (col, item) in enumerate(zip(cols, row)):
            color = card_colors[(row_idx * cols_per_row + col_idx) % len(card_colors)]
            with col:
                clicked = card(
                    title=item["title"],
                    text=item["text"],
                    key=item["key"],
                    styles={
                        "card": {
                            "width": card_width,
                            "height": card_height,
                            "border-radius": "10px",
                            "background": color,
                            "color": "white",
                            "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.25)",
                            "border": "0.1px solid #600000",
                            "text-align": "center",
                            "padding": "10px",
                            "margin": "0",
                        },
                        "title": {
                            "font-family": "serif",
                            "font-size": font_size_title,
                        },
                        "text": {
                            "font-family": "serif",
                            "font-size": font_size_text,
                        },
                    }
                )

                if clicked:
                    st.session_state.student_action = item["text"].lower()
                    st.rerun()
CARD_COLORS = [
    "linear-gradient(135deg, #1abc9c, #16a085)",
    "linear-gradient(135deg, #3498db, #2980b9)",
    "linear-gradient(135deg, #9b59b6, #8e44ad)",
    "linear-gradient(135deg, #e67e22, #d35400)",
    "linear-gradient(135deg, #e74c3c, #c0392b)",]

def display_card_menu(page_title, options, selected_key, num_cols=3):
    if f"{selected_key}_just_clicked" not in st.session_state:
        st.session_state[f"{selected_key}_just_clicked"] = False
    device_width = st_javascript("window.innerWidth", key=f"device_width_{selected_key}")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = num_cols if not is_mobile else 1
    card_height = "150px" if is_mobile else "200px"
    card_width = "100%"
    font_size_title = "50px" if is_mobile else "70px"
    font_size_text = "25px"
    cols = st.columns(num_cols_app, gap='small')
    for index, option in enumerate(options):
        color = CARD_COLORS[index % len(CARD_COLORS)]
        with cols[index % num_cols_app]:
            if card(
                title=option["title"],
                text=option["text"],
                key=f"{selected_key}-{option['text']}",
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
                        "margin": "0px",
                    },
                    "text": {"font-family": "serif", "font-size": font_size_text},
                    "title": {"font-family": "serif", "font-size": font_size_title},},):
                if not st.session_state[f"{selected_key}_just_clicked"]:
                    st.session_state[selected_key] = option["text"]
                    st.session_state[f"{selected_key}_just_clicked"] = True
                    st.rerun() 
    st.session_state[f"{selected_key}_just_clicked"] = False



def student_tasks_page():
    if st.button("🔙 Menu"):
        st.session_state.student_action = None
        st.rerun()
    student_tool_page.main()
    
def student_chats_page():
    if st.button("🔙 Menu"):
        st.session_state.student_action = None
        st.rerun()
    contact_form.main()
   

def student_feedbback_page():
    if st.button("🔙 Menu"):
        st.session_state.student_action = None
        st.rerun()
    username = st.session_state.get('user_name')
    feed_back_button()
    view_feedback(username)
    
    
    
def show_resources_menu(page_title):
    if st.button("🔙 Home"):
        st.session_state.student_action = None
        st.rerun()
    resource_options = [
        {"title": '🧠', "text": "Challenges", "module": "cont"},
        {"title": "🛠️", "text": "Self-Help", "module": "help_tech"},
        {"title": "🎥", "text": "Videos", "module": "video_archives"},
        {"title": "🎧", "text": "Podcasts", "module": "podcasts"},
        # {"title": "📄", "text": "Articles", "module": "articles"},

        ]
    selected_key = "selected_resource"  
    selected_value = st.session_state.get(selected_key)
    if selected_value:
        selected_item = next((item for item in resource_options if item["text"] == selected_value), None)
        if selected_item:
            if st.button("🔙 Resources"):
                st.session_state[selected_key] = None
                st.rerun()
            set_full_page_background('images/black_strip.jpg')
            try:
                module = __import__(selected_item["module"])
                module.main()
            except Exception as e:
                st.info("🚧 This page is under development and its coming soon.")
            return
    display_card_menu(page_title, resource_options, selected_key=selected_key, num_cols=4)

def save_feedback(message, name="Anonymous"):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedbacks (name, message) VALUES (?, ?)", (name, message))
    conn.commit()
    conn.close()


def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None


@st.dialog("💬 Give us Feedback", width='small')
def feedback_dialog():
    username = st.session_state.get('user_name')
    name = get_full_name_from_username(username)
    st.markdown(f' ##  :green[Dear] {" "} :orange[{name}] !!')
    st.markdown("""
        <h4 style='color:skyblue;font-size:25px;'>We're here to listen.</h4>
        <p style='font-size:20px;'>Your thoughts help build a better mental health experience for everyone.</p>
    """, unsafe_allow_html=True)
    feedback = st.text_area("", height=200, placeholder="I feel...")
    if st.button("✅ Submit"):
        if feedback.strip():
            save_feedback(message=feedback.strip(), name=username)
            st.success("✅ Thank you for your feedback 💚")
            time.sleep(1.5)
            st.rerun()
        else:
            st.warning("⚠️ Please enter your thoughts before submitting.")




def feed_back_button():
    if "show_feedback_form" not in st.session_state:
        st.session_state.show_appointment_form = False
    st.markdown("""
            <style>
            div.stButton > button {
                background-color: #00897b;
                color: white !important;
                padding: 12px 28px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
            }
            div.stButton > button:hover {
                background-color: #e53935;
                color: white !important;
            }
            </style>
        """, unsafe_allow_html=True)
    if st.button("🗓️ Give us your feedback"):
        feedback_dialog()
           


def view_feedback(username=None):
    set_full_page_background('images/black_strip.jpg')
    conn = create_connection()
    if username:
        query = """
            SELECT message, sent_at, response, responded_at, responder 
            FROM feedbacks 
            WHERE name = ? 
            ORDER BY sent_at DESC"""
        df = pd.read_sql_query(query, conn, params=(username,))
    else:
        query = """
            SELECT message, sent_at, response, responded_at, responder 
            FROM feedbacks 
            ORDER BY sent_at DESC
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    if df.empty:
        st.info("No feedback found for this user.")
        return
    df.index = df.index + 1
    df["sent_at"] = pd.to_datetime(df["sent_at"]).dt.strftime('%Y-%m-%d %H:%M')
    df["responded_at"] = pd.to_datetime(df["responded_at"], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
    df["responded_at"] = df["responded_at"].fillna('—')
    df["response"] = df["response"].fillna('—')
    df["responder"] = df["responder"].fillna('—')

    st.markdown("""
        <style>
            /* Table style */
            .feedback-table {
                border-collapse: collapse;
                width: 100%;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 15px;
                color: #eee;
            }
            .feedback-table th, .feedback-table td {
                border: 1px solid #444;
                padding: 12px 15px;
                text-align: left;
            }
            .feedback-table th {
                background-color: #4A90E2;
                color: white;
                font-weight: 600;
            }
            .feedback-table tbody tr:nth-child(even) {
                background-color: #1e1e1e;
            }
            .feedback-table tbody tr:nth-child(odd) {
                background-color: #2c2c2c;
            }

            /* Special colors */
            .message-cell {
                color: #8BC34A; /* Light Green */
                font-weight: 600;
            }
            .response-cell {
                color: #2196F3; /* Bright Blue */
                font-style: italic;
            }
            .meta-cell {
                color: #bbbbbb;
                font-size: 13px;
            }
        </style>
    """, unsafe_allow_html=True)
    table_html = '<table class="feedback-table">'
    table_html += "<thead><tr><th>#</th><th>My Message</th><th>Sent_on</th><th>Reply</th><th>Reply date</th><th>Replied_by</th></tr></thead><tbody>"
    for idx, row in df.iterrows():
        table_html += f"""<tr><td>{idx}</td>
                <td class="message-cell">{row['message']}</td>
                <td class="meta-cell">{row['sent_at']}</td>
                <td class="response-cell">{row['response']}</td>
                <td class="meta-cell">{row['responded_at']}</td>
                <td class="meta-cell">{row['responder']}</td>
            </tr>
        """
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)




class_list = ['','S1', 'S2', 'S3', 'S4', 'S5', 'S6']
stream_list = ['',"EAST", "SOUTH", 'WEST', 'NORTH']
gender_list = ['','MALE','FEMALE']

def fetch_student_by_username(db, username):
    cursor = db.cursor()
    select_student_query = """
    SELECT user_id, full_name, age, "class", stream, username, email, contact, password_hash
    FROM users
    WHERE username = ?
    """
    cursor.execute(select_student_query, (username,))
    student = cursor.fetchone()
    cursor.close()
    return student


from datetime import datetime
import bcrypt
import streamlit as st


def edit_student_record(db, user_id, new_age, username, password, email, contact, new_class, new_stream):
    db = create_connection()  # Make sure create_connection is your DB connect function
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor = db.cursor()
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') if password else None
        cursor.execute("""
            UPDATE users
            SET age = ?, username = ?, 
                password_hash = COALESCE(?, password_hash),
                email = ?, contact = ?, 
                "class" = ?, stream = ?, 
                last_update = ?
            WHERE user_id = ?
        """, (
            new_age,
            username,
            hashed_pw,
            email,
            contact,
            new_class,
            new_stream,
            now,
            user_id
        ))
        db.commit()
        st.session_state.update_success = now
    except Exception as e:
        st.error(f"❌ Failed to update student record: {e}")
    finally:
        cursor.close()


def edit_student(db):
    if 'edit_student' in st.session_state and st.session_state.edit_student:
        student = st.session_state.edit_student
        if 'show_password_fields' not in st.session_state:
            st.session_state.show_password_fields = False
        if st.button("Change Password"):
            st.session_state.show_password_fields = not st.session_state.show_password_fields
            st.rerun() 

        with st.form('Edit Profile Form'):
            st.markdown("""
<div style="display:flex;align-items:center;gap:10px;">
  <div style="font-size:28px;padding:10px;border-radius:50%;background:#00897b;color:#fff;display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;">
    👤
  </div>
  <div>
    <div style="font-size:20px;font-weight:700;color:orange;">Edit Profile</div>
    <div style="font-size:12px;color:#586e75;">Update your account details below</div>
  </div>
</div>
""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            username = col1.text_input(":orange[username]", value=student['username'])
            email = col1.text_input(":orange[Email]", value=student['email'])
            contact = col2.text_input(":orange[Contact]", value=student['contact'])
            new_age = col2.number_input(":orange[AGE (yrs)]", value=student['age'], min_value=1, step=1)
            class_index = class_list.index(student['student_class']) if student['student_class'] in class_list else 0
            new_class = col1.selectbox(":orange[CLASS]", class_list, index=class_index)
            stream_index = stream_list.index(student['stream']) if student['stream'] in stream_list else 0
            new_stream = col2.selectbox(":orange[STREAM]", stream_list, index=stream_index)
            if st.session_state.show_password_fields:
                old_password = col1.text_input(":orange[Old Password]", type="password")
                new_password = col2.text_input(":orange[New Password]", type="password")
            else:
                old_password = None
                new_password = None
            update = st.form_submit_button(':orange[Update Profile]')
            if update:
                if st.session_state.show_password_fields:
                    if not old_password or not new_password:
                        st.error("❌ Please enter both old and new passwords.")
                        return
                    if not bcrypt.checkpw(old_password.encode('utf-8'), student['password_hash'].encode('utf-8')):
                        st.error("❌ Old password is incorrect. Please try again.")
                        return
                else:
                    new_password = None

                edit_student_record(
                    db,
                    student['user_id'],
                    new_age,
                    student['username'],
                    new_password,
                    email,
                    contact,
                    new_class,
                    new_stream,
                )
                st.session_state.edit_student.update({
                    'username': username,
                    'email': email,
                    'contact': contact,
                    'age': new_age,
                    'student_class': new_class,
                    'stream': new_stream,
                })
                st.session_state.show_password_fields = False  # reset toggle
                st.rerun()

        if st.session_state.get('update_success'):
            st.success(f"✅ Record updated at {st.session_state['update_success']}")
            del st.session_state['update_success']


def search_edit_and_update_student(db, username):
    if username:
        student = fetch_student_by_username(db, username)
        if student:
            student_dict = {
                'user_id': student[0],
                'name': student[1],
                'age': student[2],
                'student_class': student[3],  # class
                'stream': student[4],         # stream
                'username': student[5],
                'email': student[6],
                'contact': student[7],
                'password_hash': student[8]   # password hash
            }
            st.session_state.edit_student = student_dict
            edit_student(db)
        else:
            st.error("Student record not found in the database.")

def display_student_profile(username, is_mobile):
    if username:
        st_details = fetch_student_details_by_username(username)
        st_details.pop("password", None)
        def format_line(label, value):
            return f"<div style='margin-bottom:6px;'><span style='color:#c0392b; font-weight:bold;'>{label}:</span> <span style='color:#27ae60;'>{value}</span></div>"
        profile_html = ""
        profile_fields = [
            ("User ID", st_details.get("user_id", "")),
            ("Name", st_details.get("full_name", "")),
            ("Gender", st_details.get("gender", "")),
            ("Age", f'{st_details.get("age", "-")} Years'),
            ("Class", st_details.get("class", "")),
            ("Stream", st_details.get("stream", "")),
            ("Contact", st_details.get("contact", "")),
            ("Username", st_details.get("username", "")),
            ("Email", st_details.get("email", "")),
            ("Role", st_details.get("role", "")),
            ("Registered On", st_details.get("registration_date", "")),
            ("Last Update", st_details.get("last_updated", "Not available"))]
        for label, value in profile_fields:
            profile_html += format_line(label, value)
        if is_mobile:
            with st.expander("STUDENT PROFILE", expanded=False):
                st.markdown(profile_html, unsafe_allow_html=True)
        else:
            with st.sidebar.expander("STUDENT PROFILE", expanded=True):
                st.markdown(profile_html, unsafe_allow_html=True)



def profile_update(db, username, is_mobile):
    if "show_profile_form" not in st.session_state:
        st.session_state.show_profile_form = False
    st.markdown("""
    <style>
    .top-right-button {
        position: absolute;
        top: 20px;
        right: 20px;
        z-index: 999;
    }
    div.stButton > button {
        background-color: red;
        color: white !important;
        padding: 12px 28px;
        border-radius: 25px;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
    }
    div.stButton > button:hover {
        background-color: green;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="top-right-button">', unsafe_allow_html=True)
    if not is_mobile:
        if st.sidebar.button("👤 EDIT PROFILE"):
            st.session_state.show_profile_form = not st.session_state.show_profile_form
    else:
        if st.button("👤 EDIT PROFILE"):
            st.session_state.show_profile_form = not st.session_state.show_profile_form

    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.show_profile_form:
        set_full_page_background('images/black_strip.jpg')
        search_edit_and_update_student(db, username)
        if st.button("Close Profile"):
            st.session_state.show_profile_form = False
            time.sleep(5)
            st.rerun()

def main():
    set_full_page_background('images/psy4.jpg')
    device_width = st_javascript("window.innerWidth", key="menu_device_width")
    username = st.session_state.get("user_name")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    
    db=create_connection()
    if username:
        st_details = fetch_student_details_by_username(username)
        st.session_state.student_id = st_details.get("student_id")
        st.session_state.name = st_details.get("full_name")
        st.session_state.student_class = st_details.get("class")
        st.session_state.stream = st_details.get("stream")
        st.session_state.gender = st_details.get("gender")
        st.session_state.contact = st_details.get("contact")
    display_student_profile(username, is_mobile)

    profile_update(db, username, is_mobile)
    
    action = st.session_state.get("student_action")
   

    if action == "tasks":
        student_tasks_page()
    elif action == "find help":
        student_chats_page()
    elif action == "resources":
        show_resources_menu("📚 Student Resource Center")
    elif action =='feedback':
        student_feedbback_page()
    else:
        student_menu()
if __name__  == "__main__":
    main()
