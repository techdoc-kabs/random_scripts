# DB_PATH = "users_db.db"
# import streamlit as st
# import pandas as pd
# import sqlite3
# from datetime import datetime
# import os, base64
# import calendar

# # ------------------- Helpers -------------------
# def set_full_page_background(image_path):
#     try:
#         if not os.path.exists(image_path):
#             st.error(f"Image file '{image_path}' not found.")
#             return
#         with open(image_path, "rb") as image_file:
#             encoded_string = base64.b64encode(image_file.read()).decode()
#         st.markdown(
#             f"""
#             <style>
#             [data-testid="stApp"] {{
#                 background-image: url("data:image/jpg;base64,{encoded_string}");
#                 background-size: cover;
#                 background-position: center;
#                 background-repeat: no-repeat;
#                 background-attachment: fixed;
#             }}
#             </style>
#             """,
#             unsafe_allow_html=True
#         )
#     except Exception as e:
#         st.error(f"Error setting background: {e}")

# def create_connection():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     return conn

# def get_full_name_from_username(username):
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
#     result = cursor.fetchone()
#     conn.close()
#     return result["full_name"] if result else None

# def update_appointment_response(appointment_id, response, responder_name):
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         UPDATE appointment_requests
#         SET response = ?, responder = ?, response_date = ?
#         WHERE id = ?
#     """, (response, responder_name, datetime.now(), appointment_id))
#     conn.commit()
#     conn.close()

# # ------------------- Dialog -------------------
# @st.dialog("Appointment Response")
# def respond_dialog():
#     row = st.session_state.get("active_appointment_row")
#     responder_name = st.session_state.get("responder_name", "Unknown")
#     if row is not None:
#         st.write(f"🗨️ Appointment from **{row['client_name']}** on **{row['appointment_date']} {row['appointment_time']}**")
#         st.info(row['reason'])
#         response = st.text_area("Your Response", key=f"response_input_{row['id']}")
#         if st.button("✅ Submit", key=f"submit_response_{row['id']}"):
#             if response.strip():
#                 update_appointment_response(row['id'], response.strip(), responder_name)
#                 st.success("✅ Response submitted successfully.")
#                 st.session_state["active_appointment_row"] = None
#                 st.rerun()
#             else:
#                 st.warning("⚠️ Please enter a response before submitting.")

# # ------------------- View Appointments -------------------
# def view_appointments():
#     conn = create_connection()
#     df = pd.read_sql_query("SELECT * FROM appointment_requests ORDER BY appointment_date DESC, appointment_time DESC", conn)
#     conn.close()

#     if df.empty:
#         st.info("No appointments found.")
#         return

#     df["appointment_date"] = pd.to_datetime(df["appointment_date"])
#     df["response_date"] = pd.to_datetime(df["response_date"], errors='coerce')

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
#         df_filtered = df_filtered[(df_filtered["appointment_date"] >= pd.to_datetime(start_date)) &
#                                   (df_filtered["appointment_date"] <= pd.to_datetime(end_date))]

#     if df_filtered.empty:
#         st.info("No appointments found.")
#         return

#     responder_name = st.session_state.get("responder_name", "Unknown")

#     st.markdown("""
#     <style>
#         .appt-header { background-color: #1565c0; color: white; padding: 8px; border-radius: 5px; font-weight: bold; }
#         .appt-row { padding: 6px; border-radius: 5px; }
#         .row-even { background-color: #2c2c2c; }
#         .row-odd { background-color: #1e1e1e; }
#         .responder-name { color: #81c784; font-weight: bold; }
#         .no-response { color: #f39c12; font-weight: bold; }
#         .responded { color: #2ecc71; font-weight: bold; }
#     </style>
#     """, unsafe_allow_html=True)

#     header_cols = st.columns([2, 3, 2, 2, 3, 2, 2])
#     header_titles = ["Client", "Email/Phone", "Therapist", "Date", "Time/Reason", "Response", "Action"]
#     for col, title in zip(header_cols, header_titles):
#         col.markdown(f"<div class='appt-header'>{title}</div>", unsafe_allow_html=True)

#     for i, row in df_filtered.iterrows():
#         row_class = 'row-even' if i % 2 == 0 else 'row-odd'
#         is_responded = bool(row['response']) and row['response'].strip() != ""
#         response_display = (
#             f"<span class='responded'>{row['response']}</span>"
#             if is_responded else "<span class='no-response'>Pending</span>"
#         )

#         row_cols = st.columns([2, 3, 2, 2, 3, 2, 2])
#         row_cols[0].markdown(f"<div class='appt-row {row_class}'>{row['client_name']}</div>", unsafe_allow_html=True)
#         row_cols[1].markdown(f"<div class='appt-row {row_class}'>{row['client_email']} / {row['client_phone']}</div>", unsafe_allow_html=True)
#         row_cols[2].markdown(f"<div class='appt-row {row_class}'>{row['therapist_name']}</div>", unsafe_allow_html=True)
#         row_cols[3].markdown(f"<div class='appt-row {row_class}'>{row['appointment_date'].date()}</div>", unsafe_allow_html=True)
#         row_cols[4].markdown(f"<div class='appt-row {row_class}'>{row['appointment_time']}<br>{row['reason'][:50]}{'...' if len(row['reason']) > 50 else ''}</div>", unsafe_allow_html=True)
#         row_cols[5].markdown(f"<div class='appt-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)

