import streamlit as st
from streamlit_card import card
import streamlit as st
import base64
import os
import datetime
from datetime import datetime
import sqlite3
from datetime import datetime
import bcrypt
import streamlit as st
import teachers_observations
import cont
from streamlit_javascript import st_javascript
import contact_form
import time
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import streamlit as st
from twilio.rest import Client as TwilioClient
import teachers_tool_page
DB_PATH = "users_db.db"


for key in ["name", "user_email", "contact"]:
    if key not in st.session_state:
        st.session_state[key] = ""
def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

def fetch_user_record(username):
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


def fetch_user_details_by_username(username):
    connection = create_connection()
    user_details = {}
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            record = cursor.fetchone()
            user_details = dict(record) if record else {}
        except Exception as e:
            st.error(f"Error fetching user details: {e}")
        finally:
            cursor.close()
            connection.close()
    return user_details


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






def fetch_user_by_username(db, username):
    cursor = db.cursor()
    select_user_query = """
    SELECT user_id, full_name, age, "class", stream, username, email, contact, password_hash
    FROM users
    WHERE username = ?
    """
    cursor.execute(select_user_query, (username,))
    user = cursor.fetchone()
    cursor.close()
    return user



def display_user_profile(username, is_mobile):
    if username:
        st_details = fetch_user_details_by_username(username)
        st_details.pop("password", None)
        def format_line(label, value):
            return f"<div style='margin-bottom:6px;'><span style='color:#c0392b; font-weight:bold;'>{label}:</span> <span style='color:#27ae60;'>{value}</span></div>"
        profile_html = ""
        profile_fields = [
            ("User ID", st_details.get("user_id", "")),
            ("Name", st_details.get("full_name", "")),
            ("Contact", st_details.get("contact", "")),
            ("Username", st_details.get("username", "")),
            ("Email", st_details.get("email", "")),
            ("Role", st_details.get("role", "")),
            ]
        for label, value in profile_fields:
            profile_html += format_line(label, value)
        if is_mobile:
            with st.expander("user PROFILE", expanded=False):
                st.markdown(profile_html, unsafe_allow_html=True)
        else:
            with st.sidebar.expander("user PROFILE", expanded=True):
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
        search_edit_and_update_user(db, username)
        if st.button("Close Profile"):
            st.session_state.show_profile_form = False
            time.sleep(5)
            st.rerun()



CARD_COLORS = [
    "linear-gradient(135deg, #1abc9c, #16a085)",
    "linear-gradient(135deg, #3498db, #2980b9)",
    "linear-gradient(135deg, #9b59b6, #8e44ad)",
    "linear-gradient(135deg, #e67e22, #d35400)",
    "linear-gradient(135deg, #e74c3c, #c0392b)",
]

def user_menu():
    device_width = st_javascript("window.innerWidth", key="screen_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    cols_per_row = 1 if is_mobile else 4
    card_height = "180px" if is_mobile else "220px"
    card_width = "100%"
    font_size_title = "50px" if is_mobile else "90px"
    font_size_text = "20px" if is_mobile else "30px"
    pages = [
        {"title": "📚", "text": "Resources", "key": "resources"},
        {"title": "📝", "text": "Observations", "key": "observations"},
        {"title": "🎋", "text": "Feedback", "key": "feedback"},
        {"title": "📅", "text": "Appointments", "key": "appointment"},]
    rows = [pages[i:i + cols_per_row] for i in range(0, len(pages), cols_per_row)]
    for row_idx, row in enumerate(rows):
        cols = st.columns(cols_per_row, gap="small")
        for col_idx, (col, item) in enumerate(zip(cols, row)):
            color = CARD_COLORS[(row_idx * cols_per_row + col_idx) % len(CARD_COLORS)]
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
                            "box-shadow": "0 4px 12px rgba(0,0,0,0.25)",
                            "border": "0.1px solid #600000",
                            "text-align": "center",
                            "padding": "10px",
                            "margin": "0",
                        },
                        "title": {"font-family": "serif", "font-size": font_size_title},
                        "text": {"font-family": "serif", "font-size": font_size_text},
                    }
                )
                if clicked:
                    st.session_state.user_action = item["text"].lower()
                    st.rerun()

