import streamlit as st
from streamlit_card import card
import sqlite3

import therapist
import base64
import os
from streamlit_javascript import st_javascript
import appointments

DB_PATH = "users_db.db"
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_user_record(username):
    db = create_connection()
    if not db:
        return None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        record = cursor.fetchone()
        return dict(record) if record else None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        db.close()


def fetch_user_details_by_username(username):
    db = create_connection()
    if not db:
        return {}
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        record = cursor.fetchone()
        return dict(record) if record else {}
    except sqlite3.Error as e:
        st.error(f"Error fetching user details: {e}")
        return {}
    finally:
        cursor.close()
        db.close()


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def fetch_clients(db, search_input):
    cursor = db.cursor()
    search_input = search_input.strip()
    if search_input.upper().startswith(["Stud-", 'Parent-','Teach-', 'ID-']) or search_input.isdigit():
        query = """
        SELECT *
        FROM clients
        WHERE client_id = ?
        """
        cursor.execute(query, (search_input,))
    else:
        name_parts = search_input.split()
        if len(name_parts) == 2:
            query = """
            SELECT *
            FROM clients
            WHERE client_name LIKE ? OR client_name LIKE ?
            """
            cursor.execute(query, (f"%{name_parts[0]} {name_parts[1]}%", f"%{name_parts[1]} {name_parts[0]}%"))
        else:
            query = """
            SELECT *
            FROM clients
            WHERE name LIKE ?
            """
            cursor.execute(query, (f"%{search_input}%",))
    return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]



def create_user_sessions_table():
    db = create_connection()
    if not db:
        return
    try:
        cursor = db.cursor()
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
        db.commit()
    except sqlite3.Error as e:
        print(f"Error creating user_sessions table: {e}")
    finally:
        cursor.close()
        db.close()


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

CARD_COLORS = [
    "linear-gradient(135deg, #1abc9c, #16a085)",
    "linear-gradient(135deg, #3498db, #2980b9)",
    "linear-gradient(135deg, #9b59b6, #8e44ad)",
    "linear-gradient(135deg, #e67e22, #d35400)",
    "linear-gradient(135deg, #e74c3c, #c0392b)",
    "linear-gradient(135deg, #f39c12, #f1c40f)",
    "linear-gradient(135deg, #2ecc71, #27ae60)",
    "linear-gradient(135deg, #34495e, #2c3e50)",]

def display_card_menu(page_title, options, selected_key, num_cols=3):
    device_width = st_javascript("window.innerWidth", key=f"device_width_{selected_key}")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    num_cols_app = num_cols if not is_mobile else 1
    card_height = "150px" if is_mobile else "200px"
    card_width = "100%"
    font_size_title = "50px" if is_mobile else "70px"
    font_size_text = "20px"
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
                    "title": {"font-family": "serif", "font-size": font_size_title},
                },
            ):
                st.session_state[selected_key] = option["text"]
                st.rerun()


##### PENDING CONSLTS ####
def count_pending_consult_clients(therapist_name):
    conn = create_connection()
    query = """
        SELECT statuses FROM appointments
        WHERE assigned_therapist = ?
    """
    df = pd.read_sql(query, conn, params=(therapist_name,))
    conn.close()

    def is_consult_pending(statuses_json):
        try:
            statuses = json.loads(statuses_json) if isinstance(statuses_json, str) else {}
            return statuses.get("consult", "Pending") == "Pending"
        except:
            return False

    pending_count = df["statuses"].apply(is_consult_pending).sum()
    return pending_count


import pandas as pd 
def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None
username = st.session_state.get("user_name")
pending_count = count_pending_consult_clients(username)

def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None  # ✅ Use index 0 for tuple




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

    pages = [
        {"title": "🧑‍⚕️", "text": "Consultations"},
        {"title": "📚", "text": "Reports"},
        {"title": "📘", "text": "Content"},
        {"title": "🗃️", "text": "Files"},
        {"title": '🗓️', "text": "Schedules"},
        {"title": "🔔", "text": "Notifications"}]

    cols = st.columns(num_cols_app, gap='small')
    for index, page in enumerate(pages):
        color = CARD_COLORS[index % len(CARD_COLORS)]
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



