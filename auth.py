import streamlit as st
import sqlite3
import bcrypt
import time
from pushbullet import Pushbullet
from datetime import datetime

DB_PATH = "users_db.db"
API_KEY = st.secrets["push_API_KEY"]

@st.cache_resource(show_spinner=False)
def get_pushbullet():
    return Pushbullet(API_KEY)

pb = get_pushbullet()

# --- DB Utilities ---
def create_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_users_db():
    with create_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT CHECK(role IN ('Student', 'Parent', 'Teacher', 'Therapist', 'Admin', 'Admin2')) NOT NULL,
            email TEXT,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            sex TEXT,
            age INTEGER,
            class TEXT,
            stream TEXT,
            address TEXT,
            parent_guardian TEXT,
            contact TEXT,
            profession TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
        """)


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

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_sessions_table():
    with create_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            name TEXT,
            event_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_duration INTEGER
        )
        """)
create_sessions_table()


def insert_session_event(user_id, role, name, event_type, session_duration=None):
    with create_connection() as conn:
        conn.execute("""
            INSERT INTO sessions (user_id, role, name, event_type, timestamp, session_duration)
            VALUES (?, ?, ?,?, CURRENT_TIMESTAMP, ?)
        """, (user_id, role, name, event_type, session_duration))




# --- DB Actions ---
def insert_user(data):
    try:
        with create_connection() as conn:
            conn.execute("""
                INSERT INTO users (
                    user_id, username, password_hash, role, email,
                    first_name, last_name, full_name, sex, age, class, stream,
                    address, parent_guardian, contact, profession
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['user_id'], data['username'], data['password_hash'], data['role'], data.get('email'),
                data.get('first_name'), data.get('last_name'), data.get('full_name'), data.get('sex'),
                data.get('age'), data.get('class'), data.get('stream'), data.get('address'),
                data.get('parent_guardian'), data.get('contact'), data.get('profession')
            ))
        return True, "✅ User registered successfully!"
    except sqlite3.IntegrityError as e:
        return False, f"🚫 {str(e)}"

def authenticate_user(username, password):
    conn = create_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        if user["is_active"] == 0:
            return False, username, None
        return True, user["username"], user["role"]
    return False, username, None

# # --- LOGIN DIALOG ---
# @st.dialog("🔐 Sign In", width='small')
# def show_login_dialog():
#     with st.form("login_form"):
#         username = st.text_input("Username", key="login_usernme")
#         password = st.text_input("Password", type="password", key="login_password")
#         submitted = st.form_submit_button(":green[Login]")
#         if submitted:
#             success, username, role = authenticate_user(username, password)
#             if success:
#                 st.session_state.logged_in = True
#                 st.session_state.user_name = username
#                 st.session_state.user_role = role
#                 st.session_state.show_login = False

#                 with create_connection() as conn:
#                     row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
#                     col_names = [desc[0] for desc in conn.execute("PRAGMA table_info(users)")]
#                 user = dict(zip(col_names, row)) if row else {}

#                 if "notified" not in st.session_state or not st.session_state.notified:
#                     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                     pb.push_note(
#                         "🔔 Login Alert",
#                         f"User: {user.get('full_name', '')} ({user.get('username')})\n"
#                         f"Role: {user.get('role')}\n"
#                         f"Email: {user.get('email', 'N/A')}\n"
#                         f"Tel: {user.get('contact', 'N/A')}\n"
#                         f"Date: {now.split()[0]}\n"
#                         f"Time: {now.split()[1]}"
#                     )
#                     st.session_state.notified = True

#                 st.success(f"🎉 Welcome {username}!")
#                 st.rerun()
#             else:
#                 st.error("❌ Invalid email or password.")

#     col1, col2 = st.columns([3, 2])
#     with col1:
#         st.markdown(":orange[Don't have an account yet?]")
#     with col2:
#         if st.button(":blue[👉 Click to create yours here]", key="to_signup"):
#             st.session_state.show_login = False
#             st.session_state.show_signup = True
#             st.rerun()
# --- LOGIN DIALOG ---
@st.dialog("🔐 Sign In", width='small')
def show_login_dialog():
    with st.form("login_form"):
        username_input = st.text_input("Username", key="login_usernme")
        password_input = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button(":green[Login]")

        if submitted:
            success, username, role = authenticate_user(username_input, password_input)
            if success:
                st.session_state.logged_in = True
                st.session_state.user_name = username
                st.session_state.user_role = role
                st.session_state.show_login = False

                # Fetch user info properly
                with create_connection() as conn:
                    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
                    if row:
                        # PRAGMA returns a tuple: (cid, name, type, notnull, dflt_value, pk)
                        col_names = [col[1] for col in conn.execute("PRAGMA table_info(users)")]
                        user = dict(zip(col_names, row))
                    else:
                        user = {}

                # Pushbullet notification
                if "notified" not in st.session_state or not st.session_state.notified:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pb.push_note(
                        "🔔 Login Alert",
                        f"User: {user.get('full_name', '')} ({user.get('username', '')})\n"
                        f"Role: {user.get('role', '')}\n"
                        f"Email: {user.get('email', 'N/A')}\n"
                        f"Tel: {user.get('contact', 'N/A')}\n"
                        f"Date: {now.split()[0]}\n"
                        f"Time: {now.split()[1]}"
                    )
                    st.session_state.notified = True

                st.success(f"🎉 Welcome {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(":orange[Don't have an account yet?]")
    with col2:
        if st.button(":blue[👉 Click to create yours here]", key="to_signup"):
            st.session_state.show_login = False
            st.session_state.show_signup = True
            st.rerun()

# --- SIGNUP DIALOG ---
@st.dialog("📝 Register here", width="small")
def show_signup_dialog():
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        role = col2.selectbox("I am a...", ["Select", "Student", "Parent", "Teacher", "Therapist", "Admin", "Admin2"])
        if role == "Student":
            first_name = col1.text_input("First Name")
            last_name = col2.text_input("Last Name")
            full_name = f"{first_name.strip()} {last_name.strip()}"
        else:
            full_name = col1.text_input("Full Name")
            first_name = last_name = None

        username = col2.text_input("Username")
        email = col1.text_input("Email")
        password = col2.text_input("Password", type="password")
        confirm_password = col1.text_input("Confirm Password", type="password")

        sex = age = class_ = stream = parent_guardian = profession = address = contact = None
        if role == "Student":
            sex = col1.selectbox("Sex", ["Male", "Female", "Other"])
            age = col2.number_input("Age", 3, 100, step=1)
            class_ = col1.text_input("Class")
            stream = col2.text_input("Stream")
            parent_guardian = col1.text_input("Parent/Guardian")
            address = col2.text_area("Address")
            contact = col1.text_input("Phone")
        elif role in ["Parent", "Teacher"]:
            address = col1.text_area("Address")
            contact = col2.text_input("Phone")
        elif role == "Therapist":
            profession = col1.text_input("Profession")
            contact = col2.text_input("Phone")

        submitted = st.form_submit_button("Create Account")
        if submitted:
            missing = []
            base_fields = [(username, "Username"), (email, "Email"),
                           (password, "Password"), (confirm_password, "Confirm Password")]
            if role == "Student":
                base_fields += [(first_name, "First Name"), (last_name, "Last Name")]
            else:
                base_fields += [(full_name, "Full Name")]
            missing += [label for val, label in base_fields if not val]
            if role == "Select": missing.append("Role")
            if role == "Student":
                if not sex: missing.append("Sex")
                if not age: missing.append("Age")
                if not class_: missing.append("Class")
                if not stream: missing.append("Stream")
                if not parent_guardian: missing.append("Parent/Guardian")
                if not address: missing.append("Address")
                if not contact: missing.append("Phone")
            elif role in ["Parent", "Teacher"]:
                if not address: missing.append("Address")
                if not contact: missing.append("Phone")
            elif role == "Therapist":
                if not profession: missing.append("Profession")
                if not contact: missing.append("Phone")

            if missing:
                st.warning(f"⚠️ Please fill in: **{', '.join(missing)}**")
            elif password != confirm_password:
                st.warning("⚠️ Passwords do not match.")
            else:
                user_data = {
                    "user_id": generate_user_id(role),
                    "username": username.strip(),
                    "password_hash": hash_password(password),
                    "role": role,
                    "email": email.strip(),
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": full_name.strip(),
                    "sex": sex,
                    "age": int(age) if age else None,
                    "class": class_,
                    "stream": stream,
                    "address": address,
                    "parent_guardian": parent_guardian,
                    "contact": contact,
                    "profession": profession
                }
                ok, msg = insert_user(user_data)
                if ok:
                    st.success(msg)
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pb.push_note(
                        "📥 New User Registration",
                        f"👤 {user_data['full_name']} ({username})\n"
                        f"📧 {email}\n"
                        f"📱 {contact or 'N/A'}\n"
                        f"🧾 Role: {role}\n"
                        f"🕒 Date: {now.split()[0]}\n"
                        f"🕒 Time: {now.split()[1]}"
                    )
                    with st.spinner("Redirecting to login..."):
                        time.sleep(2)
                    st.session_state.show_signup = False
                    st.session_state.show_login = True
                    st.rerun()
                else:
                    st.error(msg)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(":blue[Already have an account?]")
    with col2:
        if st.button(":orange[👉 Go to Login]", key="to_login"):
            st.session_state.show_signup = False
            st.session_state.show_login = True
            st.rerun()
