
import streamlit as st
import sqlite3
from streamlit_option_menu import option_menu
import base64, os
from datetime import datetime
import pandas as pd

DB_PATH = "users_db.db"
def create_connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.row_factory = sqlite3.Row
    return db

# st.markdown("""
#     <style>
#     .stButton button {
#         border-radius: 6px;
#         padding: 0.25rem 0.75rem;
#         font-size: 0.9rem;
#     }
#     </style>
# """, unsafe_allow_html=True)








dark_css = """
<style>
/* Only apply dark background where no custom background is set */
.stApp:not(.custom-background) {
    background-color: #121212 !important;
    color: #FFFFFF !important;
}

/* Inputs, buttons */
input, textarea, select, button, .stButton button {
    background-color: brown;
    color: orange;
    border-color: #555555 !important;
}

/* Tables */
.stDataFrame, .stDataFrame td, .stDataFrame th {
    background-color: #1E1E1E !important;
    color: #FFFFFF !important;
}

/* Custom cards and existing backgrounds remain intact */
.custom-card, .custom-background {
    background-color: unset !important;
    color: unset !important;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 10px;
}
::-webkit-scrollbar-track {
    background: #1E1E1E;
}
::-webkit-scrollbar-thumb {
    background-color: #555555;
    border-radius: 10px;
}
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)






def get_all_users():
    db = create_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT user_id, full_name, email, username, role, is_active 
        FROM users ORDER BY role, full_name
    """)
    users = cursor.fetchall()
    db.close()
    return users

