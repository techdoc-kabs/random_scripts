DB_PATH = "users_db.db"

import streamlit as st
from streamlit_card import card
from streamlit_javascript import st_javascript
from streamlit_option_menu import option_menu
import sqlite3

from datetime import datetime
import os, base64
import pandas as pd
def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None


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


# ID Generators
def screen_id(db):
    cursor = db.cursor()
    cursor.execute("SELECT IFNULL(MAX(id), 0) + 1 FROM enrolled_users")
    next_id = cursor.fetchone()[0]
    return f"Screen-{datetime.now().strftime('%Y-%m-%d')}-{next_id:04}"

def consult_id(db):
    cursor = db.cursor()
    cursor.execute("SELECT IFNULL(MAX(id), 0) + 1 FROM enrolled_users")
    next_id = cursor.fetchone()[0]
    return f"Consult-{datetime.now().strftime('%Y-%m-%d')}-{next_id:04}"

# Enrollment Table
def create_enrolled_users_table(db):
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrolled_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id TEXT UNIQUE,
        user_id TEXT,
        name TEXT,
        username TEXT,
        enrollemnt_status TEXT DEFAULT 'New',
        term TEXT,
        screen_type TEXT,
        enrollment_date TEXT,
        enrollment_time TEXT,
        enrolled_by TEXT,
        enrolled_count INTEGER DEFAULT 1, 
        assigment_status TEXT DEFAULT 'Not Assigned',
        enrollment_reason TEXT,
        role TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)
    db.commit()

# Determine Enrollment Status
def determine_enrollment_status(db, user_id):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM enrolled_users WHERE user_id = ?", (user_id,))
    return "New" if cursor.fetchone()[0] == 0 else "Revisit"

def determine_enrollment_count(db, user_id):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM enrolled_users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()[0]

# Search users
def fetch_users_by_input(db, search_input):
    cursor = db.cursor()
    search_input = search_input.strip()
    if search_input.upper().startswith(("STUD-", "PARENT-", "TEACH-", "ID-")) or search_input.isdigit():
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (search_input,))
    else:
        name_parts = search_input.split()
        if len(name_parts) == 2:
            cursor.execute("SELECT * FROM users WHERE full_name LIKE ? OR full_name LIKE ?", 
                           (f"%{name_parts[0]} {name_parts[1]}%", f"%{name_parts[1]} {name_parts[0]}%"))
        else:
            cursor.execute("SELECT * FROM users WHERE full_name LIKE ?", (f"%{search_input}%",))
    return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

def fetch_column_values(db, column):
    cursor = db.cursor()
    cursor.execute(f"SELECT DISTINCT {column} FROM users")
    return [row[0] for row in cursor.fetchall()]

def check_screen_conditions(db, student_id, name, term, screen_type):
    cursor = db.cursor()
    valid_screen_types = ['PRE-SCREEN', 'POST-SCREEN', 'CONSULT-SCREEN', 'ON-REQUEST']
    
    if screen_type not in valid_screen_types:
        st.warning(f"Invalid screen type: {screen_type}")
        return False

    cursor.execute("""
        SELECT screen_type, appointment_date 
        FROM screen_appointments 
        WHERE student_id = ? AND term = ?
    """, (student_id, term))
    
    pre_screen_found = post_screen_found = False
    for row in cursor.fetchall():
        existing_screen_type = row[0]
        if existing_screen_type == 'PRE-SCREEN':
            pre_screen_found = True
        elif existing_screen_type == 'POST-SCREEN':
            post_screen_found = True
        if pre_screen_found and post_screen_found:
            st.warning(f"{name} already has both PRE-SCREEN and POST-SCREEN for this {term}.")
            return False

    if screen_type == 'PRE-SCREEN' and pre_screen_found:
        st.warning(f"{name} already has a pre-screen appointment in this {term}.")
        return False
    elif screen_type == 'POST-SCREEN':
        if not pre_screen_found:
            st.warning(f"Post screen cannot occur before pre-screen in this {term}.")
            return False
        if post_screen_found:
            st.warning(f"{name} already has a post-screen appointment in {term}.")
            return False

    return True

