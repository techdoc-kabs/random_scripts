


DB_PATH = "users_db.db"
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os, base64
import calendar
import uuid
import json
# ------------------- Helpers -------------------
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

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if "active_confirm_client" not in st.session_state:
    st.session_state["active_confirm_client"] = None

def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None

def update_appointment_response(appointment_id, response, responder_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointment_requests
        SET response = ?, responder = ?, response_date = ?
        WHERE id = ?
    """, (response, responder_name, datetime.now(), appointment_id))
    conn.commit()
    conn.close()

# ------------------- Dialog -------------------
@st.dialog("Appointment Response")
def respond_dialog():
    row = st.session_state.get("active_appointment_row")
    responder_name = st.session_state.get("responder_name", "Unknown")
    if row is not None:
        st.write(f"🗨️ Appointment from **{row['client_name']}** on **{row['appointment_date']} {row['appointment_time']}**")
        st.info(row['reason'])
        response = st.text_area("Your Response", key=f"response_input_{row['id']}")
        if st.button("✅ Submit", key=f"submit_response_{row['id']}"):
            if response.strip():
                update_appointment_response(row['id'], response.strip(), responder_name)
                st.success("✅ Response submitted successfully.")
                st.session_state["active_appointment_row"] = None
                st.rerun()
            else:
                st.warning("⚠️ Please enter a response before submitting.")



def fetch_therapist_usernames():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE role = 'Therapist'")
    therapists = [row[0] for row in cursor.fetchall()]
    conn.close()
    return therapists



def fetch_client_details(client_name_or_id: str):
    conn = create_connection()
    cursor = conn.cursor()
    query = """
        SELECT user_id, full_name, role, email, contact
        FROM users
        WHERE full_name = ? OR user_id = ?
        LIMIT 1
    """
    cursor.execute(query, (client_name_or_id, client_name_or_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "full_name": row[1],
            "role": row[2],
            "email": row[3],
            "contact": row[4],
        }
    return None

def appointment_form():
    username = st.session_state.get("user_name",)
    therapists = fetch_therapist_usernames()
    
    if "active_confirm_client" not in st.session_state:
        st.warning("⚠️ No client selected for confirmation.")
        return
    
    # client = st.session_state["active_confirm_client"]
    client = st.session_state.get("active_confirm_client")
    if not client:
        return  # or skip showing the sidebar form

    db_client = fetch_client_details(client.get("client_name"))
    if db_client:
        user_id = db_client["user_id"]
        name = db_client["full_name"]
        client_type = db_client["role"]
        email = db_client["email"]
        phone = db_client["contact"]

    with st.expander("📋 Confirm Appointment", expanded=True):
        col1, col2 = st.columns(2)
        col1.text_input("Client Name", value=name, disabled=True, key=f"client_name_{user_id}")
        col2.text_input("Client ID", value=user_id, disabled=True, key=f"client_id_{user_id}")
        col1.text_input("Client Type", value=client_type, disabled=True, key=f"client_type_{user_id}")
        col2.text_input("Email", value=email, disabled=True, key=f"email_{user_id}")
        col2.text_input("Phone", value=phone, disabled=True, key=f"phone_{user_id}")
        appointment_type = "New" if get_visit_count(user_id) == 0 else "Revisit"
        number_of_visits = get_visit_count(user_id) + 1
        col2.text_input("Appointment Type", appointment_type, disabled=True)
        col1.number_input("Number of Visits", value=number_of_visits, disabled=True)
        selected_actions = col2.multiselect("Select Actions", ["screen", "consult", "group session"])
        created_by = col1.selectbox("Created By", [username])
        screen_type = None
        if "screen" in selected_actions:
            screen_type = col1.selectbox(
                "Screen Type",
                ["", "PRE-SCREEN", "POST-SCREEN", "ON-CONSULT", "SELF-REQUEST"])
        actions, assigned_therapist, statuses, action_dates, remaining_time = {}, {}, {}, {}, {}
        for action in selected_actions:
            assignment_mode = st.radio(
                f"Who will handle '{action}'?",
                ["Self", "Assign Therapist(s)"],
                key=f"{action}_radio"
            )
            if assignment_mode == "Self":
                assigned_therapist[action] = ["SELF"]
            else:
                selected = col2.multiselect(
                    f"Select Therapist(s) for '{action}'",
                    therapists,
                    key=f"{action}_therapist_multi"
                )
                assigned_therapist[action] = selected if selected else []

            statuses[action] = "Pending"
            date = col1.date_input(f"Date for {action}", key=f"{action}_date")
            time = col2.time_input(f"Time for {action}", key=f"{action}_time")
            dt_str = f"{date} {time}"
            dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            delta = dt_obj - datetime.now()
            action_dates[action] = dt_str
            remaining_time[action] = f"{delta.days} days"
            actions[action] = True

        if st.button("✅ Confirm Appointment"):
            if not selected_actions:
                st.warning("⚠️ Please select at least one action.")
                return
            if "screen" in selected_actions and not screen_type:
                st.warning("⚠️ Please select a valid Screen Type for 'screen'.")
                return
            for action in selected_actions:
                if not assigned_therapist.get(action):
                    st.warning(f"⚠️ Please assign a therapist or select 'Self' for '{action}'.")
                    return

            data = {
                "appointment_id": generate_appointment_id(),
                "user_id": user_id,
                "name": name,
                "client_type": client_type,
                "appointment_type": appointment_type,
                "number_of_visits": number_of_visits,
                "actions": actions,
                "assigned_therapist": assigned_therapist,
                "statuses": statuses,
                "action_dates": action_dates,
                "remaining_time": remaining_time,
                "created_by": created_by,
                "appointment_date": action_dates[selected_actions[0]] if selected_actions else "",
                "appointment_time": action_dates[selected_actions[0]][11:] if selected_actions else "",
                "screen_type": screen_type if "screen" in selected_actions else None,
            }

            success, msg = insert_appointment(data)
            if success:
                st.success(f"✅ {msg} (Type: {appointment_type}, Visit#: {number_of_visits}, Client: {name})")
                del st.session_state["active_confirm_client"]
            else:
                st.error(msg)


# ---------------- Supporting Functions ----------------
def view_appointment_requests(therapist_name: str):
    conn = create_connection()
    query = """
        SELECT * FROM appointment_requests
        WHERE therapist_name = ?
        ORDER BY appointment_date DESC, appointment_time DESC
    """
    df = pd.read_sql_query(query, conn, params=(therapist_name,))
    conn.close()
    return df


def get_visit_count(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def generate_appointment_id():
    today = datetime.now().strftime("%Y%m%d")
    return f"App-{today}-{uuid.uuid4().hex[:2]}"


def insert_appointment(appointment_data):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        if "screen" in appointment_data['actions']:
            cursor.execute("""
                SELECT COUNT(*) FROM appointments
                WHERE user_id = ?
                  AND screen_type = ?
                  AND strftime('%Y', appointment_date) = strftime('%Y', ?)
                  AND json_extract(actions, '$.screen') = 1
            """, (
                appointment_data['user_id'],
                appointment_data.get('screen_type', ''),
                appointment_data.get('appointment_date', datetime.today().strftime('%Y-%m-%d'))
            ))
            if cursor.fetchone()[0] > 0:
                return False, "Duplicate screening appointment already exists for this screen type and year."

        cursor.execute("""
            INSERT INTO appointments (
                appointment_id, user_id, username, name,
                client_type, appointment_date, appointment_time,
                appointment_type, number_of_visits, actions, statuses,
                action_dates, remaining_time, assigned_therapist,
                screening_tools, screen_type, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_data['appointment_id'],
            appointment_data['user_id'],
            appointment_data.get('username'),
            appointment_data['name'],
            appointment_data['client_type'],
            appointment_data.get('appointment_date'),
            appointment_data.get('appointment_time'),
            appointment_data['appointment_type'],
            appointment_data['number_of_visits'],
            json.dumps(appointment_data['actions']),
            json.dumps(appointment_data['statuses']),
            json.dumps(appointment_data['action_dates']),
            json.dumps(appointment_data['remaining_time']),
            json.dumps(appointment_data['assigned_therapist']),
            json.dumps(appointment_data.get('screening_tools', {})),
            appointment_data.get('screen_type'),
            appointment_data['created_by']
        ))
        conn.commit()
        return True, "Appointment created successfully!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# def view_appointments(therapist_name: str):
