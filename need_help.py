DB_PATH = "users_db.db"

import streamlit as st
import pandas as pd
import sqlite3

import base64, os
from datetime import datetime
import calendar


# ----------------- Background Setup -----------------
def set_full_page_background(image_path):
    if not os.path.exists(image_path):
        st.error(f"Image file '{image_path}' not found.")
        return
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
        <style>
        [data-testid="stApp"] {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)


# ----------------- DB Utilities -----------------
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def update_need_help_response(msg_id, response, response_date, response_time, responder_name):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE messages_table
        SET response = ?, response_date = ?, response_time = ?, responder = ?
        WHERE id = ?
    """, (response, response_date, response_time, responder_name, msg_id))
    conn.commit()
    conn.close()



@st.dialog("Respond to Message")
def respond_to_message():
    row = st.session_state.get("active_message_row")
    responder_name = st.session_state.get("responder_name")

    if row is not None:
        st.write(f"📩 Message from **{row['name']}** on **{row['sent_date']} {row['sent_time']}**")
        st.info(row['message'])
        response = st.text_area("Your Response", key=f"response_input_{row['id']}")
        if st.button("✅ Submit", key=f"submit_response_{row['id']}"):
            if response.strip():
                conn = create_connection()
                cursor = conn.cursor()
                now = datetime.now()
                cursor.execute("""
                    UPDATE messages_table SET response = ?, response_date = ?, response_time = ?, responder = ?
                    WHERE id = ?
                """, (response.strip(), now.date(), now.time().strftime('%H:%M:%S'), responder_name, row['id']))
                conn.commit()
                conn.close()
                st.success("✅ Response submitted successfully.")
                st.session_state["active_message_row"] = None
                st.rerun()
            else:
                st.warning("⚠️ Please enter a response before submitting.")

# def view_messages():
    
#     conn = create_connection()
#     df = pd.read_sql_query("""
#         SELECT id, name, email, contact, client_type, message, sent_date, sent_time, response, response_date, response_time, responder
#         FROM messages_table
#         ORDER BY sent_date DESC, sent_time DESC
#     """, conn)
#     conn.close()

#     # Check if empty before processing
#     if df.empty:
#         st.info("No messages found in the database.")
#         return




#     st.write(df)

#     # Ensure sent_date and sent_time are not null/empty
#     df = df[df['sent_date'].notnull() & df['sent_time'].notnull()]

#     try:
#         df["sent_at"] = pd.to_datetime(df["sent_date"] + ' ' + df["sent_time"])
#     except Exception as e:
#         st.error(f"Date parsing error: {e}")
#         return

#     # Sidebar Filters
#     with st.sidebar.expander('📅 Filter Messages by Date', expanded=True):
#         if df.empty:
#             st.warning("No data available for filtering.")
#             return

#         all_years = sorted(df["sent_at"].dt.year.unique(), reverse=True)
#         selected_years = st.multiselect("Select Year(s)", options=all_years, default=all_years)

#         df = df[df["sent_at"].dt.year.isin(selected_years)]

#         if df.empty:
#             st.info("No messages found for selected year(s).")
#             return

#         available_months = sorted(df["sent_at"].dt.month.unique())
#         month_names = [calendar.month_name[m] for m in available_months]
#         selected_month_names = st.multiselect("Select Month(s)", options=month_names, default=month_names)
#         selected_months = [list(calendar.month_name).index(m) for m in selected_month_names]

#         df = df[df["sent_at"].dt.month.isin(selected_months)]

#         if df.empty:
#             st.info("No messages found for selected month(s).")
#             return

#         min_date = df["sent_at"].min()
#         max_date = df["sent_at"].max()

#         start_date = st.date_input("Start Date", value=min_date.date(), min_value=min_date.date(), max_value=max_date.date())
#         end_date = st.date_input("End Date", value=max_date.date(), min_value=min_date.date(), max_value=max_date.date())

#         df = df[(df["sent_at"] >= pd.to_datetime(start_date)) & (df["sent_at"] <= pd.to_datetime(end_date))]
#     if df.empty:
#         st.info("No messages found for selected filters.")
#         return
#     st.markdown("""
#     <style>
#         .message-header { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
#         .message-row { padding: 8px; border-radius: 5px; }
#         .row-even { background-color: #2c2c2c; }
#         .row-odd { background-color: #1e1e1e; }
#         .responded { color: #2ecc71; font-weight: bold; }
#         .pending { color: #f39c12; font-weight: bold; }
#     </style>
#     """, unsafe_allow_html=True)