def main():
    db = create_connection()
    if not db:
        return

    create_enrolled_users_table(db)
    set_full_page_background('images/black_strip.jpg')

    enroller = st.session_state.get("name", "")
    enrollment_reasons = ['Screening', 'Special Consult']
    
    enroll_menu = option_menu(
        menu_title='',
        orientation='horizontal',
        menu_icon='',
        options=['Schedule', 'Assign Tools', 'Status'],
        icons=['calendar-plus', 'book', 'hourglass-split'],
        styles={
            "container": {"padding": "10!important", "background-color": 'black', 'border': '0.01px dotted red'},
            "icon": {"color": "red", "font-size": "14px"},
            "nav-link": {"color": "#d7c4c1", "font-size": "14px", "font-weight": 'bold', "text-align": "left", "margin": "0px", "--hover-color": "red"},
            "nav-link-selected": {"background-color": "green"},
        },
        key="enroll_menu"
    )

    if enroll_menu == 'Schedule':
        c1, c2 = st.columns([1, 2])

        with c1.expander('CLIENT ENROLLMENT', expanded=True):
            schedule_option = st.radio("Select schedule", ['One Client', 'Enroll Multiple'])

        if schedule_option == 'One Client':
            with c2.expander("🔍 SEARCH", expanded=True):
                search_input = st.text_input("Enter Name or Student ID", "")

            results = fetch_users_by_input(db, search_input) if search_input.strip() else []
            selected_record = None

            if results:
                st.sidebar.markdown(
                    """
                    <style>
                        .enrollment-header {
                            font-family: Haettenschweiler, sans-serif;
                            text-align: center;
                            color: #FFFFFF;
                            background-color: #4A90E2;
                            padding: 5px;
                            border-radius: 5px;
                            font-size: 25px;
                        }
                    </style>
                    <div class='enrollment-header'>STUDENT RECORD</div>
                    """,
                    unsafe_allow_html=True
                )
                st.sidebar.write('')
                with st.sidebar.expander('', expanded=True):
                    st.write(f"**{len(results)} result(s) found**")
                    options = {f"{r['full_name']} - {r['user_id']}": r for r in results}
                    selected_option = st.selectbox("Select a record:", list(options.keys()))
                selected_record = options[selected_option]

                user_id = selected_record['user_id']
                full_name = selected_record['full_name']
                username = selected_record.get('username', '')
                role = selected_record['role']
                st.session_state.update(selected_record)
                enrollment_status = determine_enrollment_status(db, user_id)
                enrollment_count = determine_enrollment_count(db, user_id) + 1

                with st.expander("Enrollment Form", expanded=True):
                    enrollment_date = datetime.now()
                    enrollment_time = datetime.now().time()
                    enrolled_by = st.text_input("Enrolled By", enroller)
                    reason = st.selectbox("Reason", enrollment_reasons)
                    role = st.text_input("Client", role)

                    term = ''
                    if selected_record.get('role', '').lower() == 'student':
                        term = st.selectbox('Term', ['', '1st-Term', '2nd-Term', '3rd-Term'])

                    screen_type = ''
                    if reason == 'Screening':
                        screen_type = st.selectbox('Screen Type', ['', 'PRE-SCREEN', 'POST-SCREEN', 'ON-CONSULT'])

                    if st.button("Enroll Now"):
                        required_fields = [enrollment_date, enrollment_time, enrolled_by, reason]
                        if selected_record.get('role', '').lower() == 'student':
                            required_fields.append(term)
                        if reason == 'Screening':
                            required_fields.append(screen_type)

                        if not all(required_fields):
                            st.warning("Please fill in all required fields.")
                        else:
                            enrollment_id = screen_id(db) if reason == 'Screening' else consult_id(db)
                            try:
                                cursor = db.cursor()
                                cursor.execute("""
                                    INSERT INTO enrolled_users (
                                        enrollment_id, user_id, name, username,
                                        enrollemnt_status, term, screen_type,
                                        enrollment_date, enrollment_time, role,
                                        enrolled_by, enrolled_count, enrollment_reason
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                                """, (
                                    enrollment_id, user_id, full_name, username,
                                    enrollment_status, term, screen_type,role,
                                    enrollment_date.strftime('%Y-%m-%d'),
                                    enrollment_time.strftime('%H:%M:%S'),
                                    enrolled_by, enrollment_count, reason, 
                                ))
                                db.commit()
                                st.success("Enrollment successful.")
                            except Exception as e:
                                st.error(f"Failed to enroll: {e}")
            elif search_input.strip():
                st.warning(f"No results found for '{search_input}'")

        elif schedule_option == 'Enroll Multiple':
            with st.sidebar.expander('📋 FILTER OPTIONS', expanded=True):
                filter_columns = ['role', 'student_class', 'stream', 'gender']
                selected_filters = st.multiselect("Filter users by:", filter_columns)
                where_clauses = []
                filter_values = []
                if selected_filters:
                    for col in selected_filters:
                        options = list(set(fetch_column_values(db, col)))
                        selected_vals = st.multiselect(f"Select {col.title()}", options)
                        if selected_vals:
                            placeholders = ','.join(['?'] * len(selected_vals))
                            where_clauses.append(f"{col} IN ({placeholders})")
                            filter_values.extend(selected_vals)
                    query = "SELECT * FROM users"
                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)
                else:
                    query = "SELECT * FROM users"
                cursor = db.cursor()
                cursor.execute(query, filter_values)
                filtered_users = cursor.fetchall()
            filtered_users = [dict(zip([col[0] for col in cursor.description], row)) for row in filtered_users]
            if filtered_users:
                df = pd.DataFrame(
                    [(c["user_id"], c["full_name"], c.get("role", ""), c.get("student_class", ""), c.get("stream", ""), c.get("gender", ""))
                     for c in filtered_users],
                    columns=["ID", "Name", "Client Type", "Class", "Stream", "Gender"]
                )
                df.index += 1

                if st.sidebar.checkbox('🔍 View selected users'):
                    with st.expander(f"📦 {len(filtered_users)} Client(s) Selected", expanded=True):
                        st.dataframe(df, use_container_width=True)

                with st.expander("📋 Enrollment Form", expanded=True):
                    col1, col2 = st.columns(2)
                    enrollment_date = col1.date_input("📅 Enrollment Date")
                    enrollment_time = col1.time_input("⏰ Enrollment Time")
                    enrolled_by = col2.text_input("👨‍⚕️ Enrolled By", enroller)
                    reason = col2.selectbox("📌 Reason for Enrollment", enrollment_reasons)
                    has_students = any(c.get('role', '').lower() == 'student' for c in filtered_users)
                    term = ''
                    if has_students:
                        term = col1.selectbox('📚 Term (only for students)', ['', '1st-Term', '2nd-Term', '3rd-Term'])
                    screen_type = ''
                    if reason == 'Screening':
                        screen_type = col2.selectbox('📊 Screening Type', ['', 'PRE-SCREEN', 'POST-SCREEN', 'CONSULT-SCREEN', 'ON-REQUEST'])

                    submit = col1.button("✅ Schedule Enrollments")
                    if submit:
                        if not enrollment_date or not enrollment_time or not enrolled_by or not reason:
                            st.warning("⚠️ Please complete all required fields.")
                        else:
                            success_count = 0
                            for client in filtered_users:
                                user_id = client['user_id']
                                full_name = client['full_name']
                                role = client.get('role', '').lower()
                                username = client.get('username', '')

                                this_term = term if role == 'student' else ''
                                this_screen = screen_type if reason == 'Screening' else ''
                                enrollment_status = determine_enrollment_status(db, user_id)
                                enrollment_count = determine_enrollment_count(db, user_id) + 1
                                enrollment_id = screen_id(db) if reason == 'Screening' else consult_id(db)

                                try:
                                    cursor.execute("""
                                        INSERT INTO enrolled_users (
                                            enrollment_id, user_id, name, username,
                                            enrollemnt_status, term, screen_type,
                                            enrollment_date, enrollment_time, role,
                                            enrolled_by, enrolled_count, enrollment_reason
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        enrollment_id, user_id, full_name, username,
                                        enrollment_status, this_term, this_screen,
                                        enrollment_date.strftime('%Y-%m-%d'),
                                        enrollment_time.strftime('%H:%M:%S'),
                                        role,
                                        enrolled_by, enrollment_count, reason
                                    ))
                                    success_count += 1
                                except Exception as e:
                                    st.error(f"⚠️ Failed to enroll {full_name}: {e}")
                            db.commit()
                            st.success(f"✅ {success_count} client(s) enrolled successfully.")
            else:
                st.warning("🚫 No users matched your filter criteria.")

if __name__ == "__main__":
    main()