def display_card_menu(page_title, options, selected_key, num_cols=3):
    if f"{selected_key}_just_clicked" not in st.session_state:
        st.session_state[f"{selected_key}_just_clicked"] = False
    device_width = st_javascript("window.innerWidth", key=f"device_width_{selected_key}")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = 1 if is_mobile else num_cols
    card_height = "150px" if is_mobile else "200px"
    card_width = "100%"
    font_size_title = "50px" if is_mobile else "70px"
    font_size_text = "25px"

    cols = st.columns(num_cols_app, gap='small')

    for index, item in enumerate(options):
        color = CARD_COLORS[index % len(CARD_COLORS)]
        card_key = item.get("key", f"{item['text']}_{index}")  # Ensure a unique key

        with cols[index % num_cols_app]:
            clicked = card(
                title=item["title"],
                text=item["text"],
                key=card_key,
                styles={
                    "card": {
                        "width": card_width,
                        "height": card_height,
                        "border-radius": "2px",
                        "background": color,
                        "color": "white",
                        "box-shadow": "0 4px 12px rgba(0,0,0,0.25)",
                        "border": "2px solid #600000",
                        "text-align": "center",
                        "margin": "0px",
                    },
                    "title": {"font-family": "serif", "font-size": font_size_title},
                    "text": {"font-family": "serif", "font-size": font_size_text},
                }
            )

            if clicked and not st.session_state[f"{selected_key}_just_clicked"]:
                st.session_state[selected_key] = item["text"]
                st.session_state[f"{selected_key}_just_clicked"] = True
                st.rerun()

    st.session_state[f"{selected_key}_just_clicked"] = False


def user_observations_page():
    if st.button("🔙 Menu"):
        st.session_state.user_action = None
        st.rerun()
    teachers_observations.main()

def user_appintments_page():
    if st.button("🔙 Menu"):
        st.session_state.user_action = None
        st.rerun()
    teachers_tool_page.main()


def user_chats_page():
    if st.button("🔙 Menu"):
        st.session_state.user_action = None
        st.rerun()
    contact_form.main()


def user_feedback_page():
    if st.button("🔙 Menu"):
        st.session_state.user_action = None
        st.rerun()
    username = st.session_state.get("user_name")
    feed_back_button()
    view_feedback(username)