#     with st.expander("📬 USER MESSAGES", expanded=True):
#         headers = ["Name", "Email", "Contact", "Client Type", "Message", "Sent At", "Response", "Reply Date", "Responder", "Action"]
#         header_cols = st.columns([1.5, 2, 2, 1.5, 3, 2, 2.5, 2, 1.5, 1])
#         for col, title in zip(header_cols, headers):
#             col.markdown(f"<div class='message-header'>{title}</div>", unsafe_allow_html=True)

#         for i, row in df.iterrows():
#             row_class = 'row-even' if i % 2 == 0 else 'row-odd'
#             responded = bool(row['response']) and row['response'].strip() != ""
#             response_display = f"<span class='responded'>{row['response']}</span>" if responded else "<span class='pending'>Pending</span>"
#             reply_date_display = f"{row['response_date']} {row['response_time']}" if responded else "-"

#             row_cols = st.columns([1.5, 2, 2, 1.5, 3, 2, 2.5, 2, 1.5, 1])
#             row_cols[0].markdown(f"<div class='message-row {row_class}'>{row['name']}</div>", unsafe_allow_html=True)
#             row_cols[1].markdown(f"<div class='message-row {row_class}'>{row['email']}</div>", unsafe_allow_html=True)
#             row_cols[2].markdown(f"<div class='message-row {row_class}'>{row['contact']}</div>", unsafe_allow_html=True)
#             row_cols[3].markdown(f"<div class='message-row {row_class}'>{row['client_type']}</div>", unsafe_allow_html=True)
#             row_cols[4].markdown(f"<div class='message-row {row_class}'>{row['message'][:100]}{'...' if len(row['message']) > 100 else ''}</div>", unsafe_allow_html=True)
#             row_cols[5].markdown(f"<div class='message-row {row_class}'>{row['sent_date']} {row['sent_time']}</div>", unsafe_allow_html=True)
#             row_cols[6].markdown(f"<div class='message-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)
#             row_cols[7].markdown(f"<div class='message-row {row_class}'>{reply_date_display}</div>", unsafe_allow_html=True)
#             row_cols[8].markdown(f"<div class='message-row {row_class}'>{row['responder'] or '-'}</div>", unsafe_allow_html=True)

#             if not responded:
#                 if row_cols[9].button("Reply", key=f"reply_btn_{row['id']}"):
#                     st.session_state["active_message_row"] = row
#                     respond_to_message()
#             else:
#                 row_cols[9].markdown(f"<div class='message-row {row_class}'>✅</div>", unsafe_allow_html=True)



# def view_messages():
#     set_full_page_background("images/black_strip.jpg")
#     conn = create_connection()
#     cursor = conn.cursor()
#     try:
#         query = """
#             SELECT name, email, contact, client_type, message, sent_date, sent_time, response, response_date, response_time, responder
#             FROM messages_table
#             ORDER BY sent_date DESC, sent_time DESC
#         """
#         df = pd.read_sql_query(query, conn)
#         df["sent_at"] = pd.to_datetime(df["sent_date"] + " " + df["sent_time"])
#         df["response_at"] = df["response_date"].fillna("") + " " + df["response_time"].fillna("")

#         if df.empty:
#             st.warning("No messages found.")
#             return

#         # Sidebar filters
#         st.sidebar.header("Filter Messages")
#         years = df["sent_date"].apply(lambda x: pd.to_datetime(x).year).unique()
#         selected_year = st.sidebar.selectbox("Select Year", sorted(years, reverse=True))
#         df = df[df["sent_date"].apply(lambda x: pd.to_datetime(x).year) == selected_year]

#         months = df["sent_date"].apply(lambda x: pd.to_datetime(x).month).unique()
#         month_names = {i: pd.to_datetime(f'2025-{i:02}-01').strftime('%B') for i in range(1, 13)}
#         selected_month = st.sidebar.selectbox("Select Month", sorted(months), format_func=lambda x: month_names[x])
#         df = df[df["sent_date"].apply(lambda x: pd.to_datetime(x).month) == selected_month]