# 
def app_router(page, analysis=None, report=None, schedule=None, file=None, task=None, support=None):
    try:
        if task:
            match task:
                case text if text.startswith("Consults"):
                    import therapist_consult as mod
                case "Group sessions" | "Class sessions":
                    import therapist_forms as mod
                case "Follow-Ups":
                    import follow_up_manager as mod
                case _:
                    st.warning(f"🔧 The '{task}' page is under development.")
                    return
            mod.main()
            return

        if file:
            match file:
                case "Files":
                    import entire_file as mod
                case _:
                    st.warning(f"🔧 The '{file}' page is under development.")
                    return
            mod.main()
            return

        if report:
            match report:
                case "Reports":
                    import therapist_report as mod
                case _:
                    st.warning(f"🔧 The '{report}' page is under development.")
                    return
            mod.main()
            return

        if schedule:
            match schedule:
                case "Online bookings":
                    import therapist_bookings as mod
                    mod.main()
                    return
                case "Follow-Ups":
                    import follow_up_manager as mod
                    mod.main()
                    return
                case _:
                    st.warning(f"🔧 The '{schedule}' page is under development.")
                    return

        st.warning("🔧 This page is under development.")

    except ModuleNotFoundError as e:
        st.error(f"❌ Missing module: {e.name}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")




def show_schedule_menu(page_title):
    schedule_options = [  # FIX: use schedule_options consistently
        {"title": "🗓️", "text": "Online bookings"},
        {"title": "📞", "text": "Follow-Ups"},
    ]
    display_card_menu(page_title, schedule_options, "selected_schedule", num_cols=4)

def main():
    db = create_connection()
    create_user_sessions_table()
    set_full_page_background('images/std2.jpg')
    username = st.session_state.get("user_name")

    keys = [
        'full_name', 'user_id', 'appointment_id', 'selected_appointment',
        'selected_page', 'selected_archive', 'selected_report',
        'selected_schedule', 'selected_analysis', 'selected_task',
        'selected_support', 'selected_file'
    ]
    for key in keys:
        st.session_state.setdefault(key, None)

    if not st.session_state.selected_page:
        show_page_menu()
        return

    # 🔑 Add show_schedule_menu here
    page_menus = {
        "🧑‍⚕️": ("selected_task", None, "Consult Menu"),
        "🗃️": ("selected_file", None, "File Menu"),
        "📚": ("selected_report", None, "Report Menu"),
        "🗓️": ("selected_schedule", show_schedule_menu, "Schedule Menu"),
    }

    selected_key, show_func, back_label = page_menus.get(
        st.session_state.selected_page, (None, None, None)
    )

    if selected_key is None:
        st.warning(f"🔧 The '{st.session_state.selected_page}' page is under development.")
        if st.button("🔙 Back to Page Menu"):
            st.session_state.selected_page = None
            st.rerun()
        return

    # 🔙 Global Back Button
    if st.button("🔙 Back to Main Menu"):
        st.session_state.selected_page = None
        st.session_state[selected_key] = None
        st.rerun()

    if st.session_state[selected_key]:
        if st.button(f"🔙 {back_label}"):
            st.session_state[selected_key] = None
            st.rerun()
        app_router(
            st.session_state.selected_page,
            **{selected_key.split("_")[1]: st.session_state[selected_key]}
        )
        return

    if st.session_state.selected_page == "📚":
        import therapist_report
        therapist_report.main()
        return

    if st.session_state.selected_page == "🗃️":
        import entire_file
        entire_file.main()
        return

    if st.session_state.selected_page == "🧑‍⚕️":
        import therapist_consult
        therapist_consult.main()



    if show_func:
        show_func(st.session_state.selected_page)

if __name__ == "__main__":
    main()