def add_user_form():
    # st.subheader("➕ Add User")
    with st.form("add_active_user_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Admin", "Therapist",'Teacher'])
        submitted = st.form_submit_button("Create User")

        if submitted:
            if not all([full_name.strip(), email.strip(), username.strip(), password.strip()]):
                st.warning("Please fill in all fields.")
            else:
                try:
                    db = create_connection()
                    cursor = db.cursor()
                    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    cursor.execute("""
                        INSERT INTO users (user_id, full_name, email, username, password_hash, role, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"{role.upper()}-{username.upper()}",
                        full_name.strip(),
                        email.strip(),
                        username.strip(),
                        password_hash,
                        role,
                        1  # active
                    ))
                    db.commit()
                    st.success(f"{role} '{full_name}' created successfully!")
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f"Error: {e}")
                finally:
                    db.close()



def ensure_is_active_column():
    try:
        with create_connection() as db:
            cursor = db.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'is_active' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
                db.commit()
                st.success("✅ 'is_active' column added to users table.")
    except sqlite3.Error as e:
        st.error(f"❌ Failed to alter table: {e}")


def toggle_user_active(user_id, activate=True):
    db = create_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE users SET is_active = ? WHERE user_id = ?",
            (1 if activate else 0, user_id)
        )
        db.commit()
        st.success(f"User {'activated' if activate else 'deactivated'} successfully.")
    except sqlite3.Error as e:
        st.error(f"Failed to update user status: {e}")
    finally:
        db.close()


def edit_user_info():
    users = get_all_users()
    user_dicts = [dict(u) for u in users]
    with st.sidebar.expander('Search user',expanded = True):
        search_query = st.text_input("Search user")
    matched_users = [u for u in user_dicts if search_query.lower() in u["full_name"].lower()] if search_query else []
    if search_query and not matched_users:
        st.warning("No user found.")
        return
    if matched_users:
        with st.sidebar.expander('Search', expanded=True):
            selected_user = st.selectbox(
                "Select user to edit", matched_users,
                format_func=lambda u: f"{u['full_name']} ({u['role']})")
            st.markdown("### 👤 User Info")
            st.markdown(f"**Name:** {selected_user['full_name']}")
            st.markdown(f"**Email:** {selected_user['email']}")
            st.markdown(f"**Username:** {selected_user['username']}")
            st.markdown(f"**Role:** {selected_user['role']}")
            st.markdown(f"**Active:** {'✅ Active' if selected_user['is_active'] else '🚫 Inactive'}")
        with st.form("edit_user_form"):
            new_name = st.text_input("Full Name", value=selected_user["full_name"])
            new_email = st.text_input("Email", value=selected_user["email"])
            new_username = st.text_input("Username", value=selected_user["username"])
            new_role = st.selectbox("Role", ["Admin", "Therapist", "Teacher","Admin2", 'Student', 'Parent'],
                                    index=["Admin", "Therapist", "Teacher","Admin2",'Student'].index(selected_user["role"]))
            submitted = st.form_submit_button("Update User")

            if submitted:
                try:
                    db = create_connection()
                    db.execute("""
                        UPDATE users 
                        SET full_name = ?, email = ?, username = ?, role = ?
                        WHERE user_id = ?
                    """, (new_name, new_email, new_username, new_role, selected_user["user_id"]))
                    db.commit()
                    st.success("✅ User updated successfully.")
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f"❌ Database error: {e}")
                finally:
                    db.close()
        current_status = bool(selected_user["is_active"])
        action_btn = "Deactivate" if current_status else "Activate"
        if st.button(f"{'🚫' if current_status else '✅'} {action_btn} User", key="toggle_user_status"):
            toggle_user_active(selected_user["user_id"], not current_status)
            st.success(f"User {'deactivated' if current_status else 'activated'} successfully.")
            st.rerun()
def show_users_table():
    users = get_all_users()
    if not users:
        st.info("No users found.")
        return
    for user in users:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 0.5, 2.5, 2])
        col1.write(user["user_id"])
        col2.write(user["full_name"])
        col3.write(user["email"])
        col4.write(user["role"])
        col5.write("✅" if user["is_active"] else "🚫")
        if user["is_active"]:
            if col6.button("Deactivate", key=f"deact_{user['user_id']}"):
                toggle_user_active(user["user_id"], False)
                st.rerun()
        else:
            if col6.button("Activate", key=f"act_{user['user_id']}"):
                toggle_user_active(user["user_id"], True)
                st.rerun()
        if col7.button("Edit", key=f"edit_{user['user_id']}"):
            st.session_state.edit_user_id = user["user_id"]
    if st.session_state.get("edit_user_id"):
        user_id = st.session_state.edit_user_id
        db = create_connection()
        user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        db.close()
        with st.sidebar:
            if user:
                with st.form("edit_user_form_inline"):
                    st.subheader("✏️ Edit User")
                    new_name = st.text_input("Full Name", value=user["full_name"])
                    new_email = st.text_input("Email", value=user["email"])
                    new_username = st.text_input("Username", value=user["username"])
                    new_role = st.selectbox("Role", ["Admin", "Therapist", 'Teacher',"Admin2",'Student', 'Parent'],
                                            index=["Admin", "Therapist", 'Teacher',"Admin2",'Student','Parent'].index(user["role"]))
                    submitted = st.form_submit_button("Update User")
                    if submitted:
                        try:
                            db = create_connection()
                            db.execute("""
                                UPDATE users 
                                SET full_name = ?, email = ?, username = ?, role = ?
                                WHERE user_id = ?
                            """, (new_name, new_email, new_username, new_role, user_id))
                            db.commit()
                            st.success("✅ User updated successfully.")
                            del st.session_state.edit_user_id
                            st.rerun()
                        except sqlite3.IntegrityError as e:
                            st.error(f"❌ Database error: {e}")
                        finally:
                            db.close()

                current_status = bool(user["is_active"])
                action_btn = "Deactivate" if current_status else "Activate"
                if st.button(f"{'🚫' if current_status else '✅'} {action_btn} User", key="toggle_user_status_inline"):
                    toggle_user_active(user_id, not current_status)
                    st.success(f"User {'deactivated' if current_status else 'activated'} successfully.")
                    st.rerun()
            else:
                st.error("Selected user not found.")



def set_full_page_background(img):
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url('{img}');
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)



def view_session_logs():
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM sessions ORDER BY timestamp DESC", conn)
    conn.close()
    st.subheader("📋 User Session Logs")
    st.dataframe(df)



def main():
    set_full_page_background("images/black_strip.jpg")
    ensure_is_active_column()
    selected = option_menu(
        menu_title=None,
        options=["Add", "Edit", "Users", "Import_users",'User_sessions'],
        icons=["person-plus",  "pencil-square", "people", "cloud-upload", 'table'],
        default_index=2 if st.session_state.get("page") == "Users" else 0,
        orientation="horizontal",
        styles={
            "container": {"padding": "10!important", "background-color": '#1b4f72', 'border': '0.01px dotted red'},
            "icon": {"color": "red", "font-size": "12px"},
            "nav-link": {"color": "#d7c4c1", "font-size": "12px", "font-weight": 'bold', "text-align": "left", "margin": "0px", "--hover-color": "red"},
            "nav-link-selected": {"background-color": "green"},
        },
        key="register_menu")
    st.session_state.page = selected
    if selected == "Add":
        add_user_form()
    elif selected == "Edit":
        edit_user_info()
    elif selected == "Users":
        show_users_table()

    elif selected == "Import_users":
        import accont_script
        accont_script.main()

    elif selected == 'User_sessions':
        view_session_logs()



if __name__ == "__main__":
    main()