#     df = view_appointment_requests(therapist_name)
#     if df.empty:
#         st.info(f"No appointments found for {therapist_name}.")
#         return
#     df["appointment_date"] = pd.to_datetime(df["appointment_date"])
#     df["response_date"] = pd.to_datetime(df.get("response_date"), errors='coerce')
#     with st.sidebar.expander('📅 Filter Appointments by Date', expanded=True):
#         all_years = sorted(df["appointment_date"].dt.year.unique(), reverse=True)
#         selected_years = st.multiselect("Select Year(s)", options=all_years, default=all_years)
#         df_filtered = df[df["appointment_date"].dt.year.isin(selected_years)]
#         available_months = sorted(df_filtered["appointment_date"].dt.month.unique())
#         month_names = [calendar.month_name[m] for m in available_months]
#         selected_month_names = st.multiselect("Select Month(s)", options=month_names, default=month_names)
#         selected_months = [list(calendar.month_name).index(m) for m in selected_month_names]
#         df_filtered = df_filtered[df_filtered["appointment_date"].dt.month.isin(selected_months)]
#         min_date = df_filtered["appointment_date"].min()
#         max_date = df_filtered["appointment_date"].max()
#         start_date = st.date_input("Choose Start Date", value=min_date, min_value=min_date, max_value=max_date)
#         end_date = st.date_input("Choose End Date", value=max_date, min_value=min_date, max_value=max_date)
#         df_filtered = df_filtered[
#             (df_filtered["appointment_date"] >= pd.to_datetime(start_date)) &
#             (df_filtered["appointment_date"] <= pd.to_datetime(end_date))]
#     if df_filtered.empty:
#         st.info("No appointments found in the selected period.")
#         return
#     st.markdown("""
#     <style>
#         .header-row { background-color: #1565c0; color: white; padding: 8px; border-radius: 5px; font-weight: bold; }
#         .data-row { padding: 6px; border-radius: 5px; }
#         .row-even { background-color: #2c2c2c; }
#         .row-odd { background-color: #1e1e1e; }
#         .no-response { color: #f39c12; font-weight: bold; }
#         .responded { color: #2ecc71; font-weight: bold; }
#     </style>
#     """, unsafe_allow_html=True)
#     header_cols = st.columns([2, 3, 2, 2, 3, 2, 2, 2])
#     titles = ["Client", "Email/Phone", "Date", "Time", "Reason", "Response", "Reply", "Confirm"]
#     for col, t in zip(header_cols, titles):
#         col.markdown(f"<div class='header-row'>{t}</div>", unsafe_allow_html=True)
#     for idx, row in df_filtered.iterrows():
#         row_class = "row-even" if idx % 2 == 0 else "row-odd"
#         row_cols = st.columns([2, 3, 2, 2, 3, 2, 2, 2])
#         client_id = row.get("user_id") or row.get("id") or row.get("appointment_id")
#         client_name = row.get("client_name") or row.get("full_name")
#         client_info = fetch_client_details(client_id) or {}
#         client_id = client_info.get("user_id", client_id)
#         client_name = client_info.get("full_name", client_name)
#         client_email = client_info.get("email", row.get("client_email", ""))
#         client_phone = client_info.get("contact", row.get("client_phone", ""))
#         client_type = client_info.get("role", row.get("client_type", "Client"))
#         appointment_date = row["appointment_date"].date()
#         appointment_time = row.get("appointment_time")
#         reason = row.get("reason", "")
#         response = row.get("response", "")
#         row_cols[0].markdown(f"<div class='data-row {row_class}'>{client_name}</div>", unsafe_allow_html=True)
#         row_cols[1].markdown(f"<div class='data-row {row_class}'>{client_email} / {client_phone}</div>", unsafe_allow_html=True)
#         row_cols[2].markdown(f"<div class='data-row {row_class}'>{appointment_date}</div>", unsafe_allow_html=True)
#         row_cols[3].markdown(f"<div class='data-row {row_class}'>{appointment_time}</div>", unsafe_allow_html=True)
#         row_cols[4].markdown(f"<div class='data-row {row_class}'>{reason}</div>", unsafe_allow_html=True)
#         is_responded = bool(response.strip())
#         response_display = f"<span class='responded'>{response}</span>" if is_responded else "<span class='no-response'>Pending</span>"
#         row_cols[5].markdown(f"<div class='data-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)
#         reply_key = f"respond_btn_{client_id}_{idx}"
#         if not is_responded:
#             if row_cols[6].button("Reply", key=reply_key):
#                 st.session_state["active_appointment_row"] = row.to_dict()
#                 respond_dialog()
#         else:
#             row_cols[6].markdown(f"<div class='data-row {row_class}'>✅</div>", unsafe_allow_html=True)
#         active_client = st.session_state.get("active_confirm_client")
#         active_client_id = active_client.get("id") if active_client else None
#         confirm_key = f"confirm_btn_{client_id}_{idx}"
#         close_key = f"close_btn_{client_id}_{idx}"
#         if active_client_id == client_id:
#             if row_cols[7].button("Close", key=close_key):
#                 st.session_state["active_confirm_client"] = None
#                 st.rerun() 
#         else:
#             if row_cols[7].button("Confirm", key=confirm_key):
#                 st.session_state["active_confirm_client"] = {
#                     "id": client_id,
#                     "client_name": client_name,
#                     "client_email": client_email,
#                     "client_phone": client_phone,
#                     "client_type": client_type,
#                     "appointment_date": str(appointment_date),
#                     "appointment_time": appointment_time,
#                     "reason": reason,
#                 }
#                 st.rerun()  # refresh immediately

