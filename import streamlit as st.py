import streamlit as st
st.set_page_config(layout='wide')
from PIL import Image
from streamlit_option_menu import option_menu
import os, base64
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu
import auth 
import sqlite3

import bcrypt
import time

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


# force_light_theme()
DB_PATH = "users_db.db"
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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


def auto_slider_with_quotes_and_button(images, quotes, button_text="Learn More", button_link="#", key_prefix="slider"):
    index_key = f"{key_prefix}_index"
    if index_key not in st.session_state:
        st.session_state[index_key] = 0

    total = len(images)
    index = st.session_state[index_key]
    refresh_interval = 10000 if index < total - 1 else 20000  # Last slide pauses longer
    st_autorefresh(interval=refresh_interval, key=f"{key_prefix}_refresh")

    if "last_refresh" not in st.session_state or st.session_state["last_refresh"] != index:
        st.session_state[index_key] = (index + 1) % total
        st.session_state["last_refresh"] = index

    with open(images[index], "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    quote_text = quotes[index]

    st.markdown(f"""
        <style>
        .hero {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            height: 75vh;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            text-align: center;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            border-radius: 1px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
            flex-direction: column;
        }}

        .overlay-text {{
            font-size: 2.2em;
            font-weight: 600;
            text-shadow: 2px 2px 6px black;
            margin: 0 10px 20px;
        }}

        .button {{
            "text-align: center; padding: 15px;">
            <a href='#' style='
            background-color: #00897b;
            color: white;
            padding: 12px 28px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);'

            padding: 0.75em 1.5em;
            font-size: 1.1em;
            border: 2px solid red;
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 80px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
        }}

        .button:hover {{
            background-color: red;
            color: black;
        }}
        </style>

        <div class="hero">
            <div class="overlay-text">{quote_text}</div>
            <a href="{button_link}" class="button">{button_text}</a>
        </div>
    """, unsafe_allow_html=True)

def button_click():
    st.markdown("""
        <style>
        .custom-button {
            background-color: #00897b;
            color: white !important;
            padding: 12px 28px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            display: inline-block;
        }

        .custom-button:hover {
            background-color: #e53935;
            color: white !important;
        }
        </style>

        <div style="text-align: center; margin-top: 20px;">
            <a href="#" class="custom-button">🌿 Book Appointment</a>
        </div>
    """, unsafe_allow_html=True)


@st.dialog("💬 Anonymous Feedback")
def feedback_dialog():
    st.markdown("""
        <h4 style='color:#0d47a1;font-size:20px;'>We're here to listen.</h4>
        <p style='font-size:20px;background-color:#1b4f72;'>Your thoughts help build a better mental health experience for everyone.</p>
    """, unsafe_allow_html=True)

    feedback = st.text_area("Your message:", height=200, placeholder="I feel...")

    if st.button("✅ Submit"):
        if feedback.strip():
            st.session_state["feedback_response"] = feedback
            st.success("Thank you for your feedback 💚")
            st.rerun()
        else:
            st.warning("Please enter your thoughts before submitting.")


images = ['images/std.jpg', 'images/std3.jpg','images/std4.jpg']
quotes = [
    "Your mind matters as much as your grades.",
    "Strong minds ask for help. That’s real strength.",
    "Healthy minds. Safe spaces. Stronger schools."]
def home_page():
    st.markdown("""
    <div style="
        background: linear-gradient(to right, #b2dfdb, #e1bee7);
        padding: 50px;
        text-align: center;
        color: #2c3e50;
        font-size: 28px;
        font-weight: bold;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-family: 'Segoe UI', sans-serif;
    ">
        🧠 Mental Health Hub for Students, Teachers & Parents
        <br>
        <span style="font-size: 18px; font-weight: normal;">
            A safe space to connect, understand your feelings, and seek help with compassion and care.
        </span>
    </div>
    """, unsafe_allow_html=True)
    auto_slider_with_quotes_and_button(images, quotes, button_text="Explore Mental Health Resources", button_link="https://example.com")
    st.markdown("### ")

    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        st.markdown("""
        <div style="
            background-color: #f3f8fb;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.05);
            font-family: 'Segoe UI', sans-serif;">
            <h4 style="color:#1b4f72; margin-top: 25px;">📞 Reach Out</h4>
            <p style="font-size: 16px; color:#333;">
                📱 WhatsApp: <strong>0781 950 263</strong><br>
                ☎️ Call: <strong>0200 804 010</strong><br>
                <em>(Mon–Fri, 9 AM–6 PM)</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style="
                background-color: #f3f8fb;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.05);
                font-family: 'Segoe UI', sans-serif;
                margin-top: 20px;
                text-align: center;">
                <h3 style="color:#1b4f72;">💬 Share Your Thoughts</h3>
                <p style="font-size: 16px; line-height: 1.6; color:#1b4f72;">
                    Your voice matters. Help us create a better, safer environment by sharing your anonymous feedback.<br>
                    We're here to listen <strong>every day from 9 AM to 6 PM</strong>.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(":blue[Give Your Feedback]"):
            feedback_dialog()
        if "feedback_response" in st.session_state:
            st.success("✅ Your feedback was submitted successfully. Thank you for sharing.")
        button_click()

    with col3:
        st.markdown("""
        <div style="
            background-color: #f3f8fb;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.05);
            font-family: 'Segoe UI', sans-serif;">
            <h4 style="color:#1b4f72; margin-top: 35px;">❓ Frequently Asked Questions</h4>
            <details style="margin-top: 15px;">
              <summary style="font-weight: bold; font-size: 18px; cursor: pointer;color:#1b4f72;">How do I know if my child needs mental health support?</summary>
              <p style="margin-left: 15px; font-size: 16px; color:#444;">
                Look for changes in mood, behavior, sleep, or appetite lasting more than two weeks. 
                If you're worried, consult a counselor or healthcare professional for an evaluation.
              </p>
            </details>
            <details style="margin-top: 15px;">
              <summary style="font-weight: bold; font-size: 18px; cursor: pointer;color:#1b4f72;">What mental health resources are available for students at school?</summary>
              <p style="margin-left: 15px; font-size: 16px; color:#444;">
                Many schools offer counseling services, peer support groups, and mental health awareness programs. 
                Reach out to your school counselor or health office for guidance.
              </p>
            </details>
            <details style="margin-top: 15px;">
              <summary style="font-weight: bold; font-size: 18px; cursor: pointer; color:#1b4f72;">How can teachers support students struggling with mental health?</summary>
              <p style="margin-left: 15px; font-size: 16px; color:#444;">
                Teachers can create a safe and supportive classroom environment, listen without judgment, 
                and refer students to school counselors or mental health professionals when needed.
              </p>
            </details>
            <details style="margin-top: 15px;">
              <summary style="font-weight: bold; font-size: 18px; cursor: pointer;color:#1b4f72;">Is mental health support confidential?</summary>
              <p style="margin-left: 15px; font-size: 16px; color:#444;">
                Yes, professional mental health services respect your privacy and keep your information confidential 
                unless there is a risk of harm to yourself or others.
              </p>
            </details>
            <details style="margin-top: 15px;">
              <summary style="font-weight: bold; font-size: 18px; cursor: pointer;color:#1b4f72;">How can I access emergency mental health help?</summary>
              <p style="margin-left: 15px; font-size: 16px; color:#444;">
                If you or someone you know is in crisis, call emergency services immediately or visit the nearest hospital emergency department.
              </p>
            </details>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### ")
    with st.container():
        st.markdown("""
        <div style="text-align: center; padding: 15px;">
            <a href='#' style='
                background-color: #00897b;
                color: white;
                padding: 12px 28px;
                border-radius: 25px;
                text-decoration: none;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);'
            >
                🌿 Explore Mental Health Resources →
            </a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

from streamlit_option_menu import option_menu

defaults = {
    "page": "login",
    "show_login": False,
    "show_signup": False,
    "logged_in": False,
    "user_name": "",
    "user_role": "",
    "admin_redirect": False,
    "notified": False
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

def logout():
    for key in ["logged_in", "user_name", "user_role", "show_login", "admin_redirect", "notified"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("👋 Logged out successfully.")
    st.rerun()





def button_click():
    if "show_appointment_form" not in st.session_state:
        st.session_state.show_appointment_form = False
    # col1, col2, col3 = st.columns([1, 2, 1])
    # with col2:
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

    if st.button("🗓️Book Appointment"):
        st.session_state.show_appointment_form = True
    if st.session_state.show_appointment_form:
        with st.form("appointment_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            date = st.date_input("Preferred Date")
            time = st.time_input("Preferred Time")
            reason = st.text_area("Reason for Appointment", height=100)
            submitted = st.form_submit_button("✅ Submit Appointment")
            if submitted:
                if name.strip() and email.strip() and reason.strip():
                    st.success(f"✅ Appointment booked for {name} on {date} at {time}")
                    st.session_state.show_appointment_form = False 
                    st.rerun() 
                else:
                    st.warning("⚠️ Please fill in all required fields.")



##### CODE ######
def main():
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

        # if st.button("🚪 Logout"):
        #     logout()
        return

    menu = option_menu(
        menu_title='',
        options=["Home", "Resources", "Services", "SignIn", "Help"],
        icons=["house", "folder", "hospital", "box-arrow-in-right", "question-circle"],
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#1b4f72"},
            "icon": {"color": "white", "font-size": "22px"},
            "nav-link": {"color": "white", "font-size": "20px", "font-weight": "bold"},
            "nav-link-selected": {"background-color": "#2980b9"},
        })

    if menu == "SignIn":
        if st.session_state.get("show_login"):
            auth.show_login_dialog()
        elif st.session_state.get("show_signup"):
            auth.show_signup_dialog()
        else:
            st.session_state.show_login = True
            st.rerun()

    elif menu == "Home":
        home_page()
    elif menu == "Resources":
        import cont
        cont.main()
    

    elif menu == "Services":
        st.info("🛠 Services coming soon.")
    elif menu == "Help":
        st.info("💬 How can we assist you?")

if __name__ == "__main__":
    main()
