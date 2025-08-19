# import streamlit as st
# import sqlite3
# import bcrypt
# import time
# from pushbullet import Pushbullet
# from datetime import datetime

# DB_PATH = "users_db.db"
# API_KEY = st.secrets["push_API_KEY"]

# @st.cache_resource(show_spinner=False)
# def get_pushbullet():
#     return Pushbullet(API_KEY)

# pb = get_pushbullet()

# # --- DB Utilities ---
# def create_connection():
#     return sqlite3.connect(DB_PATH, check_same_thread=False)

# def create_users_db():
#     with create_connection() as conn:
#         conn.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             user_id TEXT PRIMARY KEY,
#             username TEXT UNIQUE NOT NULL,
#             password_hash TEXT NOT NULL,
#             role TEXT CHECK(role IN ('Student', 'Parent', 'Teacher', 'Therapist', 'Admin', 'Admin2')) NOT NULL,
#             email TEXT,
#             first_name TEXT,
#             last_name TEXT,
#             full_name TEXT,
#             sex TEXT,
#             age INTEGER,
#             class TEXT,
#             stream TEXT,
#             address TEXT,
#             parent_guardian TEXT,
#             contact TEXT,
#             profession TEXT,
#             registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             is_active INTEGER DEFAULT 1
#         )
#         """)


# def generate_user_id(role):
#     prefix_map = {
#         'student': 'STUD',
#         'parent': 'PARENT',
#         'teacher': 'TEACH',
#         'therapist': 'USER',
#         'admin': 'ADMIN'
#     }
#     prefix = prefix_map.get(role.lower(), 'GUEST')  # now works as expected
#     today = datetime.now().strftime("%Y%m%d")
#     like_pattern = f"{prefix}-{today}-%"

#     with sqlite3.connect(DB_PATH) as conn:
#         row = conn.execute("""
#             SELECT user_id FROM users WHERE user_id LIKE ?
#             ORDER BY user_id DESC LIMIT 1
#         """, (like_pattern,)).fetchone()
    
#     next_num = int(row[0].split("-")[-1]) + 1 if row else 1
#     return f"{prefix}-{today}-{next_num:04d}"

# def hash_password(password):
#     return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# def verify_password(password, hashed):
#     return bcrypt.checkpw(password.encode(), hashed.encode())


# def create_sessions_table():
#     with create_connection() as conn:
#         conn.execute("""
#         CREATE TABLE IF NOT EXISTS sessions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id TEXT,
#             role TEXT,
#             name TEXT,
#             event_type TEXT,
#             timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             session_duration INTEGER
#         )
#         """)
# create_sessions_table()


# def insert_session_event(user_id, role, name, event_type, session_duration=None):
#     with create_connection() as conn:
#         conn.execute("""
#             INSERT INTO sessions (user_id, role, name, event_type, timestamp, session_duration)
#             VALUES (?, ?, ?,?, CURRENT_TIMESTAMP, ?)
#         """, (user_id, role, name, event_type, session_duration))




