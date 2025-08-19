



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




# @st.dialog("🔐 Sign In", width='small')
# def show_login_dialog():
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
#         .stTextInput > div > div > input {
#             margin-top: -5px !important;
#         }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

#     with st.form("login_form"):
#         st.markdown('<span class="tight-label">Username</span>', unsafe_allow_html=True)
#         username_input = st.text_input("", key="login_username")
#         st.markdown('<span class="tight-label">Password</span>', unsafe_allow_html=True)
#         password_input = st.text_input("", type="password", key="login_password")
#         submitted = st.form_submit_button(":green[Login]")

#         if submitted:
#             try:
#                 success, username, role = authenticate_user(username_input, password_input)
#             except Exception as e:
#                 st.error(f"❌ Login failed due to error: {e}")
#                 return

#             if success:
#                 st.session_state.logged_in = True
#                 st.session_state.user_name = username
#                 st.session_state.user_role = role
#                 st.session_state.show_login = False

#                 # Fetch full user info
#                 try:
#                     with create_connection() as conn:
#                         row = conn.execute(
#                             "SELECT * FROM users WHERE username = ?", (username,)
#                         ).fetchone()
#                         if row:
#                             col_names = [col[1] for col in conn.execute("PRAGMA table_info(users)")]
#                             user = dict(zip(col_names, row))
#                         else:
#                             user = {}
#                 except Exception as e:
#                     user = {}
#                     st.warning(f"⚠️ Could not fetch full user info: {e}")

#                 # Pushbullet notification safely
#                 if "notified" not in st.session_state or not st.session_state.notified:
#                     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                     try:
#                         pb.push_note(
#                             "🔔 Login Alert",
#                             f"User: {user.get('full_name', '')} ({user.get('username', '')})\n"
#                             f"Role: {user.get('role', '')}\n"
#                             f"Email: {user.get('email', 'N/A')}\n"
#                             f"Tel: {user.get('contact', 'N/A')}\n"
#                             f"Date: {now.split()[0]}\n"
#                             f"Time: {now.split()[1]}"
#                         )
#                     except Exception as e:
#                         st.warning(f"⚠️ Pushbullet notification failed: {e}")
#                     st.session_state.notified = True

#                 st.success(f"🎉 Welcome {username}!")
#                 st.rerun()
#             else:
#                 st.error("❌ Invalid username or password.")

#     # Link to signup outside form
#     col1, col2 = st.columns([3, 2])
#     with col1:
#         st.markdown(":orange[Don't have an account yet?]")
#     with col2:
#         if st.button(":green[👉 Click to create yours here]", key="to_signup"):
#             st.session_state.show_login = False
#             st.session_state.show_signup = True
#             st.rerun()



# @st.dialog("📝 Register here", width="small")
# def show_signup_dialog():
#     import time
#     from datetime import datetime

#     # --- CSS for tight labels ---
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

#     # --- Role selection outside the form ---
#     st.markdown('<span class="tight-label">Select Role</span>', unsafe_allow_html=True)
#     role = st.selectbox("", ["Select role ..", "Student", "Parent", "Teacher", "Therapist", "Admin", "Admin2"])

#     if role != "Select role ..":
#         # --- Form for account info and role-specific fields ---
#         with st.form("signup_form"):
#             # Initialize fields
#             first_name = last_name = full_name = username = email = password = confirm_password = None
#             sex = age = class_ = stream = parent_guardian = profession = address = contact = None

#             # --- Role-dependent fields ---
#             if role == "Student":
#                 st.markdown('<span class="tight-label">First Name</span>', unsafe_allow_html=True)
#                 first_name = st.text_input("", key="first_name")
#                 st.markdown('<span class="tight-label">Last Name</span>', unsafe_allow_html=True)
#                 last_name = st.text_input("", key="last_name")
#                 full_name = f"{first_name.strip()} {last_name.strip()}" if first_name and last_name else ""

#                 st.markdown('<span class="tight-label">Sex</span>', unsafe_allow_html=True)
#                 sex = st.selectbox("", ["Male", "Female", "Other"])
#                 st.markdown('<span class="tight-label">Age</span>', unsafe_allow_html=True)
#                 age = st.number_input("", 3, 100, step=1)
#                 st.markdown('<span class="tight-label">Class</span>', unsafe_allow_html=True)
#                 class_ = st.text_input("", key="class_")
#                 st.markdown('<span class="tight-label">Stream</span>', unsafe_allow_html=True)
#                 stream = st.text_input("", key="stream")
#                 st.markdown('<span class="tight-label">Parent/Guardian</span>', unsafe_allow_html=True)
#                 parent_guardian = st.text_input("", key="parent_guardian")
#                 st.markdown('<span class="tight-label">Address</span>', unsafe_allow_html=True)
#                 address = st.text_area("", key="address")
#                 st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
#                 contact = st.text_input("", key="contact")

