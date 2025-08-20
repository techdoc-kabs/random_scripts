DB_PATH = "users_db.db"

DB_PATH = "users_db.db"

import streamlit as st
import pandas as pd
import sqlite3

import hashlib
import smtplib
from email.mime.text import MIMEText
from streamlit_option_menu import option_menu
import random
import string
import time

DB_PATH = "users_db.db"

from datetime import datetime

def add_student(first, last, contact, email, username, password, class_, stream, sex, age, parent_guardian, address):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    user_id = generate_user_id("Student")  # Generate unique ID

    try:
        cursor.execute("""
            INSERT INTO users (
                user_id, first_name, last_name, contact, email, username, password_hash,
                role, full_name, class, stream, sex, age, parent_guardian, address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Student', ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, first, last, contact, email, username, pw_hash,
              f"{first} {last}", class_, stream, sex, age, parent_guardian, address))
        conn.commit()
    except sqlite3.IntegrityError:
        st.warning(f"Username '{username}' already exists. Skipping.")
    conn.close()


def fetch_all_students():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query("SELECT user_id, first_name, last_name, contact, email, username, class, stream FROM users WHERE role = 'Student'", conn)
    conn.close()
    return df


def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, first_name FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        stored_hash, first_name = row
        if hashlib.sha256(password.encode()).hexdigest() == stored_hash:
            return True, first_name
    return False, None


def update_password(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
    conn.commit()
    conn.close()


#### password reset #####
OTP_EXPIRY_SECONDS = 600  # 10 minutes

def create_otp_table():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_otp (
            username TEXT PRIMARY KEY,
            otp TEXT,
            created_at INTEGER
        )
    """)
    conn.commit()
    conn.close()


def save_otp(username, otp):
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        INSERT OR REPLACE INTO password_reset_otp (username, otp, created_at) VALUES (?, ?, ?)
    """, (username, otp, now))
    conn.commit()
    conn.close()


def verify_otp(username, otp):
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("""
        SELECT otp, created_at FROM password_reset_otp WHERE username = ?
    """, (username,)).fetchone()
    conn.close()

    if not row:
        return False
    saved_otp, created_at = row
    return saved_otp == otp and now - created_at <= OTP_EXPIRY_SECONDS


def get_user_email(username):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT email FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row[0] if row else None


def send_email_otp(to_email, otp):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "kabpol1@gmail.com"
    SMTP_PASSWORD = "your_app_password"
    subject = "Your Password Reset OTP Code"
    body = f"Your OTP code for password reset is: {otp}\nThis code expires in 10 minutes."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False


def password_reset_flow():
    step = st.session_state.get("reset_step", 1)
    if step == 1:
        with st.form("request_otp_form"):
            username = st.text_input("Enter your username")
            submit_otp_request = st.form_submit_button("Send OTP")
        if submit_otp_request:
            username_lower = username.strip().lower()
            email = get_user_email(username_lower)
            if not email:
                st.error("Username not found.")
            else:
                otp = ''.join(random.choices(string.digits, k=6))
                save_otp(username_lower, otp)
                if send_email_otp(email, otp):
                    st.success(f"OTP sent to {email}. Please check your inbox.")
                    st.session_state.reset_username = username_lower
                    st.session_state.reset_step = 2
                    st.rerun()

    elif step == 2:
        with st.form("verify_otp_form"):
            otp_input = st.text_input("Enter the OTP sent to your email")
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            submit_reset = st.form_submit_button("Reset Password")

        if submit_reset:
            username_lower = st.session_state.get("reset_username")
            if not username_lower:
                st.error("Session expired. Please restart the reset process.")
                st.session_state.reset_step = 1
                return

            if new_password != confirm_password:
                st.warning("Passwords do not match.")
            elif not verify_otp(username_lower, otp_input.strip()):
                st.error("Invalid or expired OTP.")
            else:
                update_password(username_lower, new_password)
                st.success("✅ Password reset successful! You can now log in with your new password.")
                del st.session_state["reset_step"]
                del st.session_state["reset_username"]

def generate_user_id(role):
    prefix_map = {
        'student': 'STUD',
        'parent': 'PARENT',
        'teacher': 'TEACH',
        'therapist': 'USER',
        'admin': 'ADMIN'
    }
    prefix = prefix_map.get(role.lower(), 'GUEST')  # now works as expected
    today = datetime.now().strftime("%Y%m%d")
    like_pattern = f"{prefix}-{today}-%"

    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT user_id FROM users WHERE user_id LIKE ?
            ORDER BY user_id DESC LIMIT 1
        """, (like_pattern,)).fetchone()
    
    next_num = int(row[0].split("-")[-1]) + 1 if row else 1
    return f"{prefix}-{today}-{next_num:04d}"




def main():
    st.markdown("""
            <style>
            [data-testid="stForm"] label {
                color: #1b4f72 !important;
                font-weight: 600;
            }
            </style>
        """, unsafe_allow_html=True)
    with st.sidebar:
        menu = option_menu(
            menu_title='',
            options=["upload_data", "Fetch_data", "Change Password", 'Reset Password'],
            icons=["cloud-upload", "people", "lock", "question-circle"],
            orientation="vertical",
            styles={
                "container": {"padding": "0!important", "background-color": "#1b4f72"},
                "icon": {"color": "white", "font-size": "13px"},
                "nav-link": {"color": "white", "font-size": "13px", "font-weight": "bold"},
                "nav-link-selected": {"background-color": "#2980b9"},})

    if menu == 'upload_data':
        uploaded_file = st.file_uploader("Upload CSV with: first_name, last_name, contact, email, class, stream, sex, age, parent_guardian, address", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("CSV Preview:")
            st.dataframe(df)
            for _, row in df.iterrows():
                add_student(
                    first=str(row.get('first_name', '')).strip().capitalize(),
                    last=str(row.get('last_name', '')).strip().capitalize(),
                    contact=str(row.get('contact', '')).strip(),
                    email=str(row.get('email', '')).strip(),
                    username=f"{str(row.get('first_name', '')).strip().lower()}@{str(row.get('last_name', '')).strip().lower()}",
                    password="password",
                    class_=str(row.get('class', '')),
                    stream=str(row.get('stream', '')),
                    sex=str(row.get('sex', '')),
                    age=int(row['age']) if pd.notna(row.get('age')) else None,
                    parent_guardian=str(row.get('parent_guardian', '')),
                    address=str(row.get('address', ''))
                )

            st.success("✅ Students imported with default passwords!")

    elif menu == 'Fetch_data':
        students_df = fetch_all_students()
        if students_df.empty:
            st.warning("No student records found.")
        else:
            st.success(f"Total students: {len(students_df)}")
            st.dataframe(students_df)

    elif menu == "Change Password":
        st.subheader("🔒 Change Your Password")
        with st.form("change_password_form"):
            username = st.text_input("Username")
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Change Password")

        if submitted:
            valid, _ = authenticate_user(username.strip().lower(), current_pw)
            if not valid:
                st.error("❌ Current password is incorrect.")
            elif new_pw != confirm_pw:
                st.warning("⚠️ New passwords do not match.")
            else:
                update_password(username.strip().lower(), new_pw)
                st.success("✅ Password updated successfully.")

    elif menu == "Reset Password":
        password_reset_flow()

if __name__ == "__main__":
    main()