#     # --- Sidebar selected client details ---
#     client = st.session_state.get("active_confirm_client")
#     if client:
#         db_client = fetch_client_details(client.get("client_name"))
#         if db_client:
#             user_id = db_client["user_id"]
#             name = db_client["full_name"]
#             client_type = db_client["role"]
#             email = db_client["email"]
#             phone = db_client["contact"]

#             with st.sidebar.expander("📌 Selected Client Details", expanded=True):
#                 st.markdown(f"**Client Name:** {name}")
#                 st.markdown(f"**Client ID:** {user_id}")
#                 st.markdown(f"**Email:** {email}")
#                 st.markdown(f"**Phone:** {phone}")
#                 st.markdown(f"**Client Type:** {client_type}")

#             st.markdown("---")
#             st.subheader("📋 Confirm Appointment Form")
#             appointment_form()


# def view_appointments(therapist_name: str):
#     df = view_appointment_requests(therapist_name)
#     if df.empty:
#         st.info(f"No appointments found for {therapist_name}.")
#         return

#     df["appointment_date"] = pd.to_datetime(df["appointment_date"])
#     df["response_date"] = pd.to_datetime(df.get("response_date"), errors='coerce')

#     # --- Sidebar filters ---
#     with st.sidebar.expander('📅 Filter Appointments by Date', expanded=True):
#         all_years = sorted(df["appointment_date"].dt.year.unique(), reverse=True)
#         selected_years = st.multiselect("Select Year(s)", options=all_years, default=all_years)
#         df_filtered = df[df["appointment_date"].dt.year.isin(selected_years)]