# # --- DB Actions ---
# def insert_user(data):
#     try:
#         with create_connection() as conn:
#             conn.execute("""
#                 INSERT INTO users (
#                     user_id, username, password_hash, role, email,
#                     first_name, last_name, full_name, sex, age, class, stream,
#                     address, parent_guardian, contact, profession
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """, (
#                 data['user_id'], data['username'], data['password_hash'], data['role'], data.get('email'),
#                 data.get('first_name'), data.get('last_name'), data.get('full_name'), data.get('sex'),
#                 data.get('age'), data.get('class'), data.get('stream'), data.get('address'),
#                 data.get('parent_guardian'), data.get('contact'), data.get('profession')
#             ))
#         return True, "✅ User registered successfully!"
#     except sqlite3.IntegrityError as e:
#         return False, f"🚫 {str(e)}"

# def authenticate_user(username, password):
#     conn = create_connection()
#     conn.row_factory = sqlite3.Row
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
#     user = cursor.fetchone()
#     conn.close()

#     if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
#         if user["is_active"] == 0:
#             return False, username, None
#         return True, user["username"], user["role"]
#     return False, username, None

# @st.dialog("🔐 Sign In", width='small')
# def show_login_dialog():
#     with st.form("login_form"):
#         username_input = st.text_input("Username", key="login_usernme")
#         password_input = st.text_input("Password", type="password", key="login_password")
#         submitted = st.form_submit_button(":green[Login]")

#         if submitted:
#             success, username, role = authenticate_user(username_input, password_input)
#             if success:
#                 st.session_state.logged_in = True
#                 st.session_state.user_name = username
#                 st.session_state.user_role = role
#                 st.session_state.show_login = False

#                 # Fetch user info properly
#                 with create_connection() as conn:
#                     row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
#                     if row:
#                         # PRAGMA returns a tuple: (cid, name, type, notnull, dflt_value, pk)
#                         col_names = [col[1] for col in conn.execute("PRAGMA table_info(users)")]
#                         user = dict(zip(col_names, row))
#                     else:
#                         user = {}

#                 # Pushbullet notification
#                 if "notified" not in st.session_state or not st.session_state.notified:
#                     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                     pb.push_note(
#                         "🔔 Login Alert",
#                         f"User: {user.get('full_name', '')} ({user.get('username', '')})\n"
#                         f"Role: {user.get('role', '')}\n"
#                         f"Email: {user.get('email', 'N/A')}\n"
#                         f"Tel: {user.get('contact', 'N/A')}\n"
#                         f"Date: {now.split()[0]}\n"
#                         f"Time: {now.split()[1]}"
#                     )
#                     st.session_state.notified = True

#                 st.success(f"🎉 Welcome {username}!")
#                 st.rerun()
#             else:
#                 st.error("❌ Invalid username or password.")

#     col1, col2 = st.columns([3, 2])
#     with col1:
#         st.markdown(":orange[Don't have an account yet?]")
#     with col2:
#         if st.button(":blue[👉 Click to create yours here]", key="to_signup"):
#             st.session_state.show_login = False
#             st.session_state.show_signup = True
#             st.rerun()

# # --- SIGNUP DIALOG ---
# @st.dialog("📝 Register here", width="small")
# def show_signup_dialog():
#     with st.form("signup_form"):
#         col1, col2 = st.columns(2)
#         role = col2.selectbox("I am a...", ["Select", "Student", "Parent", "Teacher", "Therapist", "Admin", "Admin2"])
#         if role == "Student":
#             first_name = col1.text_input("First Name")
#             last_name = col2.text_input("Last Name")
#             full_name = f"{first_name.strip()} {last_name.strip()}"
#         else:
#             full_name = col1.text_input("Full Name")
#             first_name = last_name = None

#         username = col2.text_input("Username")
#         email = col1.text_input("Email")
#         password = col2.text_input("Password", type="password")
#         confirm_password = col1.text_input("Confirm Password", type="password")

#         sex = age = class_ = stream = parent_guardian = profession = address = contact = None
#         if role == "Student":
#             sex = col1.selectbox("Sex", ["Male", "Female", "Other"])
#             age = col2.number_input("Age", 3, 100, step=1)
#             class_ = col1.text_input("Class")
#             stream = col2.text_input("Stream")
#             parent_guardian = col1.text_input("Parent/Guardian")
#             address = col2.text_area("Address")
#             contact = col1.text_input("Phone")
#         elif role in ["Parent", "Teacher"]:
#             address = col1.text_area("Address")
#             contact = col2.text_input("Phone")
#         elif role == "Therapist":
#             profession = col1.text_input("Profession")
#             contact = col2.text_input("Phone")

#         submitted = st.form_submit_button("Create Account")
#         if submitted:
#             missing = []
#             base_fields = [(username, "Username"), (email, "Email"),
#                            (password, "Password"), (confirm_password, "Confirm Password")]
#             if role == "Student":
#                 base_fields += [(first_name, "First Name"), (last_name, "Last Name")]
#             else:
#                 base_fields += [(full_name, "Full Name")]
#             missing += [label for val, label in base_fields if not val]
#             if role == "Select": missing.append("Role")
#             if role == "Student":
#                 if not sex: missing.append("Sex")
#                 if not age: missing.append("Age")
#                 if not class_: missing.append("Class")
#                 if not stream: missing.append("Stream")
#                 if not parent_guardian: missing.append("Parent/Guardian")
#                 if not address: missing.append("Address")
#                 if not contact: missing.append("Phone")
#             elif role in ["Parent", "Teacher"]:
#                 if not address: missing.append("Address")
#                 if not contact: missing.append("Phone")
#             elif role == "Therapist":
#                 if not profession: missing.append("Profession")
#                 if not contact: missing.append("Phone")

#             if missing:
#                 st.warning(f"⚠️ Please fill in: **{', '.join(missing)}**")
#             elif password != confirm_password:
#                 st.warning("⚠️ Passwords do not match.")
#             else:
#                 user_data = {
#                     "user_id": generate_user_id(role),
#                     "username": username.strip(),
#                     "password_hash": hash_password(password),
#                     "role": role,
#                     "email": email.strip(),
#                     "first_name": first_name,
#                     "last_name": last_name,
#                     "full_name": full_name.strip(),
#                     "sex": sex,
#                     "age": int(age) if age else None,
#                     "class": class_,
#                     "stream": stream,
#                     "address": address,
#                     "parent_guardian": parent_guardian,
#                     "contact": contact,
#                     "profession": profession
#                 }
#                 ok, msg = insert_user(user_data)
#                 if ok:
#                     st.success(msg)
#                     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                     pb.push_note(
#                         "📥 New User Registration",
#                         f"👤 {user_data['full_name']} ({username})\n"
#                         f"📧 {email}\n"
#                         f"📱 {contact or 'N/A'}\n"
#                         f"🧾 Role: {role}\n"
#                         f"🕒 Date: {now.split()[0]}\n"
#                         f"🕒 Time: {now.split()[1]}"
#                     )
#                     with st.spinner("Redirecting to login..."):
#                         time.sleep(2)
#                     st.session_state.show_signup = False
#                     st.session_state.show_login = True
#                     st.rerun()
#                 else:
#                     st.error(msg)

#     col1, col2 = st.columns([3, 2])
#     with col1:
#         st.markdown(":blue[Already have an account?]")
#     with col2:
#         if st.button(":orange[👉 Go to Login]", key="to_login"):
#             st.session_state.show_signup = False
#             st.session_state.show_login = True
#             st.rerun()





import streamlit as st
import sqlite3
import hashlib
import time
from pushbullet import Pushbullet
from datetime import datetime
from pathlib import Path

DB_PATH = Path("users_db.db")
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

dark_css = """
<style>
/* ---------- DARK THEME ---------- */
.stApp.dark {
    background-color: #121212 !important;
    color: #FFFFFF !important;
}

