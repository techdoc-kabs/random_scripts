import streamlit as st
from streamlit_card import card
import sqlite3

import therapist
import base64
import os
from streamlit_javascript import st_javascript
import appointments
import json



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
                background-attachment: fixed;}}
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
        {"title": '🗓️', "text": "Schedules"},
        {"title": "📚", "text": "Reports"},
        {"title": "📈", "text": "Analysis"},
        {"title": "📧", "text": "Messages"},
        {"title": "🗃️", "text": "Files"},
        {"title": "🗄️", "text": "Resources"},
    ]

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

def show_resource_menu(page_title):
    resource_options = [
        {"title": '🎥', "text": "Videos"},
        {"title": "🎙️", "text": "Podcasts"},
        {"title": "📖", "text": "Publish"},

    ]
    display_card_menu(page_title, resource_options, "selected_resource", num_cols=3)

def show_schedule_menu(page_title):
    schedule_options = [
        {"title": '📝', "text": "Enroll Clients"},
        {"title": "💢", "text": "Assign Tools"},
        {"title": "⏳", "text": "Status"},
    ]
    display_card_menu(page_title, schedule_options, "selected_schedule", num_cols=4)

def show_analysis_menu(page_title):
    analysis_options = [
        {"title": "📦", "text": "Results"},
        {"title": "📊", "text": "Graphs"},
        # {"title": "🌍", "text": "Impact"},  # Coming soon
    ]
    display_card_menu(page_title, analysis_options, "selected_analysis", num_cols=3)

def show_report_menu(page_title):
    report_options = [
        {"title": '💹', "text": "Activities"},
        {"title": "🧠", "text": "Conditions"},
        {"title": "🌍", "text": "Impact"},
    ]
    display_card_menu(page_title, report_options, "selected_report", num_cols=3)


def show_support_menu(page_title):
    support_options = [
        {"title": "🙋‍♀️", "text": "Need help"},
        {"title": "💬", "text": "Feedback"},
        {"title": "📅", "text": "Bookings"},
    ]
    display_card_menu(page_title, support_options, "selected_support", num_cols=4)


def app_router(page, analysis=None, report=None, schedule=None, file=None, support=None, resource=None):
    try:
        if schedule:
            if schedule == "Enroll Clients":
                import appointments; appointments.main()
            elif schedule == "Assign Tools":
                import assingn_tools; assingn_tools.main()
            elif schedule == "Status":
                import track_screen_status; track_screen_status.main()
            else:
                st.info(f"Coming Soon: {schedule}")
            return

        if resource:
            if resource == "Videos":
                import video_handles; video_handles.main()
            


            elif resource == "Podcasts":
                st.info('Starting soon')
            elif resource == "Publish":
                st.info('Soonest')
            else:
                st.info(f"Coming Soon: {schedule}")
            return



        if analysis:
            if analysis == "Results":
                import screen_results_mult; screen_results_mult.main()
            elif analysis == "Graphs":
                import graphs; graphs.main()
            else:
                st.info(f"Coming Soon: {analysis}")
            return
        if report:
            if report == "Activities":
                import activity_summary; activity_summary.main()
            elif report == "Conditions":
                import screen_results_mult; screen_results_mult.main()

            elif report == "Impact":
                import impact; impact.main()
            else:
                st.info(f"Coming Soon: {report}")
            return
        if support:
            if support == "Need help":
               import need_help; need_help.main()

            elif support =="Feedback":
                import feedback; feedback.main()

            elif support =='Bookings':
                import bookings; bookings.main()
            return
        if file:
            if file == "Files":
                import entire_file; entire_file.main()
            else:
                st.info(f"Coming Soon: {file}")
            return

        st.warning("🔧 This page is under development.")
    except ModuleNotFoundError:
        st.info("Coming Soon: This feature is not available yet.")


#### DRIVE CODE ########
def main():
    set_full_page_background('images/psy4.jpg')
    keys = [
        'full_name', 'user_id', 'appointment_id', 'selected_appointment',
        'selected_page', 'selected_file', 'selected_report','selected_resource',
        'selected_schedule', 'selected_analysis', 'selected_task', 'selected_support']
    for key in keys:
        if key not in st.session_state:
            st.session_state[key] = None
    if not st.session_state.selected_page:
        show_page_menu()
        return
    page_menus = {
        "🗓️": ("selected_schedule", show_schedule_menu, "Schedule Menu"),
        "📈": ("selected_analysis", show_analysis_menu, "Analysis Menu"),
        "📚": ("selected_report", show_report_menu, "Report Menu"),
        "📧": ("selected_support", show_support_menu, "Support Menu"),
        "🗄️": ("selected_resource", show_resource_menu, "Resource Menu"),
        "🗃️": ("selected_file", None, "Main Menu"),}
    
    selected_key, show_func, back_label = page_menus.get(st.session_state.selected_page, (None, None, None))
    if selected_key is None:
        show_page_menu()
        return
    if st.session_state[selected_key]:
        if st.button(f"🔙 {back_label}"):
            if selected_key == "selected_file":
                st.session_state[selected_key] = None
                st.session_state.selected_page = None
            else:
                st.session_state[selected_key] = None
            st.rerun()
        if st.session_state.selected_page == "🗃️":
            import entire_file
            entire_file.main()

        else:
            app_router(
                st.session_state.selected_page,
                **{selected_key.split("_")[1]: st.session_state[selected_key]})
    else:
        if st.button("🔙 Page Menu"):
            st.session_state[selected_key] = None
            st.session_state.selected_page = None
            st.rerun()
        elif st.session_state.selected_page == "🗃️" and not st.session_state[selected_key]:
            st.session_state[selected_key] = "Files"
            st.rerun()
        elif show_func:
            show_func(st.session_state.selected_page)

if __name__ == "__main__":
    main()