#         min_date = pd.to_datetime(df["sent_date"]).min()
#         max_date = pd.to_datetime(df["sent_date"]).max()
#         start_date = st.sidebar.date_input("Start Date", value=min_date.date(), min_value=min_date.date(), max_value=max_date.date())
#         end_date = st.sidebar.date_input("End Date", value=max_date.date(), min_value=min_date.date(), max_value=max_date.date())

#         start_dt = pd.to_datetime(start_date)
#         end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
#         df = df[(df["sent_at"] >= start_dt) & (df["sent_at"] <= end_dt)]

#         if df.empty:
#             st.warning("No messages found for selected filters.")
#             return

#         # Display messages
#         st.markdown("""
#         <style>
#             .message-table {
#                 width: 100%;
#                 border-collapse: collapse;
#                 color: white;
#                 font-size: 15px;
#             }
#             .message-table th, .message-table td {
#                 border: 1px solid #444;
#                 padding: 8px;
#                 text-align: left;
#             }
#             .message-table th {
#                 background-color: #222;
#                 color: orange;
#             }
#             .message-table tr:nth-child(even) {
#                 background-color: #333;
#             }
#             .message-table tr:hover {
#                 background-color: #444;
#             }
#             .reply-btn {
#                 background-color: red;
#                 color: white;
#                 padding: 4px 10px;
#                 border: none;
#                 border-radius: 4px;
#                 text-align: center;
#                 cursor: pointer;
#             }
#         </style>
#         """, unsafe_allow_html=True)

#         st.markdown("<h4 style='color:white;'>Messages Table</h4>", unsafe_allow_html=True)
#         table_html = """
#         <table class='message-table'><thead><tr>
#                     <th>Name</th>
#                     <th>Email</th>
#                     <th>Contact</th>
#                     <th>Client Type</th>
#                     <th>Message</th>
#                     <th>Sent At</th>
#                     <th>Response</th>
#                     <th>Response At</th>
#                     <th>Responder</th>
#                     <th>Action</th>
#                 </tr>
#             </thead>
#             <tbody>
#         """

#         for index, row in df.iterrows():
#             sent_at = pd.to_datetime(row["sent_date"] + " " + row["sent_time"]).strftime("%d %b %Y, %I:%M %p")
#             response_at = ""
#             if row["response_date"] and row["response_time"]:
#                 try:
#                     response_at = pd.to_datetime(row["response_date"] + " " + row["response_time"]).strftime("%d %b %Y, %I:%M %p")
#                 except:
#                     response_at = f"{row['response_date']} {row['response_time']}"
#             response_display = row["response"] if row["response"] else "No response yet"
#             table_html += f"""<tr><td>{row['name']}</td>
#                     <td>{row['email']}</td>
#                     <td>{row['contact']}</td>
#                     <td>{row['client_type']}</td>
#                     <td>{row['message']}</td>
#                     <td>{sent_at}</td>
#                     <td>{response_display}</td>
#                     <td>{response_at}</td>
#                     <td>{row['responder'] if row['responder'] else '-'}</td>
#                     <td><a href='#reply-{index}' class='reply-btn'>Reply</a></td>
#                 </tr>
#             """
#         table_html += "</tbody></table>"
#         st.markdown(table_html, unsafe_allow_html=True)

#     except Exception as e:
#         st.error(f"Error loading messages: {e}")
#     finally:
#         conn.close()

# def view_messages():
#     conn = create_connection()
#     df = pd.read_sql_query("""
#         SELECT id, name, email, contact, client_type, message, sent_date, sent_time, response, response_date, response_time, responder
#         FROM messages_table
#         ORDER BY sent_date DESC, sent_time DESC
#     """, conn)
#     conn.close()

#     if df.empty:
#         st.info("No messages found for selected filters.")
#         return

#     # Styling
#     st.markdown("""
#     <style>
#         .message-header { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
#         .message-row { padding: 8px; border-radius: 5px; }
#         .row-even { background-color: #2c2c2c; }
#         .row-odd { background-color: #1e1e1e; }
#         .responded { color: #2ecc71; font-weight: bold; }
#         .pending { color: #f39c12; font-weight: bold; }
#     </style>
#     """, unsafe_allow_html=True)

#     with st.expander("📬 USER MESSAGES", expanded=True):
#         headers = ["Name", "Email", "Contact", "Client Type", "Message", "Sent At", "Response", "Reply Date", "Responder", "Action"]
#         header_cols = st.columns([1.5, 2, 2, 1.5, 3, 2, 2.5, 2, 1.5, 1])
#         for col, title in zip(header_cols, headers):
#             col.markdown(f"<div class='message-header'>{title}</div>", unsafe_allow_html=True)