#         available_months = sorted(df_filtered["appointment_date"].dt.month.unique())
#         month_names = [calendar.month_name[m] for m in available_months]
#         selected_month_names = st.multiselect("Select Month(s)", options=month_names, default=month_names)
#         selected_months = [list(calendar.month_name).index(m) for m in selected_month_names]
#         df_filtered = df_filtered[df_filtered["appointment_date"].dt.month.isin(selected_months)]

#         min_date = df_filtered["appointment_date"].min()
#         max_date = df_filtered["appointment_date"].max()
#         start_date = st.date_input("Choose Start Date", value=min_date, min_value=min_date, max_value=max_date)
#         end_date = st.date_input("Choose End Date", value=max_date, min_value=min_date, max_value=max_date)
#         df_filtered = df_filtered[
#             (df_filtered["appointment_date"] >= pd.to_datetime(start_date)) &
#             (df_filtered["appointment_date"] <= pd.to_datetime(end_date))
#         ]

#     if df_filtered.empty:
#         st.info("No appointments found in the selected period.")
#         return

#     # --- Table header styling ---
#     st.markdown("""
#     <style>
#         .header-row { background-color: #1565c0; color: white; padding: 8px; border-radius: 5px; font-weight: bold; }
#         .data-row { padding: 6px; border-radius: 5px; }
#         .row-even { background-color: #2c2c2c; }
#         .row-odd { background-color: #1e1e1e; }
#         .no-response { color: #f39c12; font-weight: bold; }
#         .responded { color: #2ecc71; font-weight: bold; }
#     </style>
#     """, unsafe_allow_html=True)
#     header_cols = st.columns([2, 3, 2, 2, 3, 2, 2, 2])
#     titles = ["Client", "Email/Phone", "Date", "Time", "Reason", "Response", "Reply", "Confirm"]
#     for col, t in zip(header_cols, titles):
#         col.markdown(f"<div class='header-row'>{t}</div>", unsafe_allow_html=True)