/* Force input labels to show in both themes */
.stApp.dark [data-testid="stMarkdownContainer"],
.stApp.dark .stTextInput label,
.stApp.dark .stPasswordInput label,
.stApp.dark .stSelectbox label,
.stApp.dark legend {
    color: #FFFFFF;
}

.stApp:not(.dark) [data-testid="stMarkdownContainer"],
.stApp:not(.dark) .stTextInput label,
.stApp:not(.dark) .stPasswordInput label,
.stApp:not(.dark) .stSelectbox label,
.stApp:not(.dark) legend {
    color: #000000 !important;
}

/* Inputs, buttons (dark theme only) */
.stApp.dark input,
.stApp.dark textarea,
.stApp.dark select,
.stApp.dark button,
.stApp.dark .stButton button {
    background-color: #333333 !important;
    color: #FFFFFF !important;
    border-color: #555555 !important;
}

/* Tables */
.stApp.dark .stDataFrame,
.stApp.dark .stDataFrame td,
.stApp.dark .stDataFrame th {
    background-color: #1E1E1E !important;
    color: #FFFFFF !important;
}

/* Preserve custom cards/backgrounds */
.custom-card, .custom-background {
    background-color: unset !important;
    color: unset !important;
}

/* Scrollbars (dark only) */
.stApp.dark ::-webkit-scrollbar {
    width: 10px;
}
.stApp.dark ::-webkit-scrollbar-track {
    background: #1E1E1E;
}
.stApp.dark ::-webkit-scrollbar-thumb {
    background-color: #555555;
    border-radius: 10px;
}
</style>
"""


def generate_user_id(role):
    prefix_map = {
        'student': 'STUD',
        'parent': 'PARENT',
        'teacher': 'TEACH',
        'therapist': 'USER',
        'admin': 'ADMIN'
    }
    prefix = prefix_map.get(role.lower(), 'GUEST')
    today = datetime.now().strftime("%Y%m%d")
    like_pattern = f"{prefix}-{today}-%"

    with create_connection() as conn:
        row = conn.execute("""
            SELECT user_id FROM users WHERE user_id LIKE ?
            ORDER BY user_id DESC LIMIT 1
        """, (like_pattern,)).fetchone()
    
    next_num = int(row[0].split("-")[-1]) + 1 if row else 1
    return f"{prefix}-{today}-{next_num:04d}"

# --- Password Utilities ---
def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a SHA-256 hashed password"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed

# --- Sessions Table ---
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
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
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

    if user and verify_password(password, user["password_hash"]):
        if user["is_active"] == 0:
            return False, username, None
        return True, user["username"], user["role"]
    return False, username, None


@st.dialog("🔐 Sign In", width='small')
def show_login_dialog():
    st.markdown(
        """
        <style>
        .tight-label {
            color: #1E90FF;
            font-weight: 250;
            padding: 0px;
            margin: 0px;
            line-height: 0.5;
            display: block;
            font-style: Times New Romans;
        }
        /* Pulls input closer to its label */
        .stTextInput > div > div > input {
            margin-top: -5px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.form("login_form"):
        st.markdown('<span class="tight-label">Username</span>', unsafe_allow_html=True)
        username_input = st.text_input("", key="login_username")
        st.markdown('<span class="tight-label">Password</span>', unsafe_allow_html=True)
        password_input = st.text_input("", type="password", key="login_password")
        submitted = st.form_submit_button(":green[Login]")
        if submitted:
            success, username, role = authenticate_user(username_input, password_input)
            if success:
                st.session_state.logged_in = True
                st.session_state.user_name = username
                st.session_state.user_role = role
                st.session_state.show_login = False
                with create_connection() as conn:
                    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
                    if row:
                        col_names = [col[1] for col in conn.execute("PRAGMA table_info(users)")]
                        user = dict(zip(col_names, row))
                    else:
                        user = {}

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
        if st.button(":green[👉 Click to create yours here]", key="to_signup"):
            st.session_state.show_login = False
            st.session_state.show_signup = True
            st.rerun()




# @st.dialog("📝 Register here", width="small")
# def show_signup_dialog():
#     import time
#     from datetime import datetime
#     st.markdown(
#         """
#         <style>
#         .tight-label {
#             color: #1E90FF;
#             font-weight: 250;
#             padding: 0px;
#             margin: 0px;
#             line-height: 0.5;
#             display: block;
#             font-style: Times New Roman;
#         }
#         /* Pull inputs closer to labels */
#         .stTextInput > div > div > input,
#         .stNumberInput > div > div > input,
#         .stTextArea > div > div > textarea,
#         .stSelectbox > div > div > div {
#             margin-top: -5px !important;
#         }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

#     # --- Form ---
#     with st.form("signup_form"):
#         # Role selection
#         st.markdown('<span class="tight-label">Select Role</span>', unsafe_allow_html=True)
#         role = st.selectbox("", ["Select role ..", "Student", "Parent", "Teacher", "Therapist", "Admin", "Admin2"])
#         if role == "Student":
#             st.markdown('<span class="tight-label">First Name</span>', unsafe_allow_html=True)
#             first_name = st.text_input("", key="first_name")
#             st.markdown('<span class="tight-label">Last Name</span>', unsafe_allow_html=True)
#             last_name = st.text_input("", key="last_name")
#             full_name = f"{first_name.strip()} {last_name.strip()}"
#         else:
#             st.markdown('<span class="tight-label">Full Name</span>', unsafe_allow_html=True)
#             full_name = st.text_input("", key="full_name")
#             first_name = last_name = None

#         # Account info
#         st.markdown('<span class="tight-label">Username</span>', unsafe_allow_html=True)
#         username = st.text_input("", key="username")
#         st.markdown('<span class="tight-label">Email</span>', unsafe_allow_html=True)
#         email = st.text_input("", key="email")
#         st.markdown('<span class="tight-label">Password</span>', unsafe_allow_html=True)
#         password = st.text_input("", type="password", key="password")
#         st.markdown('<span class="tight-label">Confirm Password</span>', unsafe_allow_html=True)
#         confirm_password = st.text_input("", type="password", key="confirm_password")

#         # Conditional fields
#         sex = age = class_ = stream = parent_guardian = profession = address = contact = None
#         if role == "Student":
#             st.markdown('<span class="tight-label">Sex</span>', unsafe_allow_html=True)
#             sex = st.selectbox("", ["Male", "Female", "Other"])
#             st.markdown('<span class="tight-label">Age</span>', unsafe_allow_html=True)
#             age = st.number_input("", 3, 100, step=1)
#             st.markdown('<span class="tight-label">Class</span>', unsafe_allow_html=True)
#             class_ = st.text_input("", key="class_")
#             st.markdown('<span class="tight-label">Stream</span>', unsafe_allow_html=True)
#             stream = st.text_input("", key="stream")
#             st.markdown('<span class="tight-label">Parent/Guardian</span>', unsafe_allow_html=True)
#             parent_guardian = st.text_input("", key="parent_guardian")
#             st.markdown('<span class="tight-label">Address</span>', unsafe_allow_html=True)
#             address = st.text_area("", key="address")
#             st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
#             contact = st.text_input("", key="contact")
#         elif role in ["Parent", "Teacher"]:
#             st.markdown('<span class="tight-label">Address</span>', unsafe_allow_html=True)
#             address = st.text_area("", key="address")
#             st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
#             contact = st.text_input("", key="contact")
#         elif role == "Therapist":
#             st.markdown('<span class="tight-label">Profession</span>', unsafe_allow_html=True)
#             profession = st.text_input("", key="profession")
#             st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
#             contact = st.text_input("", key="contact")

#         # Submit button
#         submitted = st.form_submit_button(":green[Create Account]")
#         if submitted:
#             # Validation
#             missing = []
#             base_fields = [(username, "Username"), (email, "Email"),
#                            (password, "Password"), (confirm_password, "Confirm Password")]
#             if role == "Student":
#                 base_fields += [(first_name, "First Name"), (last_name, "Last Name")]
#             else:
#                 base_fields += [(full_name, "Full Name")]
#             missing += [label for val, label in base_fields if not val]
#             if role == "Select role ..": missing.append("Role")
#             if role == "Student":
#                 if not sex: missing.append("Sex")
#                 if not age: missing.append("Age")
#                 if not class_: missing.append("Class")
#                 if not stream: missing.append("Stream")
#                 if not parent_guardian: missing.append("Parent/Guardian")
#                 if not address: missing.append("Address")
#                 if not contact: missing.append("Phone")
#             elif role in ["Parent", "Teacher"]:
#                 if not address: missing.append("Address")
#                 if not contact: missing.append("Phone")
#             elif role == "Therapist":
#                 if not profession: missing.append("Profession")
#                 if not contact: missing.append("Phone")

#             if missing:
#                 st.warning(f"⚠️ Please fill in: **{', '.join(missing)}**")
#             elif password != confirm_password:
#                 st.warning("⚠️ Passwords do not match.")
#             else:
#                 st.success("✅ Account created successfully!")
#                 with st.spinner("Redirecting to login..."):
#                     time.sleep(2)
#                 st.session_state.show_signup = False
#                 st.session_state.show_login = True
#                 st.rerun()

#     # --- Login link outside form ---
#     col1, col2 = st.columns([3, 2])
#     with col1:
#         st.markdown(":orange[Already have an account?]")
#     with col2:
#         if st.button(":blue[👉 Go to Login]", key="to_login"):
#             st.session_state.show_signup = False
#             st.session_state.show_login = True
#             st.rerun()


@st.dialog("📝 Register here", width="small")
def show_signup_dialog():
    import time
    from datetime import datetime

    # --- CSS for tight labels ---
    st.markdown(
        """
        <style>
        .tight-label {
            color: #1E90FF;
            font-weight: 250;
            padding: 0px;
            margin: 0px;
            line-height: 0.5;
            display: block;
            font-style: Times New Roman;
        }
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {
            margin-top: -5px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- Role selection outside the form ---
    st.markdown('<span class="tight-label">Select Role</span>', unsafe_allow_html=True)
    role = st.selectbox("", ["Select role ..", "Student", "Parent", "Teacher", "Therapist", "Admin", "Admin2"])

    if role != "Select role ..":
        # --- Form for account info and role-specific fields ---
        with st.form("signup_form"):
            # Initialize fields
            first_name = last_name = full_name = username = email = password = confirm_password = None
            sex = age = class_ = stream = parent_guardian = profession = address = contact = None

            # --- Role-dependent fields ---
            if role == "Student":
                st.markdown('<span class="tight-label">First Name</span>', unsafe_allow_html=True)
                first_name = st.text_input("", key="first_name")
                st.markdown('<span class="tight-label">Last Name</span>', unsafe_allow_html=True)
                last_name = st.text_input("", key="last_name")
                full_name = f"{first_name.strip()} {last_name.strip()}" if first_name and last_name else ""

                st.markdown('<span class="tight-label">Sex</span>', unsafe_allow_html=True)
                sex = st.selectbox("", ["Male", "Female", "Other"])
                st.markdown('<span class="tight-label">Age</span>', unsafe_allow_html=True)
                age = st.number_input("", 3, 100, step=1)
                st.markdown('<span class="tight-label">Class</span>', unsafe_allow_html=True)
                class_ = st.text_input("", key="class_")
                st.markdown('<span class="tight-label">Stream</span>', unsafe_allow_html=True)
                stream = st.text_input("", key="stream")
                st.markdown('<span class="tight-label">Parent/Guardian</span>', unsafe_allow_html=True)
                parent_guardian = st.text_input("", key="parent_guardian")
                st.markdown('<span class="tight-label">Address</span>', unsafe_allow_html=True)
                address = st.text_area("", key="address")
                st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
                contact = st.text_input("", key="contact")

            elif role in ["Parent", "Teacher"]:
                st.markdown('<span class="tight-label">Full Name</span>', unsafe_allow_html=True)
                full_name = st.text_input("", key="full_name")
                st.markdown('<span class="tight-label">Address</span>', unsafe_allow_html=True)
                address = st.text_area("", key="address")
                st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
                contact = st.text_input("", key="contact")

            elif role == "Therapist":
                st.markdown('<span class="tight-label">Full Name</span>', unsafe_allow_html=True)
                full_name = st.text_input("", key="full_name")
                st.markdown('<span class="tight-label">Profession</span>', unsafe_allow_html=True)
                profession = st.text_input("", key="profession")
                st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
                contact = st.text_input("", key="contact")

            elif role in ["Admin", "Admin2"]:
                st.markdown('<span class="tight-label">Full Name</span>', unsafe_allow_html=True)
                full_name = st.text_input("", key="full_name")

            # --- Common account info ---
            st.markdown('<span class="tight-label">Username</span>', unsafe_allow_html=True)
            username = st.text_input("", key="username")
            st.markdown('<span class="tight-label">Email</span>', unsafe_allow_html=True)
            email = st.text_input("", key="email")
            st.markdown('<span class="tight-label">Password</span>', unsafe_allow_html=True)
            password = st.text_input("", type="password", key="password")
            st.markdown('<span class="tight-label">Confirm Password</span>', unsafe_allow_html=True)
            confirm_password = st.text_input("", type="password", key="confirm_password")

            # --- Submit button ---
            submitted = st.form_submit_button(":green[Create Account]")
            if submitted:
                missing = []
                base_fields = [(username, "Username"), (email, "Email"),
                               (password, "Password"), (confirm_password, "Confirm Password")]
                if role == "Student":
                    base_fields += [(first_name, "First Name"), (last_name, "Last Name")]
                else:
                    base_fields += [(full_name, "Full Name")]
                missing += [label for val, label in base_fields if not val]

                if role == "Student":
                    for fld, lbl in [(sex, "Sex"), (age, "Age"), (class_, "Class"),
                                     (stream, "Stream"), (parent_guardian, "Parent/Guardian"),
                                     (address, "Address"), (contact, "Phone")]:
                        if not fld: missing.append(lbl)
                elif role in ["Parent", "Teacher"]:
                    for fld, lbl in [(address, "Address"), (contact, "Phone")]:
                        if not fld: missing.append(lbl)
                elif role == "Therapist":
                    for fld, lbl in [(profession, "Profession"), (contact, "Phone")]:
                        if not fld: missing.append(lbl)

                if missing:
                    st.warning(f"⚠️ Please fill in: **{', '.join(missing)}**")
                elif password != confirm_password:
                    st.warning("⚠️ Passwords do not match.")
                else:
                    st.success("✅ Account created successfully!")
                    with st.spinner("Redirecting to login..."):
                        time.sleep(2)
                    st.session_state.show_signup = False
                    st.session_state.show_login = True
                    st.rerun()

    # --- Login link outside form ---
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(":orange[Already have an account?]")
    with col2:
        if st.button(":blue[👉 Go to Login]", key="to_login"):
            st.session_state.show_signup = False
            st.session_state.show_login = True
            st.rerun()