#         if not is_responded:
#             if row_cols[6].button("Reply", key=f"respond_btn_{row['id']}"):
#                 st.session_state["active_appointment_row"] = row
#                 respond_dialog()
#         else:
#             row_cols[6].markdown(f"<div class='appt-row {row_class}'>✅</div>", unsafe_allow_html=True)

# # ------------------- Main -------------------
# def main():
#     username = st.session_state.get("user_name")
#     full_name = get_full_name_from_username(username)
#     responder_name = full_name or username or "Unknown"
#     st.session_state["responder_name"] = responder_name

#     set_full_page_background('images/black_strip.jpg')
#     st.write('---')
#     view_appointments()

# if __name__ == "__main__":
#     main()


DB_PATH = "users_db.db"
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os, base64
import calendar

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

# ------------------- View Appointments -------------------
def view_appointments():
    conn = create_connection()
    df = pd.read_sql_query(
        "SELECT * FROM appointment_requests ORDER BY appointment_date DESC, appointment_time DESC", conn
    )
    conn.close()

    if df.empty:
        st.info("No appointments found.")
        return

    df["appointment_date"] = pd.to_datetime(df["appointment_date"])
    df["response_date"] = pd.to_datetime(df["response_date"], errors='coerce')

    # Sidebar filters
    with st.sidebar.expander('📅 Filter Appointments by Date', expanded=True):
        all_years = sorted(df["appointment_date"].dt.year.unique(), reverse=True)
        selected_years = st.multiselect("Select Year(s)", options=all_years, default=all_years)
        df_filtered = df[df["appointment_date"].dt.year.isin(selected_years)]

        available_months = sorted(df_filtered["appointment_date"].dt.month.unique())
        month_names = [calendar.month_name[m] for m in available_months]
        selected_month_names = st.multiselect("Select Month(s)", options=month_names, default=month_names)
        selected_months = [list(calendar.month_name).index(m) for m in selected_month_names]
        df_filtered = df_filtered[df_filtered["appointment_date"].dt.month.isin(selected_months)]

        min_date = df_filtered["appointment_date"].min()
        max_date = df_filtered["appointment_date"].max()
        start_date = st.date_input("Choose Start Date", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("Choose End Date", value=max_date, min_value=min_date, max_value=max_date)
        df_filtered = df_filtered[
            (df_filtered["appointment_date"] >= pd.to_datetime(start_date)) &
            (df_filtered["appointment_date"] <= pd.to_datetime(end_date))
        ]

    if df_filtered.empty:
        st.info("No appointments found.")
        return
    responder_name = st.session_state.get("responder_name", "Unknown")

    st.markdown("""
    <style>
        .appt-header { background-color: #1565c0; color: white; padding: 8px; border-radius: 5px; font-weight: bold; }
        .appt-row { padding: 6px; border-radius: 5px; }
        .row-even { background-color: #2c2c2c; }
        .row-odd { background-color: #1e1e1e; }
        .responder-name { color: #81c784; font-weight: bold; }
        .no-response { color: #f39c12; font-weight: bold; }
        .responded { color: #2ecc71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    # Table headers
    header_cols = st.columns([2, 3, 2, 2, 3, 2, 2])
    header_titles = ["Client", "Email/Phone", "Therapist", "Date", "Time/Reason", "Response", "Action"]
    for col, title in zip(header_cols, header_titles):
        col.markdown(f"<div class='appt-header'>{title}</div>", unsafe_allow_html=True)

    # Table rows
    for i, row in df_filtered.iterrows():
        row_class = 'row-even' if i % 2 == 0 else 'row-odd'
        is_responded = bool(row['response']) and row['response'].strip() != ""
        response_display = (
            f"<span class='responded'>{row['response']}</span>"
            if is_responded else "<span class='no-response'>Pending</span>"
        )

        row_cols = st.columns([2, 3, 2, 2, 3, 2, 2])
        row_cols[0].markdown(f"<div class='appt-row {row_class}'>{row['client_name']}</div>", unsafe_allow_html=True)
        row_cols[1].markdown(f"<div class='appt-row {row_class}'>{row['client_email']} / {row['client_phone']}</div>", unsafe_allow_html=True)
        row_cols[2].markdown(f"<div class='appt-row {row_class}'>{row['therapist_name']}</div>", unsafe_allow_html=True)
        row_cols[3].markdown(f"<div class='appt-row {row_class}'>{row['appointment_date'].date()}</div>", unsafe_allow_html=True)
        row_cols[4].markdown(f"<div class='appt-row {row_class}'>{row['appointment_time']}<br>{row['reason'][:50]}{'...' if len(row['reason']) > 50 else ''}</div>", unsafe_allow_html=True)
        row_cols[5].markdown(f"<div class='appt-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)

        if not is_responded:
            if row_cols[6].button("Reply", key=f"respond_btn_{row['id']}"):
                st.session_state["active_appointment_row"] = row.to_dict()  # <-- convert to dict
                respond_dialog()
        else:
            row_cols[6].markdown(f"<div class='appt-row {row_class}'>✅</div>", unsafe_allow_html=True)

# ------------------- Main -------------------
def main():
    # Ensure responder_name is set
    if "responder_name" not in st.session_state:
        username = st.session_state.get("user_name")
        full_name = get_full_name_from_username(username)

        st.session_state["responder_name"] = full_name or username or "Unknown"

    set_full_page_background('images/black_strip.jpg')
    st.write('---')
    view_appointments()

if __name__ == "__main__":
    main()