#     for idx, row in df_filtered.iterrows():
#         row_class = "row-even" if idx % 2 == 0 else "row-odd"
#         row_cols = st.columns([2, 3, 2, 2, 3, 2, 2, 2])
#         client_id = row.get("user_id") or row.get("id") or row.get("appointment_id")
#         client_name = row.get("client_name") or row.get("full_name")
#         client_info = fetch_client_details(client_id) or {}
#         client_id = client_info.get("user_id", client_id)
#         client_name = client_info.get("full_name", client_name)
#         client_email = client_info.get("email", row.get("client_email", ""))
#         client_phone = client_info.get("contact", row.get("client_phone", ""))
#         client_type = client_info.get("role", row.get("client_type", "Client"))
#         appointment_date = row["appointment_date"].date()
#         appointment_time = row.get("appointment_time")
#         reason = row.get("reason", "")
#         response = row.get("response", "")
#         row_cols[0].markdown(f"<div class='data-row {row_class}'>{client_name}</div>", unsafe_allow_html=True)
#         row_cols[1].markdown(f"<div class='data-row {row_class}'>{client_email} / {client_phone}</div>", unsafe_allow_html=True)
#         row_cols[2].markdown(f"<div class='data-row {row_class}'>{appointment_date}</div>", unsafe_allow_html=True)
#         row_cols[3].markdown(f"<div class='data-row {row_class}'>{appointment_time}</div>", unsafe_allow_html=True)
#         row_cols[4].markdown(f"<div class='data-row {row_class}'>{reason}</div>", unsafe_allow_html=True)
#         is_responded = bool(response.strip())
#         response_display = f"<span class='responded'>{response}</span>" if is_responded else "<span class='no-response'>Pending</span>"
#         row_cols[5].markdown(f"<div class='data-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)
#         reply_key = f"respond_btn_{client_id}_{idx}"
#         if not is_responded:
#             if row_cols[6].button("Reply", key=reply_key):
#                 st.session_state["active_appointment_row"] = row.to_dict()
#                 respond_dialog()
        





#         else:
#             row_cols[6].markdown(f"<div class='data-row {row_class}'>✅</div>", unsafe_allow_html=True)

#         # Confirm / Close button
#         active_client = st.session_state.get("active_confirm_client")
#         active_client_id = active_client.get("id") if active_client else None

#         confirm_key = f"confirm_btn_{client_id}_{idx}"
#         close_key = f"close_btn_{client_id}_{idx}"
#         if active_client_id == client_id:
#             if row_cols[7].button("Close", key=close_key):
#                 st.session_state["active_confirm_client"] = None
#         else:
#             if row_cols[7].button("Confirm", key=confirm_key):
#                 st.session_state["active_confirm_client"] = {
#                     "id": client_id,
#                     "client_name": client_name,
#                     "client_email": client_email,
#                     "client_phone": client_phone,
#                     "client_type": client_type,
#                     "appointment_date": str(appointment_date),
#                     "appointment_time": appointment_time,
#                     "reason": reason,
#                 }

