import streamlit as st
st.set_page_config(layout='wide')
from PIL import Image
from streamlit_option_menu import option_menu
import os, base64
import auth 
import sqlite3

import bcrypt
import time
from PIL import Image
import os, base64
import pandas as pd

def set_custom_background(bg_color="skyblue", sidebar_img=None):
    page_bg_img = f"""
        <style>
        [data-testid="stAppViewContainer"] > .main {{
            background-color: {bg_color};  i
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
            right: 2rem;}}
        </style>"""
    st.markdown(page_bg_img, unsafe_allow_html=True)

@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_img_as_base64("images/IMG.webp")
set_custom_background(bg_color=None, sidebar_img=img)

if 'page' not in st.session_state:
    st.session_state.page = 'home'
def navigate(page_name):
    st.session_state.page = page_name

def footer():
    st.markdown("©PPPS - Uganda. All rights reserved.", unsafe_allow_html=True)

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

DB_PATH = "users_db.db"
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@st.dialog("💬 Give us Feedback")
def feedback_dialog():
    st.markdown("""
        <h4 style='color:skyblue;font-size:25px;'>We're here to listen.</h4>
        <p style='font-size:20px;'>Your thoughts help build a better mental health experience for everyone.</p>
    """, unsafe_allow_html=True)
    feedback = st.text_area("Your message:", height=200, placeholder="I feel...")
    if st.button("✅ Submit"):
        if feedback.strip():
            st.session_state["feedback_response"] = feedback
            st.success("Thank you for your feedback 💚")
            st.rerun()
        else:
            st.warning("Please enter your thoughts before submitting.")


defaults = {
    "page": "login",
    "show_login": False,
    "show_signup": False,
    "logged_in": False,
    "user_name": "",
    "user_role": "",
    "admin_redirect": False,
    "notified": False}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val
def logout():
    for key in ["logged_in", "user_name", "user_role", "show_login", "admin_redirect", "notified"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("👋 Logged out successfully.")
    st.rerun()

# def button_click():
#     if "show_appointment_form" not in st.session_state:
#         st.session_state.show_appointment_form = False
#     st.markdown("""
#             <style>
#             div.stButton > button {
#                 background-color: #00897b;
#                 color: white !important;
#                 padding: 12px 28px;
#                 border-radius: 25px;
#                 font-size: 16px;
#                 font-weight: bold;
#                 box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
#                 transition: all 0.3s ease;
#                 border: none;
#                 cursor: pointer;
#             }
#             div.stButton > button:hover {
#                 background-color: #e53935;
#                 color: white !important;
#             }
#             </style>
#         """, unsafe_allow_html=True)
#     if st.button("🗓️Book Appointment"):
#         st.session_state.show_appointment_form = True
#     if st.session_state.show_appointment_form:
#         with st.form("appointment_form"):
#             name = st.text_input(":orange[Full Name]")
#             email = st.text_input(":orange[Email Address]")
#             tel = st.text_input(":orange[Telephone]", placeholder='')
#             date = st.date_input(":orange[Preferred Date]")
#             time = st.time_input(":orange[Preferred Time]")
#             reason = st.text_area(":orange[Reason for Appointment]", height=100)
#             submitted = st.form_submit_button("✅ Submit Appointment")
#             if submitted:
#                 if name.strip() and email.strip() and reason.strip():
#                     st.success(f"✅ Appointment booked for {name} on {date} at {time}")
#                     import time
#                     time.sleep(3)
#                     st.session_state.show_appointment_form = False 
#                     st.rerun() 
#                 else:
#                     st.warning("⚠️ Please fill in all required fields.")

import streamlit as st

def button_click():
    if "show_appointment_form" not in st.session_state:
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

    # Toggle form visibility on button click
    if st.button("🗓️ Book Appointment"):
        st.session_state.show_appointment_form = not st.session_state.show_appointment_form

    if st.session_state.show_appointment_form:
        with st.form("appointment_form"):
            name = st.text_input(":orange[Full Name]")
            email = st.text_input(":orange[Email Address]")
            tel = st.text_input(":orange[Telephone]", placeholder='')
            date = st.date_input(":orange[Preferred Date]")
            time = st.time_input(":orange[Preferred Time]")
            reason = st.text_area(":orange[Reason for Appointment]", height=100)

            submitted = st.form_submit_button("✅ Submit Appointment")

            if submitted:
                if name.strip() and email.strip() and reason.strip():
                    st.success(f"✅ Appointment booked for {name} on {date} at {time}")
                    import time
                    time.sleep(3)
                    st.session_state.show_appointment_form = False
                    st.rerun()
                else:
                    st.warning("⚠️ Please fill in all required fields.")

        # Cancel link/button outside the form to close it
        if st.button("Close form"):
            st.session_state.show_appointment_form = False
            st.rerun()

# button_click()


def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    # Appointments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS online_appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            tel TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            reason TEXT NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response TEXT,
            responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responder TEXT
        )
    """)

    # Feedback Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT 'Anonymous',
            message TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response TEXT,
            responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responder TEXT
        )
    """)

    conn.commit()
    conn.close()