def show_resources_menu(page_title):
    if st.button("🔙 Home"):
        st.session_state.user_action = None
        st.rerun()

    resource_options = [
        {"title": "🧠", "text": "Challenges", "module": "cont", "key": "challenges"},
        {"title": "🛠️", "text": "Self-Help", "module": "help_tech", "key": "self_help"},
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
            except Exception:
                st.info("🚧 This page is under development and coming soon.")
            return
    display_card_menu(page_title, resource_options, selected_key=selected_key, num_cols=4)

def show_appointments_menu(page_title):
    if st.button("🔙 Home"):
        st.session_state.user_action = None
        st.rerun()

    appointmnet_options = [
        {"title": "", "text": "Status", "module": "cont", "key": "challenges"},
        {"title": "🛠️", "text": "", "module": "help_tech", "key": "self_help"},
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
            except Exception:
                st.info("🚧 This page is under development and coming soon.")
            return
    display_card_menu(page_title, resource_options, selected_key=selected_key, num_cols=4)



#### REQUEST FO APPOINTMENTS ####
username = st.session_state.get("user_name")
if username:
        user_details = fetch_user_details_by_username(username)
        st.session_state.user_id = user_details.get("user_id")
        st.session_state.name = user_details.get("full_name")
        st.session_state.user_email = user_details.get("email")
        st.session_state.contact = user_details.get("contact")
def fetch_all_therapists(conn, include_any=True):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT full_name, profession, email, contact 
            FROM users 
            WHERE role = ?
        """, ("Therapist",))
        rows = cur.fetchall()

        therapists = []
        if include_any:
            therapists.append({
                "display": "Any Available",
                "full_name": None,
                "profession": None,
                "email": None,
                "contact": None})
        for row in rows:
            therapists.append({
                "display": f"{row[0]} ({row[1]})",
                "full_name": row[0],
                "profession": row[1],
                "email": row[2],
                "contact": row[3]})
        return therapists

    except sqlite3.Error as e:
        print(f"Error fetching therapists: {e}")
        return []


def display_profile(is_mobile=True):
    if "show_profile" not in st.session_state:
        st.session_state.show_profile = False
    username = st.session_state.get("user_name")
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
            cursor: pointer;}
        div.stButton > button:hover {
            background-color: #e53935;
            color: white !important;}
        </style>
    """, unsafe_allow_html=True)
    if st.sidebar.button("Display Profile"):
        st.session_state.show_profile = not st.session_state.show_profile
    if st.session_state.show_profile:
        if username:
            display_user_profile(username, is_mobile)
    


def send_email_notification(client_email, therapist_email, therapist_name, client_name, date, time, reason, client_phone):
    import smtplib, traceback
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from twilio.rest import Client as TwilioClient
    import streamlit as st
    import pandas as pd

    # Load secrets
    try:
        sender_email = st.secrets["U"]
        smtp_server = st.secrets["SERVER"]
        smtp_port = int(st.secrets["PORT"])
        smtp_password = st.secrets["SECRET"]
    except KeyError as e:
        st.error(f"❌ Missing secret key: {e}")
        st.text(traceback.format_exc())
        return

    # Message templates
    therapist_body = f"""
Dear {therapist_name},

You have a new appointment request from {client_name}.

──────────────────────────────
🧑 Client Name: {client_name}
📧 Client Email: {client_email}
📱 Client Phone: {client_phone}
📅 Date: {date}
🕒 Time: {time}
📝 Reason: {reason}
──────────────────────────────

Please contact the client directly to confirm or reschedule.
"""

    client_body = f"""
Dear {client_name},

Your appointment request with {therapist_name} has been received.
──────────────────────────────
📅 Date: {date}
🕒 Time: {time}
📝 Reason: {reason}
──────────────────────────────

You will be contacted to confirm or reschedule.
Thank you for using our Appointment Booking System.
"""

    # Helper to send email
    def send_email(to_email, body, subject):
        try:
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # st.info(f"🔄 Sending email to {to_email}...")
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(sender_email, smtp_password)
                    server.sendmail(sender_email, to_email, msg.as_string())
            else:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, smtp_password)
                    server.sendmail(sender_email, to_email, msg.as_string())
        except Exception as e:
            raise e
    notification_status = []
    if therapist_email:
        try:
            send_email(therapist_email, therapist_body, subject="📅 New Appointment Request")
            notification_status.append({"Type": "Email (Therapist)", "Status": "✅ Sent"})
        except Exception as e:
            notification_status.append({"Type": "Email (Therapist)", "Status": f"❌ Failed: {e}"})
    if client_email:
        try:
            send_email(client_email, client_body, subject="📅 Appointment Confirmation")
            notification_status.append({"Type": "Email (Client)", "Status": "✅ Sent"})
        except Exception as e:
            notification_status.append({"Type": "Email (Client)", "Status": f"❌ Failed: {e}"})

    try:
        twilio_sid = st.secrets["TWILIO_SID"]
        twilio_token = st.secrets["TWILIO_AUTH_TOKEN"]
        twilio_from = st.secrets["TWILIO_PHONE"]
        twilio_client = TwilioClient(twilio_sid, twilio_token)
        sms_message = f"New Appointment:\nClient: {client_name}\nDate: {date}\nTime: {time}"
        twilio_client.messages.create(body=sms_message, from_=twilio_from, to=client_phone)
        notification_status.append({"Type": "SMS (Client)", "Status": "✅ Sent"})
    
    except KeyError:
        notification_status.append({"Type": "SMS (Client)", "Status": "⚠️ Twilio credentials missing"})
    except Exception as e:
        notification_status.append({"Type": "SMS (Client)", "Status": f"❌ Failed: {e}"})