#     # --- Sidebar selected client details ---
#     client = st.session_state.get("active_confirm_client")
#     if client:
#         db_client = fetch_client_details(client.get("client_name"))
#         if db_client:
#             user_id = db_client["user_id"]
#             name = db_client["full_name"]
#             client_type = db_client["role"]
#             email = db_client["email"]
#             phone = db_client["contact"]

#             with st.sidebar.expander("📌 Selected Client Details", expanded=True):
#                 st.markdown(f"**Client Name:** {name}")
#                 st.markdown(f"**Client ID:** {user_id}")
#                 st.markdown(f"**Email:** {email}")
#                 st.markdown(f"**Phone:** {phone}")
#                 st.markdown(f"**Client Type:** {client_type}")

#             st.markdown("---")
#             st.subheader("📋 Confirm Appointment Form")
#             appointment_form()
def view_appointments(therapist_name: str):
    df = view_appointment_requests(therapist_name)
    if df.empty:
        st.info(f"No appointments found for {therapist_name}.")
        return

    # --- Convert dates safely ---
    df["appointment_date"] = pd.to_datetime(df["appointment_date"], errors="coerce")
    df["response_date"] = pd.to_datetime(df.get("response_date"), errors="coerce")

    # --- Sidebar filters ---
    with st.sidebar.expander('📅 Filter Appointments by Date', expanded=True):
        all_years = sorted(df["appointment_date"].dt.year.dropna().unique(), reverse=True)
        selected_years = st.multiselect("Select Year(s)", options=all_years, default=all_years)
        df_filtered = df[df["appointment_date"].dt.year.isin(selected_years)]

        available_months = sorted(df_filtered["appointment_date"].dt.month.dropna().unique())
        month_names = [calendar.month_name[m] for m in available_months]
        selected_month_names = st.multiselect("Select Month(s)", options=month_names, default=month_names)
        selected_months = [list(calendar.month_name).index(m) for m in selected_month_names]
        df_filtered = df_filtered[df_filtered["appointment_date"].dt.month.isin(selected_months)]

        min_date = df_filtered["appointment_date"].min()
        max_date = df_filtered["appointment_date"].max()
        if pd.notna(min_date) and pd.notna(max_date):
            start_date = st.date_input("Choose Start Date", value=min_date, min_value=min_date, max_value=max_date)
            end_date = st.date_input("Choose End Date", value=max_date, min_value=min_date, max_value=max_date)
            df_filtered = df_filtered[
                (df_filtered["appointment_date"] >= pd.to_datetime(start_date)) &
                (df_filtered["appointment_date"] <= pd.to_datetime(end_date))
            ]

    if df_filtered.empty:
        st.info("No appointments found in the selected period.")
        return

    # --- Table header styling ---
    st.markdown("""
    <style>
        .header-row { background-color: #1565c0; color: white; padding: 8px; border-radius: 5px; font-weight: bold; }
        .data-row { padding: 6px; border-radius: 5px; }
        .row-even { background-color: #2c2c2c; }
        .row-odd { background-color: #1e1e1e; }
        .no-response { color: #f39c12; font-weight: bold; }
        .responded { color: #2ecc71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    header_cols = st.columns([2, 3, 2, 2, 3, 2, 2, 2])
    titles = ["Client", "Email/Phone", "Date", "Time", "Reason", "Response", "Reply", "Confirm"]
    for col, t in zip(header_cols, titles):
        col.markdown(f"<div class='header-row'>{t}</div>", unsafe_allow_html=True)

    # --- Appointment rows ---
    for idx, row in df_filtered.iterrows():
        row_class = "row-even" if idx % 2 == 0 else "row-odd"
        row_cols = st.columns([2, 3, 2, 2, 3, 2, 2, 2])

        # --- Client & appointment details (safe defaults) ---
        client_id = row.get("user_id") or row.get("id") or row.get("appointment_id") or ""
        client_name = row.get("client_name") or row.get("full_name") or "Unknown"
        client_info = fetch_client_details(client_id) or {}

        client_id = client_info.get("user_id", client_id)
        client_name = client_info.get("full_name", client_name)
        client_email = client_info.get("email", row.get("client_email", ""))
        client_phone = client_info.get("contact", row.get("client_phone", ""))
        client_type = client_info.get("role", row.get("client_type", "Client"))

        appointment_date = row.get("appointment_date")
        appointment_date = appointment_date.date() if pd.notna(appointment_date) else "N/A"
        appointment_time = row.get("appointment_time") or "N/A"
        reason = row.get("reason") or ""
        response = row.get("response") or ""

        # --- Render row ---
        row_cols[0].markdown(f"<div class='data-row {row_class}'>{client_name}</div>", unsafe_allow_html=True)
        row_cols[1].markdown(f"<div class='data-row {row_class}'>{client_email} / {client_phone}</div>", unsafe_allow_html=True)
        row_cols[2].markdown(f"<div class='data-row {row_class}'>{appointment_date}</div>", unsafe_allow_html=True)
        row_cols[3].markdown(f"<div class='data-row {row_class}'>{appointment_time}</div>", unsafe_allow_html=True)
        row_cols[4].markdown(f"<div class='data-row {row_class}'>{reason}</div>", unsafe_allow_html=True)

        # --- Response column ---
        is_responded = bool(response.strip())
        response_display = f"<span class='responded'>{response}</span>" if is_responded else "<span class='no-response'>Pending</span>"
        row_cols[5].markdown(f"<div class='data-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)

        # --- Reply button ---
        reply_key = f"respond_btn_{client_id}_{idx}"
        if not is_responded:
            if row_cols[6].button("Reply", key=reply_key):
                st.session_state["active_appointment_row"] = row.to_dict()
                respond_dialog()
        else:
            row_cols[6].markdown(f"<div class='data-row {row_class}'>✅</div>", unsafe_allow_html=True)

        # --- Confirm / Close button ---
        active_client = st.session_state.get("active_confirm_client")
        active_client_id = active_client.get("id") if active_client else None

        confirm_key = f"confirm_btn_{client_id}_{idx}"
        close_key = f"close_btn_{client_id}_{idx}"
        if active_client_id == client_id:
            if row_cols[7].button("Close", key=close_key):
                st.session_state["active_confirm_client"] = None
        else:
            if row_cols[7].button("Confirm", key=confirm_key):
                st.session_state["active_confirm_client"] = {
                    "id": client_id,
                    "client_name": client_name,
                    "client_email": client_email,
                    "client_phone": client_phone,
                    "client_type": client_type,
                    "appointment_date": str(appointment_date),
                    "appointment_time": appointment_time,
                    "reason": reason,
                }

    # --- Sidebar selected client details ---
    client = st.session_state.get("active_confirm_client")
    if client:
        db_client = fetch_client_details(client.get("client_name"))
        if db_client:
            user_id = db_client.get("user_id", "")
            name = db_client.get("full_name", "Unknown")
            client_type = db_client.get("role", "Client")
            email = db_client.get("email", "")
            phone = db_client.get("contact", "")

            with st.sidebar.expander("📌 Selected Client Details", expanded=True):
                st.markdown(f"**Client Name:** {name}")
                st.markdown(f"**Client ID:** {user_id}")
                st.markdown(f"**Email:** {email}")
                st.markdown(f"**Phone:** {phone}")
                st.markdown(f"**Client Type:** {client_type}")

            st.markdown("---")
            st.subheader("📋 Confirm Appointment Form")
            appointment_form()


def main():
    set_full_page_background('images/black_strip.jpg')
    username = st.session_state.get("user_name")
    full_name = get_full_name_from_username(username)
    therapist_name = full_name or username or "Unknown"
    if "responder_name" not in st.session_state:
        st.session_state["responder_name"] = therapist_name
    view_appointments(therapist_name)
if __name__ == "__main__":
    main()