#         for i, row in df.iterrows():
#             row_class = 'row-even' if i % 2 == 0 else 'row-odd'
#             responded = bool(row['response']) and row['response'].strip() != ""
#             response_display = f"<span class='responded'>{row['response']}</span>" if responded else "<span class='pending'>Pending</span>"
#             reply_date_display = f"{row['response_date']} {row['response_time']}" if responded else "-"

#             row_cols = st.columns([1.5, 2, 2, 1.5, 3, 2, 2.5, 2, 1.5, 1])
#             row_cols[0].markdown(f"<div class='message-row {row_class}'>{row['name']}</div>", unsafe_allow_html=True)
#             row_cols[1].markdown(f"<div class='message-row {row_class}'>{row['email']}</div>", unsafe_allow_html=True)
#             row_cols[2].markdown(f"<div class='message-row {row_class}'>{row['contact']}</div>", unsafe_allow_html=True)
#             row_cols[3].markdown(f"<div class='message-row {row_class}'>{row['client_type']}</div>", unsafe_allow_html=True)
#             row_cols[4].markdown(f"<div class='message-row {row_class}'>{row['message'][:100]}{'...' if len(row['message']) > 100 else ''}</div>", unsafe_allow_html=True)
#             row_cols[5].markdown(f"<div class='message-row {row_class}'>{row['sent_date']} {row['sent_time']}</div>", unsafe_allow_html=True)
#             row_cols[6].markdown(f"<div class='message-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)
#             row_cols[7].markdown(f"<div class='message-row {row_class}'>{reply_date_display}</div>", unsafe_allow_html=True)
#             row_cols[8].markdown(f"<div class='message-row {row_class}'>{row['responder'] or '-'}</div>", unsafe_allow_html=True)

#             if not responded:
#                 if row_cols[9].button("Reply", key=f"reply_btn_{row['id']}"):
#                     st.session_state["active_message_row"] = row
#                     st.session_state["show_reply_dialog"] = True

#             else:
#                 row_cols[9].markdown(f"<div class='message-row {row_class}'>✅</div>", unsafe_allow_html=True)

    # Show the reply dialog if triggered
    # if st.session_state.get("show_reply_dialog"):
    #     show_reply_dialog()