def create_appointment_requests_table():
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            client_email TEXT NOT NULL,
            client_phone TEXT,
            therapist_name TEXT,
            therapist_email TEXT,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT,
            response TEXT,
            responder TEXT,
            response_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_appointment(client_name, client_email, client_phone, therapist_name, therapist_email, appointment_date, appointment_time, reason):
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO appointment_requests (
            client_name, client_email, client_phone, therapist_name, therapist_email,
            appointment_date, appointment_time, reason, response, responder, response_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
    """, (client_name, client_email, client_phone, therapist_name, therapist_email, str(appointment_date), str(appointment_time), reason))
    conn.commit()
    conn.close()


import threading
import streamlit as st
import time as t

def send_notifications_async(client_email, therapist_email, therapist_name, client_name, date, time, reason, client_phone):
    """Send emails and SMS in a background thread"""
    thread = threading.Thread(
        target=send_email_notification,
        args=(client_email, therapist_email, therapist_name, client_name, date, time, reason, client_phone)
    )
    thread.start()

def book_appointment():
    create_appointment_requests_table()
    if "show_appointment_form" not in st.session_state:
        st.session_state.show_appointment_form = False

    conn = create_connection()
    therapist_list = fetch_all_therapists(conn)

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

    if st.button("🗓️ Request for an appointment"):
        st.session_state.show_appointment_form = not st.session_state.show_appointment_form

    if st.session_state.show_appointment_form:
        set_full_page_background('images/black_strip.jpg')
        with st.form("appointment_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input(":orange[Full Name]", value=st.session_state.name)
            email = col1.text_input(":orange[Email Address]", value=st.session_state.user_email)
            tel = col1.text_input(":orange[Telephone]", value=st.session_state.contact)

            # Build therapist selectbox
            therapist_display_names = [t["display"] for t in therapist_list]
            if "Any Available" not in therapist_display_names:
                therapist_display_names.insert(0, "Any Available")  # add top option

            selected_display = col2.selectbox('Prefer to speak to:', therapist_display_names)

            if selected_display == "Any Available":
                selected_therapist_name = "Any Available"
                selected_therapist_email = "any@available.com"  # placeholder
            else:
                selected_therapist = next(t for t in therapist_list if t["display"] == selected_display)
                selected_therapist_name = selected_therapist["full_name"]
                selected_therapist_email = selected_therapist["email"]

            date = col2.date_input(":orange[Preferred Date]")
            time = col2.time_input(":orange[Preferred Time]")
            reason = st.text_area(":orange[Reason for Appointment]", height=100)
            submitted = st.form_submit_button("✅ Submit Appointment")

            if submitted:
                if name.strip() and email.strip() and reason.strip():
                    # Save appointment immediately
                    save_appointment(
                        client_name=name,
                        client_email=email,
                        client_phone=tel,
                        therapist_name=selected_therapist_name,
                        therapist_email=selected_therapist_email,
                        appointment_date=date,
                        appointment_time=time,
                        reason=reason)
                    send_notifications_async(
                        client_email=email,
                        therapist_email=selected_therapist_email,
                        therapist_name=selected_therapist_name,
                        client_name=name,
                        date=date,
                        time=time,
                        reason=reason,
                        client_phone=tel
                    )

                    st.success(f"✅ Appointment booked with {selected_display} on {date} at {time}")
                    t.sleep(1)
                    st.session_state.show_appointment_form = False
                    st.rerun()
                else:
                    st.warning("⚠️ Please fill in all required fields.")



###### DRIVER CODE #########
def main():
    create_appointment_requests_table()
    set_full_page_background('images/psy4.jpg')
    if "user_action" not in st.session_state:
        st.session_state.user_action = None
    username = st.session_state.get("user_name")
    device_width = st_javascript("window.innerWidth", key="device_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704 
    db = create_connection()
    if username:
        col1, col2 = st.columns([1,3])
        with col1:
            display_profile(is_mobile)
        with col2:
            book_appointment()
    action = st.session_state.user_action
    if action == "observations":
        user_observations_page()
    elif action == "resources":
        show_resources_menu("📚 User Resource Center")
    elif action == 'appointments':
        user_appintments_page()
    elif action == "feedback":
        user_feedback_page()
    elif action == "find help":
        user_chats_page()
    else:
        user_menu()
if __name__ == "__main__":
    main()
