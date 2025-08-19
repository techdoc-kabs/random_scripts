DB_PATH = "users_db.db"
import streamlit as st
import pandas as pd
import sqlite3

from datetime import datetime
import os, base64 

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

def update_feedback_response(feedback_id, response, responder_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE feedbacks
        SET response = ?, responded_at = ?, responder = ?
        WHERE id = ?
    """, (response, datetime.now(), responder_name, feedback_id))
    conn.commit()
    conn.close()


import calendar
# Dialog box for responding
@st.dialog("Feedback Response")
def respond_dialog():
    row = st.session_state.get("active_feedback_row")
    responder_name = st.session_state.get("responder_name")

    if row is not None:
        st.write(f"🗨️ Feedback from **{row['name']}** on **{row['sent_at']}**")
        st.info(row['message'])

        response = st.text_area("Your Response", key=f"response_input_{row['id']}")
        if st.button("✅ Submit", key=f"submit_response_{row['id']}"):
            if response.strip():
                update_feedback_response(row['id'], response.strip(), responder_name)
                st.success("✅ Response submitted successfully.")
                st.session_state["active_feedback_row"] = None
                st.rerun()
            else:
                st.warning("⚠️ Please enter a response before submitting.")

# Display feedback in table format
def view_feedback():
    conn = create_connection()
    df = pd.read_sql_query("SELECT id, name, message, sent_at, response, responded_at, responder FROM feedbacks ORDER BY sent_at DESC", conn)
    conn.close()

    df["sent_at"] = pd.to_datetime(df["sent_at"])

    with st.sidebar.expander('📅 Filter Feedback by Date', expanded=True):
        # Step 1: Select Year(s)
        all_years = sorted(df["sent_at"].dt.year.unique(), reverse=True)
        selected_years = st.multiselect("Select Year(s)", options=all_years, default=all_years)

        # Step 2: Filter by selected years
        df_filtered_by_year = df[df["sent_at"].dt.year.isin(selected_years)]

        # Step 3: Select Month(s)
        available_months = sorted(df_filtered_by_year["sent_at"].dt.month.unique())
        month_names = [calendar.month_name[m] for m in available_months]
        selected_month_names = st.multiselect("Select Month(s)", options=month_names, default=month_names)
        selected_months = [list(calendar.month_name).index(m) for m in selected_month_names]

        # Step 4: Filter by selected months
        df_filtered = df_filtered_by_year[df_filtered_by_year["sent_at"].dt.month.isin(selected_months)]

        # Step 5: Select Date Range (your own choice)
        min_date = df_filtered["sent_at"].min()
        max_date = df_filtered["sent_at"].max()

        start_date = st.date_input("Choose Start Date", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("Choose End Date", value=max_date, min_value=min_date, max_value=max_date)

        # Final filter
        df_filtered = df_filtered[(df_filtered["sent_at"] >= pd.to_datetime(start_date)) &
                                  (df_filtered["sent_at"] <= pd.to_datetime(end_date))]


        



    if df.empty:
        st.info("No feedback found.")
        return

    responder_name = st.session_state.get("responder_name", "Unknown")

    st.markdown("""
    <style>
        .feedback-header {
            background-color: #1565c0;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        }
        .feedback-row {
            padding: 8px;
            border-radius: 5px;
        }
        .row-even { background-color: #2c2c2c; }
        .row-odd { background-color: #1e1e1e; }
        .responder-name { color: #81c784; font-weight: bold; }
        .no-response { color: #f39c12; font-weight: bold; }
        .responded { color: #2ecc71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    with st.expander("📝 USER FEEDBACK", expanded=True):
        header_cols = st.columns([2, 3, 2, 4, 2, 1.5])
        header_titles = ["Name", "Message", "Sent_At", "Response", "Reply_date", "Action"]
        for col, title in zip(header_cols, header_titles):
            col.markdown(f"<div class='feedback-header'>{title}</div>", unsafe_allow_html=True)

        for i, row in df.iterrows():
            row_class = 'row-even' if i % 2 == 0 else 'row-odd'
            is_responded = bool(row['response']) and row['response'].strip() != ""
            response_display = (
                f"<span class='responded'>{row['response']}</span>"
                if is_responded else "<span class='no-response'>Pending</span>"
            )
            responded_at_display = row['responded_at'] if row['responded_at'] else "-"

            row_cols = st.columns([2, 3, 2, 4, 2, 1.5])
            row_cols[0].markdown(f"<div class='feedback-row {row_class}'>{row['name']}</div>", unsafe_allow_html=True)
            row_cols[1].markdown(f"<div class='feedback-row {row_class}'>{row['message'][:120]}{'...' if len(row['message']) > 120 else ''}</div>", unsafe_allow_html=True)
            row_cols[2].markdown(f"<div class='feedback-row {row_class}'>{row['sent_at']}</div>", unsafe_allow_html=True)
            row_cols[3].markdown(f"<div class='feedback-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)
            row_cols[4].markdown(f"<div class='feedback-row {row_class}'>{responded_at_display}</div>", unsafe_allow_html=True)

            if not is_responded:
                if row_cols[5].button("Reply", key=f"respond_btn_{row['id']}"):
                    st.session_state["active_feedback_row"] = row
                    respond_dialog()
            else:
                row_cols[5].markdown(f"<div class='feedback-row {row_class}'>✅</div>", unsafe_allow_html=True)

# Get full name from username
def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Entry point
def main():
    username = st.session_state.get("user_name")
    full_name = get_full_name_from_username(username)

    responder_name = full_name or username or "Unknown"
    st.session_state["responder_name"] = responder_name  # Set globally

    set_full_page_background('images/black_strip.jpg')
    view_feedback()

if __name__ == '__main__':
    main()