def view_messages():
    import calendar  # make sure calendar is imported
    
    conn = create_connection()
    df = pd.read_sql_query("""
        SELECT id, name, email, contact, client_type, message, sent_date, sent_time, response, response_date, response_time, responder
        FROM messages_table
        ORDER BY sent_date DESC, sent_time DESC
    """, conn)
    conn.close()

    if df.empty:
        st.info("No messages found for selected filters.")
        return

    # Combine date and time columns into datetime
    df = df[df['sent_date'].notnull() & df['sent_time'].notnull()]
    df['sent_at'] = pd.to_datetime(df['sent_date'] + ' ' + df['sent_time'])

    # Sidebar filters cumulative
    with st.sidebar.expander('📅 Filter Messages by Date', expanded=True):
        # Year filter
        all_years = sorted(df['sent_at'].dt.year.unique(), reverse=True)
        selected_years = st.multiselect("Select Year(s)", options=all_years, default=all_years)
        if not selected_years:
            st.warning("Select at least one year.")
            return
        df = df[df['sent_at'].dt.year.isin(selected_years)]

        # Month filter based on selected years
        available_months = sorted(df['sent_at'].dt.month.unique())
        month_names = [calendar.month_name[m] for m in available_months]
        selected_month_names = st.multiselect("Select Month(s)", options=month_names, default=month_names)
        if not selected_month_names:
            st.warning("Select at least one month.")
            return
        selected_months = [list(calendar.month_name).index(m) for m in selected_month_names]
        df = df[df['sent_at'].dt.month.isin(selected_months)]

        # Date range filter based on selected year(s) and month(s)
        min_date = df['sent_at'].dt.date.min()
        max_date = df['sent_at'].dt.date.max()
        start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

        if start_date > end_date:
            st.warning("Start date must be before or equal to end date.")
            return

        df = df[(df['sent_at'].dt.date >= start_date) & (df['sent_at'].dt.date <= end_date)]

    if df.empty:
        st.info("No messages found for selected filters.")
        return

    # Styling
    st.markdown("""
    <style>
        .message-header { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
        .message-row { padding: 8px; border-radius: 5px; }
        .row-even { background-color: #2c2c2c; }
        .row-odd { background-color: #1e1e1e; }
        .responded { color: #2ecc71; font-weight: bold; }
        .pending { color: #f39c12; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    with st.expander("📬 MESSAGES", expanded=True):
        headers = ["Name", "Email", "Contact", "Message", "Sent At", "Response", "Reply Date", "Action"]
        header_cols = st.columns([1.5, 2, 2, 3, 2, 2.5, 2, 1.5])
        for col, title in zip(header_cols, headers):
            col.markdown(f"<div class='message-header'>{title}</div>", unsafe_allow_html=True)

        for i, row in df.iterrows():
            row_class = 'row-even' if i % 2 == 0 else 'row-odd'
            responded = bool(row['response']) and row['response'].strip() != ""
            response_display = f"<span class='responded'>{row['response']}</span>" if responded else "<span class='pending'>Pending</span>"
            reply_date_display = f"{row['response_date']} {row['response_time']}" if responded else "-"

            row_cols = st.columns([1.5, 2, 2, 3, 2, 2.5, 2, 1.5])
            row_cols[0].markdown(f"<div class='message-row {row_class}'>{row['name']}</div>", unsafe_allow_html=True)
            row_cols[1].markdown(f"<div class='message-row {row_class}'>{row['email']}</div>", unsafe_allow_html=True)
            row_cols[2].markdown(f"<div class='message-row {row_class}'>{row['contact']}</div>", unsafe_allow_html=True)
            # row_cols[3].markdown(f"<div class='message-row {row_class}'>{row['client_type']}</div>", unsafe_allow_html=True)
            row_cols[3].markdown(f"<div class='message-row {row_class}'>{row['message'][:100]}{'...' if len(row['message']) > 100 else ''}</div>", unsafe_allow_html=True)
            row_cols[4].markdown(f"<div class='message-row {row_class}'>{row['sent_date']} {row['sent_time']}</div>", unsafe_allow_html=True)
            row_cols[5].markdown(f"<div class='message-row {row_class}'>{response_display}</div>", unsafe_allow_html=True)
            row_cols[6].markdown(f"<div class='message-row {row_class}'>{reply_date_display}</div>", unsafe_allow_html=True)
            # row_cols[8].markdown(f"<div class='message-row {row_class}'>{row['responder'] or '-'}</div>", unsafe_allow_html=True)

            if not responded:
                if row_cols[7].button("Reply", key=f"reply_btn_{row['id']}"):
                    st.session_state["active_message_row"] = row
                    st.session_state["show_reply_dialog"] = True

            else:
                row_cols[7].markdown(f"<div class='message-row {row_class}'>✅</div>", unsafe_allow_html=True)
    if st.session_state.get("show_reply_dialog"):
        show_reply_dialog()

@st.dialog("Respond to Message")
def show_reply_dialog():
    row = st.session_state.get("active_message_row")
    responder_name = st.session_state.get("responder_name", "Unknown")

    if row is None:
        st.warning("No message selected to reply to.")
        return

    st.markdown(f"### Replying to message from **{row['name']}** sent on **{row['sent_date']} {row['sent_time']}**")
    st.info(row['message'])

    response_text = st.text_area("Your Response:", key="response_text_area")

    if st.button("Submit Response"):
        if not response_text.strip():
            st.warning("Please enter a response before submitting.")
            return

        # Update DB with response and current date/time
        conn = create_connection()
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute("""
            UPDATE messages_table
            SET response = ?, response_date = ?, response_time = ?, responder = ?
            WHERE id = ?
        """, (response_text.strip(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), responder_name, row["id"]))
        conn.commit()
        conn.close()
        st.success("Response submitted successfully.")
        st.session_state["show_reply_dialog"] = False
        st.session_state["active_message_row"] = None
        st.rerun()

def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def main():
    username = st.session_state.get("user_name")
    full_name = get_full_name_from_username(username)
    st.session_state["responder_name"] = full_name or username or "Unknown"
    set_full_page_background('images/black_strip.jpg')
    view_messages()

if __name__ == '__main__':
    main()