#             elif role in ["Parent", "Teacher"]:
#                 st.markdown('<span class="tight-label">Full Name</span>', unsafe_allow_html=True)
#                 full_name = st.text_input("", key="full_name")
#                 st.markdown('<span class="tight-label">Address</span>', unsafe_allow_html=True)
#                 address = st.text_area("", key="address")
#                 st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
#                 contact = st.text_input("", key="contact")

#             elif role == "Therapist":
#                 st.markdown('<span class="tight-label">Full Name</span>', unsafe_allow_html=True)
#                 full_name = st.text_input("", key="full_name")
#                 st.markdown('<span class="tight-label">Profession</span>', unsafe_allow_html=True)
#                 profession = st.text_input("", key="profession")
#                 st.markdown('<span class="tight-label">Phone</span>', unsafe_allow_html=True)
#                 contact = st.text_input("", key="contact")

#             elif role in ["Admin", "Admin2"]:
#                 st.markdown('<span class="tight-label">Full Name</span>', unsafe_allow_html=True)
#                 full_name = st.text_input("", key="full_name")

#             # --- Common account info ---
#             st.markdown('<span class="tight-label">Username</span>', unsafe_allow_html=True)
#             username = st.text_input("", key="username")
#             st.markdown('<span class="tight-label">Email</span>', unsafe_allow_html=True)
#             email = st.text_input("", key="email")
#             st.markdown('<span class="tight-label">Password</span>', unsafe_allow_html=True)
#             password = st.text_input("", type="password", key="password")
#             st.markdown('<span class="tight-label">Confirm Password</span>', unsafe_allow_html=True)
#             confirm_password = st.text_input("", type="password", key="confirm_password")

      

#             submitted = st.form_submit_button(":green[Create Account]")
#             if submitted:
#                 missing = []
#                 base_fields = [(username, "Username"), (email, "Email"),
#                                (password, "Password"), (confirm_password, "Confirm Password")]
#                 if role == "Student":
#                     base_fields += [(first_name, "First Name"), (last_name, "Last Name")]
#                 else:
#                     base_fields += [(full_name, "Full Name")]
#                 missing += [label for val, label in base_fields if not val]

#                 # Role-specific checks
#                 if role == "Student":
#                     for fld, lbl in [(sex, "Sex"), (age, "Age"), (class_, "Class"),
#                                      (stream, "Stream"), (parent_guardian, "Parent/Guardian"),
#                                      (address, "Address"), (contact, "Phone")]:
#                         if not fld: missing.append(lbl)
#                 elif role in ["Parent", "Teacher"]:
#                     for fld, lbl in [(address, "Address"), (contact, "Phone")]:
#                         if not fld: missing.append(lbl)
#                 elif role == "Therapist":
#                     for fld, lbl in [(profession, "Profession"), (contact, "Phone")]:
#                         if not fld: missing.append(lbl)

#                 if missing:
#                     st.warning(f"⚠️ Please fill in: **{', '.join(missing)}**")
#                 elif password != confirm_password:
#                     st.warning("⚠️ Passwords do not match.")
#                 else:
#                     # ✅ Generate user_id and hash password
#                     user_id = generate_user_id(role)
#                     password_hash = hash_password(password)

#                     # Prepare data dict for insert
#                     data = {
#                         "user_id": user_id,
#                         "username": username,
#                         "password_hash": password_hash,
#                         "role": role,
#                         "email": email,
#                         "first_name": first_name,
#                         "last_name": last_name,
#                         "full_name": full_name,
#                         "sex": sex,
#                         "age": age,
#                         "class": class_,
#                         "stream": stream,
#                         "address": address,
#                         "parent_guardian": parent_guardian,
#                         "contact": contact,
#                         "profession": profession
#                     }