def save_feedback(message, name="Anonymous"):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedbacks (name, message) VALUES (?, ?)", (name, message))
    conn.commit()
    conn.close()

def save_appointment(name, email, date, appointment_time, reason, tel=""):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO online_appointments (name, email, tel, date, time, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, tel, str(date), str(appointment_time), reason))
    conn.commit()
    conn.close()


def appointment_section():
    if "show_appointment_form" not in st.session_state:
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
        }
        </style>
    """, unsafe_allow_html=True)

    if st.button("🗓️ Book Appointment"):
        st.session_state.show_appointment_form = True

    if st.session_state.show_appointment_form:
        with st.form("appointment_form"):
            st.subheader("📋 Appointment Form")
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            tel = st.text_input("Phone Number")
            date = st.date_input("Preferred Date")
            appointment_time = st.time_input("Preferred Time")
            reason = st.text_area("Reason for Appointment", height=100)

            submitted = st.form_submit_button("✅ Submit Appointment")
            if submitted:
                if name.strip() and email.strip() and tel.strip() and reason.strip():
                    save_appointment(name, email, date, appointment_time, reason, tel)
                    st.success(f"✅ Appointment booked for {name} on {date} at {appointment_time}")
                    st.session_state.show_appointment_form = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("⚠️ Please fill in all required fields.")




create_tables()
@st.dialog("💬 Feedback")
def feedback_dialog():
    st.markdown("""
        <h4 style='color:skyblue;font-size:25px;'>We're here to listen.</h4>
        <p style='font-size:20px;'>Your thoughts help build a better mental health experience for everyone.</p>
    """, unsafe_allow_html=True)

    name = 'Anonymous'
    feedback = st.text_area("Your Message:", height=200, placeholder="I feel...")

    if st.button("✅ Submit"):
        if feedback.strip():
            save_feedback(message=feedback.strip(), name=name)
            st.success("✅ Thank you for your feedback 💚")
            time.sleep(1.5)
            st.rerun()
        else:
            st.warning("⚠️ Please enter your thoughts before submitting.")


def view_appointments():
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM online_appointments ORDER BY created_at DESC", conn)
    conn.close()
    st.subheader("📅 Online Appointments")
    st.dataframe(df)


##### CODE ######
def main():
    create_connection()
    set_full_page_background('images/dark_green_back.jpg')
    st.markdown("""
        <style>
        [data-testid="stForm"] label {
            color: #1b4f72 !important;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    auth.create_users_db() 
    if st.session_state.get("logged_in"):
        if st.session_state.get("logged_in"):
            st.sidebar.success(f"👋 Welcome, {st.session_state.user_name}")
        db = auth.create_connection()
        db.row_factory = sqlite3.Row  # Enable dictionary-style access
        user = db.execute("SELECT is_active FROM users WHERE username = ?", 
                          (st.session_state.get("user_name"),)).fetchone()
        db.close()
        if user and user["is_active"] == 0:
            st.warning("🚫 Your account has been deactivated. Please contact admin.")
            for key in ["logged_in", "user_name", "user_role", "show_login", "admin_redirect"]:
                st.session_state[key] = False if isinstance(st.session_state[key], bool) else ""
        role = st.session_state.get("user_role")
        if role == "Admin":
            import admin
            admin.main()
            with st.sidebar:
                if st.button("🚪 Logout"):
                    logout()
            st.stop()

        elif role == "Admin2":
            import super_admin
            super_admin.main()
            with st.sidebar:
                if st.button("🚪 Logout"):
                    logout()

        elif role == "Therapist":
            import therapist
            therapist.main()
            with st.sidebar:
                if st.button("🚪 Logout"):
                    logout()
            st.stop()
        elif role in ["Teacher", "Parent"]:
            import student_page
            student_page.main()
            with st.sidebar:
                if st.button("🚪 Logout"):
                    logout()
            st.stop()
        
        elif role in ["Student"]:
            import student_page
            student_page.main()
            with st.sidebar:
                if st.button("🚪 Logout"):
                    logout()
            st.stop()
        return

    menu = option_menu(
        menu_title='',
        options=["Home", "Services", "Account", "Help"],
        icons=["house", "hospital", "person-circle", "question-circle"],
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#1b4f72"},
            "icon": {"color": "white", "font-size": "22px"},
            "nav-link": {"color": "white", "font-size": "20px", "font-weight": "bold"},
            "nav-link-selected": {"background-color": "#2980b9"},
        })

    if menu == "Account":
        set_full_page_background('images/dark_green_back.jpg')
        import welcome
        welcome.main()
        if st.session_state.get("show_login"):
            auth.show_login_dialog()
        elif st.session_state.get("show_signup"):
            auth.show_signup_dialog()
        else:
            st.session_state.show_login = True
            st.rerun()

    elif menu == "Home":
        import welcome
        welcome.main()
        # st.write('---')
        col1, col2, col3 = st.columns([1, 1, 1.5], gap="small")

        with col1:
            st.markdown("""
            <div style="
                background-color: #f3f8fb;
                padding: 25px;
                border-radius: 20px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.05);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 320px;
            ">
                <div>
                    <h4 style="color:#1b4f72; margin-top: 0;">📞 <strong>Reach Out</strong></h4>
                    <p style="font-size: 16px; color:#333; margin-bottom: 15px;">
                        <span style="font-size: 18px;">📱</span> WhatsApp: <strong>0781 950 263</strong><br>
                        <span style="font-size: 18px;">☎️</span> Call: <strong>0200 804 010</strong><br>
                        <em>(Mon–Fri, 9 AM–6 PM)</em>
                    </p>
                </div>
                <div style="margin-top: 15px;">
                    <!-- The button will go here -->
                </div>
            </div>
            """, unsafe_allow_html=True)
            import time
            button_click()

        with col2:
            st.markdown("""
                <div style="
                    background-color: #f3f8fb;
                    padding: 25px;
                    border-radius: 20px;
                    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
                    height: 320px;
                    text-align: center;
                ">
                    <h3 style="color:#1b4f72; margin-top: 0;">💬 <strong>Share Your Thoughts</strong></h3>
                    <p style="font-size: 16px; line-height: 1.6; color:#1b4f72;">
                        Your voice matters. Help us create a better, safer environment by sharing your anonymous feedback.<br>
                        We're here to listen <strong>every day from 9 AM to 6 PM</strong>.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Give Your Feedback"):
                feedback_dialog()  # Your feedback dialog function

        with col3:
            st.markdown("""
            <div style="
                background-color: #f3f8fb;
                padding: 25px;
                border-radius: 20px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.05);
                height: 320px;
                overflow-y: auto;
            ">
                <h4 style="color:#1b4f72; margin-top: 0;">❓ <strong>Frequently Asked Questions</strong></h4>
                <details style="margin-top: 15px;">
                  <summary style="font-weight: bold; font-size: 16px; cursor: pointer; color:#1b4f72;">How do I know if my child needs mental health support?</summary>
                  <p style="margin-left: 15px; font-size: 14px; color:#444;">
                    Look for changes in mood, behavior, sleep, or appetite lasting more than two weeks. 
                    If you're worried, consult a counselor or healthcare professional for an evaluation.
                  </p>
                </details>
                <details style="margin-top: 10px;">
                  <summary style="font-weight: bold; font-size: 16px; cursor: pointer; color:#1b4f72;">What mental health resources are available for students at school?</summary>
                  <p style="margin-left: 15px; font-size: 14px; color:#444;">
                    Many schools offer counseling services, peer support groups, and mental health awareness programs. 
                    Reach out to your school counselor or health office for guidance.
                  </p>
                </details>
                <details style="margin-top: 10px;">
                  <summary style="font-weight: bold; font-size: 16px; cursor: pointer; color:#1b4f72;">How can teachers support students struggling with mental health?</summary>
                  <p style="margin-left: 15px; font-size: 14px; color:#444;">
                    Teachers can create a safe and supportive classroom environment, listen without judgment, 
                    and refer students to school counselors or mental health professionals when needed.
                  </p>
                </details>
                <details style="margin-top: 10px;">
                  <summary style="font-weight: bold; font-size: 16px; cursor: pointer; color:#1b4f72;">Is mental health support confidential?</summary>
                  <p style="margin-left: 15px; font-size: 14px; color:#444;">
                    Yes, professional mental health services respect your privacy and keep your information confidential 
                    unless there is a risk of harm to yourself or others.
                  </p>
                </details>
                <details style="margin-top: 10px;">
                  <summary style="font-weight: bold; font-size: 16px; cursor: pointer; color:#1b4f72;">How can I access emergency mental health help?</summary>
                  <p style="margin-left: 15px; font-size: 14px; color:#444;">
                    If you or someone you know is in crisis, call emergency services immediately or visit the nearest hospital emergency department.
                  </p>
                </details>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.write('---')

    elif menu == "Resources":
        import cont
        cont.main()
    
    elif menu == "Services":
        import services; services.main()
        # st.info("🛠 Services coming soon.")
    


    elif menu == "Help":
        st.info("💬 How can we assist you?")
    footer()
if __name__ == "__main__":
    main()
        