#                     success, msg = insert_user(data)
#                     if success:
#                         st.success(msg)
#                         with st.spinner("Redirecting to login..."):
#                             time.sleep(2)
#                         st.session_state.show_signup = False
#                         st.session_state.show_login = True
#                         st.rerun()
#                     else:
#                         st.error(msg)
#   # --- Login link outside form ---
#     col1, col2 = st.columns([3, 2])
#     with col1:
#         st.markdown(":orange[Already have an account?]")
#     with col2:
#         if st.button(":blue[👉 Go to Login]", key="to_login"):
#             st.session_state.show_signup = False
#             st.session_state.show_login = True
#             st.rerun()
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
            font-style: Times New Roman;
        }
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
            try:
                success, username, role = authenticate_user(username_input, password_input)
            except Exception as e:
                st.error(f"❌ Login failed due to error: {e}")
                return

            if success:
                st.session_state.logged_in = True
                st.session_state.user_name = username
                st.session_state.user_role = role
                st.session_state.show_login = False

                # Fetch full user info
                try:
                    with create_connection() as conn:
                        row = conn.execute(
                            "SELECT * FROM users WHERE username = ?", (username,)
                        ).fetchone()
                        if row:
                            col_names = [col[1] for col in conn.execute("PRAGMA table_info(users)")]
                            user = dict(zip(col_names, row))
                        else:
                            user = {}
                except Exception as e:
                    user = {}
                    st.warning(f"⚠️ Could not fetch full user info: {e}")

                # Pushbullet notification safely
                if "notified" not in st.session_state or not st.session_state.notified:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        pb.push_note(
                            "🔔 Login Alert",
                            f"User: {user.get('full_name', '')} ({user.get('username', '')})\n"
                            f"Role: {user.get('role', '')}\n"
                            f"Email: {user.get('email', 'N/A')}\n"
                            f"Tel: {user.get('contact', 'N/A')}\n"
                            f"Date: {now.split()[0]}\n"
                            f"Time: {now.split()[1]}"
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Pushbullet notification failed: {e}")
                    st.session_state.notified = True

                st.success(f"🎉 Welcome {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    # Link to signup outside form
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(":orange[Don't have an account yet?]")
    with col2:
        if st.button(":green[👉 Click to create yours here]", key="to_signup"):
            st.session_state.show_login = False
            st.session_state.show_signup = True
            st.rerun()


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
        with st.form("signup_form"):
            # Init
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

                # --- load previous Class/Stream options ---
                with create_connection() as conn:
                    conn.execute("CREATE TABLE IF NOT EXISTS class_options (name TEXT UNIQUE)")
                    conn.execute("CREATE TABLE IF NOT EXISTS stream_options (name TEXT UNIQUE)")
                    class_list = [r[0] for r in conn.execute("SELECT name FROM class_options").fetchall()]
                    stream_list = [r[0] for r in conn.execute("SELECT name FROM stream_options").fetchall()]

                default_classes = ["S.1", "S.2", "S.3", "S.4", "S.5", "S.6"]
                default_streams = ["EAST", "WEST", "NORTH", "SOUTH"]
                class_list = default_classes + [c for c in class_list if c not in default_classes]
                stream_list = default_streams + [s for s in stream_list if s not in default_streams]

                # Class
                st.markdown('<span class="tight-label">Class</span>', unsafe_allow_html=True)
                class_choice = st.selectbox("", class_list + ["Other"], key="class_select")
                if class_choice == "Other":
                    class_ = st.text_input("Enter class", key="custom_class")
                else:
                    class_ = class_choice

                # Stream
                st.markdown('<span class="tight-label">Stream</span>', unsafe_allow_html=True)
                stream_choice = st.selectbox("", stream_list + ["Other"], key="stream_select")
                if stream_choice == "Other":
                    stream = st.text_input("Enter stream", key="custom_stream")
                else:
                    stream = stream_choice

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

            # --- Common fields ---
            st.markdown('<span class="tight-label">Username</span>', unsafe_allow_html=True)
            username = st.text_input("", key="username")
            st.markdown('<span class="tight-label">Email</span>', unsafe_allow_html=True)
            email = st.text_input("", key="email")
            st.markdown('<span class="tight-label">Password</span>', unsafe_allow_html=True)
            password = st.text_input("", type="password", key="password")
            st.markdown('<span class="tight-label">Confirm Password</span>', unsafe_allow_html=True)
            confirm_password = st.text_input("", type="password", key="confirm_password")

            submitted = st.form_submit_button(":green[Create Account]")
            if submitted:
                missing = []
                base_fields = [(username, "Username"), (email, "Email"),
                               (password, "Password"), (confirm_password, "Confirm Password")]
                if role == "Student":
                    base_fields += [(first_name, "First Name"), (last_name, "Last Name")]
                else:
                    base_fields += [(full_name, "Full Name")]
                missing += [lbl for val, lbl in base_fields if not val]

                # Role-specific checks
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
                    # ✅ Save user
                    user_id = generate_user_id(role)
                    password_hash = hash_password(password)
                    data = {
                        "user_id": user_id, "username": username, "password_hash": password_hash,
                        "role": role, "email": email, "first_name": first_name, "last_name": last_name,
                        "full_name": full_name, "sex": sex, "age": age, "class": class_,
                        "stream": stream, "address": address, "parent_guardian": parent_guardian,
                        "contact": contact, "profession": profession
                    }

                    success, msg = insert_user(data)
                    if success:
                        # ✅ Save new Class/Stream if custom
                        try:
                            with create_connection() as conn:
                                if class_ and class_ not in default_classes:
                                    conn.execute("INSERT OR IGNORE INTO class_options (name) VALUES (?)", (class_,))
                                if stream and stream not in default_streams:
                                    conn.execute("INSERT OR IGNORE INTO stream_options (name) VALUES (?)", (stream,))
                                conn.commit()
                        except Exception as e:
                            st.warning(f"⚠️ Could not save custom class/stream: {e}")

                        st.success(msg)
                        with st.spinner("Redirecting to login..."):
                            time.sleep(2)
                        st.session_state.show_signup = False
                        st.session_state.show_login = True
                        st.rerun()
                    else:
                        st.error(msg)

    # --- Login link outside form ---
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(":orange[Already have an account?]")
    with col2:
        if st.button(":blue[👉 Go to Login]", key="to_login"):
            st.session_state.show_signup = False
            st.session_state.show_login = True
            st.rerun()
