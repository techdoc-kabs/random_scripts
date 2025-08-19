import sqlite3

import json
from datetime import datetime
import streamlit as st
import os, base64
import pandas as pd
import threading
from pushbullet import Pushbullet
import smtplib
from email.message import EmailMessage
import calendar


API_KEY = st.secrets["push_API_KEY"]
pb = Pushbullet(API_KEY)
DB_PATH = "users_db.db"


def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None


def assign_tools_to_screen(appointment_id, user_id, created_by, tools_to_assign, scheduled_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT screening_tools FROM appointments WHERE appointment_id = ?", (appointment_id,))
    row = cursor.fetchone()

    if row:
        current_tools = json.loads(row[0]) if row[0] else {}

        new_tools_added = 0
        skipped_tools = 0

        for tool in tools_to_assign:
            if tool in current_tools:
                skipped_tools += 1
                continue
            current_tools[tool] = {
                "status": "Pending",
                "response_date": None,
                "scheduled_date": scheduled_date
            }
            new_tools_added += 1

        cursor.execute("""
            UPDATE appointments SET screening_tools = ? WHERE appointment_id = ?
        """, (json.dumps(current_tools), appointment_id))
        conn.commit()
        conn.close()
        return new_tools_added, skipped_tools

    else:
        tools_dict = {
            tool: {
                "status": "Pending",
                "response_date": None,
                "scheduled_date": scheduled_date
            } for tool in tools_to_assign
        }
        cursor.execute("""
            INSERT INTO appointments (
                appointment_id, user_id, created_by, screening_tools
            ) VALUES (?, ?, ?, ?)
        """, (
            appointment_id,
            user_id,
            created_by,
            json.dumps(tools_dict)
        ))
        conn.commit()
        conn.close()
        return len(tools_to_assign), 0



def initialize_session_vars():
    defaults = {
        'appointment_id': None,
        'user_id': None,
        'name': None,
        'client_type': None,
        'username': "SELF"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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


def search_pending_screens_by_name(db, client_type, screen_type, search_input):
    cursor = db.cursor()
    name_parts = search_input.strip().split()
    query_conditions = [
        "status = 'Pending'",
        "client_type = ?",
        "screen_type = ?"]
    params = [client_type, screen_type]
    if len(name_parts) == 2:
        query_conditions.append("(name LIKE ? OR name LIKE ?)")
        first_name, last_name = name_parts
        params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
    else:
        query_conditions.append("name LIKE ?")
        params.append(f"%{search_input.strip()}%")
    query = f"""
        SELECT appointment_id, name, created_at
        FROM appointments
        WHERE {" AND ".join(query_conditions)}
        ORDER BY created_at DESC"""
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    return results


def fetch_screen_tools(appointment_id, db):
    cursor = db.cursor()
    cursor.execute("""
        SELECT appointment_id, name, screen_type, class, stream, term, client_type, screening_tools
        FROM appointments
        WHERE appointment_id = ?
    """, (appointment_id,))
    rows = cursor.fetchall()
    cursor.close()

    records = []
    for row in rows:
        try:
            tools_dict = json.loads(row[7]) if row[7] else {}
        except Exception as e:
            st.warning(f"Failed to parse screening_tools for appointment_id {row[0]}: {e}")
            tools_dict = {}

        for tool, details in tools_dict.items():
            status = details.get("status", "Pending")
            response_date = details.get("response_date")
            scheduled_date = details.get("scheduled_date")
            records.append({
                'appointment_id': row[0],
                "name": row[1],
                "screen_type": row[2],
                "class": row[3],
                "stream": row[4],
                "term": row[5],
                "client_type": row[6],
                "tool": tool,
                "status": status,
                "response_date": response_date,
                "scheduled_date": scheduled_date
            })

    return pd.DataFrame(records)


#### notifications #######
def fetch_user_email_by_name(name):
    conn = create_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        query = "SELECT email FROM users WHERE full_name = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def fetch_user_contact_by_name(name):
    conn = create_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        query = "SELECT contact FROM users WHERE full_name = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def send_email(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['To'] = to  
    user = st.secrets['U']
    msg['From'] = user
    password = st.secrets['SECRET']
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        st.success(f"📧 Email notification sent to {to}")
    except Exception as e:
        st.error(f"Error sending email: {e}")


def send_sms_notification(phone_number, message):
    st.warning("⚠️ SMS sending not implemented yet. Integrate an API like Twilio.")
    return


def send_email_notification(name, tools, date, email):
    subject = "🔔 Screening Tools Assigned"
    body = (f"Dear {name},\n\n"
            f"You have been assigned the following screening tools to complete:\n"
            f"{''.join(tools)}\n\n"
            f"Activity created on: {date}\n\n"
            f"Please ensure you complete them on time.\n\n"
            f"Best regards,\n"
            f"PUKKA PSYCHOMETRIC & PSYCHOLOGICAL SERVICES ")
    
    send_email(subject, body, email)


def send_notifications(name, tools, date):
    message = (f'Dear {name} !! \n'
               f'You have {tools} to fill \n'
               f'Scheduled on: {date}\n'
               f'Please ignore this message if already attended to') 

    threading.Thread(target=pb.push_note, args=("🔔 TODO Alert", message)).start()
    student_email = fetch_user_email_by_name(name)
    
    if student_email:
        send_email_notification(name, tools, date, student_email)
    phone_number = fetch_user_contact_by_name(name)
    if phone_number:
        send_sms_notification(phone_number, message)


def remove_requested_tool(db, appointment_id, tool_to_remove):
    cursor = db.cursor()
    cursor.execute("""
        SELECT screening_tools
        FROM appointments
        WHERE appointment_id = ?
    """, (appointment_id,))
    result = cursor.fetchone()
    if not result:
        st.error("No matching record found.")
        return
    try:
        tools_dict = json.loads(result[0]) if result[0] else {}
    except Exception as e:
        st.error(f"Error parsing screening_tools data: {e}")
        return

    if tool_to_remove not in tools_dict:
        st.warning(f"Tool '{tool_to_remove}' not found.")
        return

    if tools_dict[tool_to_remove].get("status") == "Completed":
        st.warning(f"Tool '{tool_to_remove}' is marked as Completed and cannot be removed.")
        return

    tools_dict.pop(tool_to_remove, None)
    updated_tools_json = json.dumps(tools_dict)

    cursor.execute("""
        UPDATE appointments
        SET screening_tools = ?
        WHERE appointment_id = ?
    """, (updated_tools_json, appointment_id))
    db.commit()
    cursor.close()
    st.success(f"✅ Tool '{tool_to_remove}' was successfully removed.")


def screen_type_exists_for_appointment(db, appointment_id, screen_type):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 1 FROM appointments
        WHERE appointment_id = ? AND screen_type = ?
        LIMIT 1
    """, (appointment_id, screen_type))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def is_pre_screen_completed(db, appointment_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT status FROM appointments
        WHERE appointment_id = ? AND screen_type = 'PRE-SCREEN'
    """, (appointment_id,))
    row = cursor.fetchone()
    cursor.close()
    return row and row[0] == "Completed"


def get_available_screen_types(db, appointment_id):
    used_types = pd.read_sql("SELECT DISTINCT screen_type FROM appointments WHERE appointment_id = ?", db, params=[appointment_id])['screen_type'].tolist()
    possible = ["PRE-SECREEN", "POST-SCREEN",'ON-CONSULT','ON-REQUEST']  # or dynamic from DB
    return [s for s in possible if s not in used_types]
# def get_date_range_sidebar(db, available_years, default_years):
#     """Handles year, month, and date range selection safely within the sidebar."""
#     selected_years = st.multiselect("Year(s)", available_years, default=default_years)

#     # --- MONTH SELECTION ---
#     if selected_years:
#         years_str = ','.join(f"'{y:04d}'" for y in selected_years)
#         month_query = f"""
#             SELECT DISTINCT strftime('%m', appointment_date) AS month 
#             FROM appointments 
#             WHERE appointment_date IS NOT NULL
#             AND strftime('%Y', appointment_date) IN ({years_str})
#         """
#         month_df = pd.read_sql(month_query, db)
#         available_month_nums = sorted([int(m) for m in month_df['month'].dropna().unique()])
#         available_months = [calendar.month_name[m] for m in available_month_nums]
#     else:
#         available_month_nums = []
#         available_months = []

#     selected_months = st.multiselect("Month(s)", available_months, default=available_months)

#     # --- DATE RANGE CALCULATION ---
#     if selected_years and selected_months:
#         month_nums_selected = [list(calendar.month_name).index(m) for m in selected_months]
#         years_str = ','.join(f"'{y:04d}'" for y in selected_years)
#         months_str = ','.join(f"'{m:02d}'" for m in month_nums_selected)

#         date_range_query = f"""
#             SELECT MIN(date(appointment_date)) as min_date, MAX(date(appointment_date)) as max_date
#             FROM appointments
#             WHERE appointment_date IS NOT NULL
#             AND strftime('%Y', appointment_date) IN ({years_str})
#             AND strftime('%m', appointment_date) IN ({months_str})
#         """
#         date_range_df = pd.read_sql(date_range_query, db)
#     else:
#         date_range_df = pd.read_sql("""
#             SELECT MIN(date(appointment_date)) as min_date, MAX(date(appointment_date)) as max_date
#             FROM appointments
#             WHERE appointment_date IS NOT NULL
#         """, db)

#     min_date = pd.to_datetime(date_range_df.at[0, 'min_date'])
#     max_date = pd.to_datetime(date_range_df.at[0, 'max_date'])
#     today = datetime.today().date()

#     # --- SAFETY CHECKS ---
#     if pd.isnull(min_date) or pd.isnull(max_date):
#         min_date = pd.Timestamp(today)
#         max_date = pd.Timestamp(today)

#     # default_start = max(min_date.date(), today)
#     # default_end = max(default_start, max_date.date())

#     # selected_date_range = st.date_input(
#     #     "Date Range (Start - End)",
#     #     value=(default_start, default_end),
#     #     min_value=min_date.date(),
#     #     max_value=max_date.date()
#     # )
#     min_d = min_date.date()
#     max_d = max_date.date()

#     # Ensure defaults are within allowed range
#     default_start = min(max(today, min_d), max_d)
#     default_end = max(default_start, min(max_d, today))

#     selected_date_range = st.date_input(
#         "Date Range (Start - End)",
#         value=(default_start, default_end),
#         min_value=min_d,
#         max_value=max_d
#     )


#     return selected_years, selected_months, selected_date_range


# # def main():
# #     set_full_page_background('images/black_strip.jpg')
# #     db = create_connection()

# #     bulk_mode = st.toggle("Bulk Assign Mode", value=True)
# #     tools_list = ["PHQ-4", "PHQ-9", "GAD-7", 'CAPS-14','SSQ','HSQ','SNAP-IV-C', "DASS-21", 'BDI', "SRQ"]
# #     client_types = pd.read_sql("SELECT DISTINCT client_type FROM appointments", db)['client_type'].dropna().tolist()
# #     terms = pd.read_sql("SELECT DISTINCT term FROM appointments", db)['term'].dropna().tolist()
# #     screen_types = pd.read_sql("SELECT DISTINCT screen_type FROM appointments", db)['screen_type'].dropna().tolist()

# #     year_df = pd.read_sql("SELECT DISTINCT strftime('%Y', appointment_date) AS year FROM appointments WHERE appointment_date IS NOT NULL", db)
# #     available_years = sorted([int(y) for y in year_df['year'].dropna().unique()])
# #     current_year = datetime.now().year
# #     default_years = [current_year] if current_year in available_years else available_years[:1]

# #     with st.sidebar.expander('FILTER OPTIONS', expanded=True):
# #         selected_client_type = st.selectbox("Client Type", client_types)
# #         selected_screen_type = st.selectbox("Screen Type", screen_types)
# #         selected_term = st.selectbox("Term", terms)
# #         selected_years = st.multiselect("Year(s)", available_years, default=default_years)

# #         if selected_years:
# #             years_str = ','.join(f"'{y:04d}'" for y in selected_years)
# #             month_query = f"""
# #                 SELECT DISTINCT strftime('%m', appointment_date) AS month 
# #                 FROM appointments 
# #                 WHERE appointment_date IS NOT NULL
# #                 AND strftime('%Y', appointment_date) IN ({years_str})
# #             """
# #             month_df = pd.read_sql(month_query, db)
# #             available_month_nums = sorted([int(m) for m in month_df['month'].dropna().unique()])
# #             available_months = [calendar.month_name[m] for m in available_month_nums]
# #         else:
# #             available_month_nums = []
# #             available_months = []

# #         selected_months = st.multiselect("Month(s)", available_months, default=available_months)

# #         min_date, max_date = None, None
# #         if selected_years and selected_months:
# #             month_nums_selected = [list(calendar.month_name).index(m) for m in selected_months]
# #             years_str = ','.join(f"'{y:04d}'" for y in selected_years)
# #             months_str = ','.join(f"'{m:02d}'" for m in month_nums_selected)

# #             date_range_query = f"""
# #                 SELECT MIN(date(appointment_date)) as min_date, MAX(date(appointment_date)) as max_date
# #                 FROM appointments
# #                 WHERE appointment_date IS NOT NULL
# #                 AND strftime('%Y', appointment_date) IN ({years_str})
# #                 AND strftime('%m', appointment_date) IN ({months_str})
# #             """
# #             date_range_df = pd.read_sql(date_range_query, db)
# #             min_date = pd.to_datetime(date_range_df.at[0, 'min_date'])
# #             max_date = pd.to_datetime(date_range_df.at[0, 'max_date'])
# #         else:
# #             date_range_query = """
# #                 SELECT MIN(date(appointment_date)) as min_date, MAX(date(appointment_date)) as max_date
# #                 FROM appointments
# #                 WHERE appointment_date IS NOT NULL
# #             """
# #             date_range_df = pd.read_sql(date_range_query, db)
# #             min_date = pd.to_datetime(date_range_df.at[0, 'min_date'])
# #             max_date = pd.to_datetime(date_range_df.at[0, 'max_date'])

# #         today = datetime.today().date()
# #         default_start = max(min_date.date(), today) if min_date else today
# #         default_end = max_date.date() if max_date else today

# #         # selected_date_range = st.date_input(
# #         #     "Date Range (Start - End)", 
# #         #     value=(default_start, default_end), 
# #         #     min_value=min_date.date() if min_date else None, 
# #         #     max_value=max_date.date() if max_date else None
# #         # )
# #         # Ensure min_date and max_date are valid
# #         if pd.isnull(min_date) or pd.isnull(max_date):
# #             min_date = pd.Timestamp(today)
# #             max_date = pd.Timestamp(today)

# #         # Ensure default_start <= default_end
# #         default_start = max(min_date.date(), today)
# #         default_end = max(default_start, max_date.date())

# #         selected_date_range = st.date_input(
# #             "Date Range (Start - End)", 
# #             value=(default_start, default_end), 
# #             min_value=min_date.date(), 
# #             max_value=max_date.date()
# #         )


# #     # Compose filters for query
# #     filters = []
# #     sql_conditions = []

# #     if selected_client_type:
# #         sql_conditions.append("client_type = ?")
# #         filters.append(selected_client_type)

# #     if selected_screen_type:
# #         sql_conditions.append("screen_type = ?")
# #         filters.append(selected_screen_type)

# #     if selected_term:
# #         sql_conditions.append("term = ?")
# #         filters.append(selected_term)

# #     if selected_years:
# #         year_placeholders = ",".join(["?"] * len(selected_years))
# #         sql_conditions.append(f"strftime('%Y', appointment_date) IN ({year_placeholders})")
# #         filters.extend([str(y) for y in selected_years])

# #     if selected_months:
# #         month_nums_selected = [list(calendar.month_name).index(m) for m in selected_months]
# #         month_placeholders = ",".join(["?"] * len(month_nums_selected))
# #         sql_conditions.append(f"strftime('%m', appointment_date) IN ({month_placeholders})")
# #         filters.extend([f"{m:02d}" for m in month_nums_selected])

# #     if selected_date_range and len(selected_date_range) == 2:
# #         start_date = selected_date_range[0].strftime("%Y-%m-%d")
# #         end_date = selected_date_range[1].strftime("%Y-%m-%d")
# #         sql_conditions.append("date(appointment_date) BETWEEN ? AND ?")
# #         filters.extend([start_date, end_date])

# #     base_query = """
# #         SELECT appointment_id, user_id, name, class, stream, term, screen_type, created_by, appointment_date
# #         FROM appointments
# #     """
# #     if sql_conditions:
# #         where_clause = " WHERE " + " AND ".join(sql_conditions)
# #         final_query = base_query + where_clause + " ORDER BY appointment_date DESC"
# #     else:
# #         final_query = base_query + " ORDER BY appointment_date DESC"

# #     filtered_df = pd.read_sql(final_query, db, params=filters)

# #     # BULK MODE
# #     if selected_client_type == "Student" and bulk_mode:
# #         class_options_df = pd.read_sql("SELECT DISTINCT class FROM appointments WHERE class IS NOT NULL", db)
# #         class_options = class_options_df['class'].dropna().tolist()
# #         stream_options_df = pd.read_sql("SELECT DISTINCT stream FROM appointments WHERE stream IS NOT NULL", db)
# #         stream_options = stream_options_df['stream'].dropna().tolist()

# #         with st.form("bulk_tool_form"):
# #             col1, col2 = st.columns(2)
# #             selected_classes = col1.multiselect("🎓 Filter by Class", class_options, default=class_options)
# #             selected_streams = col2.multiselect("🏞️ Filter by Stream", stream_options, default=stream_options)

# #             df_bulk = filtered_df.copy()
# #             if selected_classes:
# #                 df_bulk = df_bulk[df_bulk['class'].isin(selected_classes)]
# #             if selected_streams:
# #                 df_bulk = df_bulk[df_bulk['stream'].isin(selected_streams)]
# #             all_matching = df_bulk.dropna(subset=['appointment_id', 'user_id', 'created_by', 'name']).values.tolist()
# #             name_to_row = {row[2]: row for row in all_matching}  # name is row[3]
# #             selected_names = col1.multiselect(f"Select Specific {selected_client_type}s", list(name_to_row.keys()))
# #             selected_rows = [name_to_row[name] for name in selected_names] if selected_names else list(name_to_row.values())
# #             tools_to_assign = col2.multiselect("🧰 Select Tools to Assign", tools_list)
# #             scheduled_date = col1.date_input("📅 Scheduled Date").strftime("%Y-%m-%d")
# #             assign_tools_btn = st.form_submit_button("✅ Assign Tools (Bulk)")

# #         if assign_tools_btn:
# #             if not tools_to_assign:
# #                 st.error("Select at least one tool to assign.")
# #             elif not selected_rows:
# #                 st.warning("No records selected.")
# #             else:
# #                 added, skipped = [], []
# #                 for appointment_id, user_id, full_name, name, *rest in selected_rows:
# #                     a, s = assign_tools_to_screen(appointment_id, user_id, full_name, tools_to_assign, scheduled_date)
# #                     if a > 0:
# #                         added.append(name)
# #                     if s > 0:
# #                         skipped.append(name)
# #                 if added:
# #                     st.success(f"✅ Tools assigned: {', '.join(added)}")
# #                 if skipped:
# #                     st.warning(f"⚠️ Already assigned (not added): {', '.join(skipped)}")
# #                 if added:
# #                     send_notifications("Bulk Admin", ' & '.join(tools_to_assign), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
# #                 else:
# #                     st.info("No new tools assigned, so no notifications sent.")

# #         # Bulk Remove Tool
# #         existing_tools = set()
# #         for row in selected_rows:
# #             tools_df = fetch_screen_tools(row[1], db)
# #             if not tools_df.empty:
# #                 existing_tools.update(tools_df['tool'].tolist())

# #         if existing_tools:
# #             with st.form("remove_tool_form"):
# #                 col1, col2 = st.columns(2)
# #                 to_remove = col2.selectbox("🗑️ Tool to Remove", sorted(existing_tools))
# #                 remove_btn = st.form_submit_button("Remove Tool from Selected")

# #             if remove_btn:
# #                 for row in selected_rows:
# #                     remove_requested_tool(db, row[0], row[1], to_remove)
# #                 st.success(f"🧹 Removed '{to_remove}' from selected screens.")
# #         else:
# #             st.info("No tools currently assigned across selected.")

# #     # INDIVIDUAL MODE
# #     else:
# #         col1, col2 = st.columns([1.5, 2])
# #         if filtered_df.empty:
# #             st.warning("No matching clients/appointments found for the selected filters.")
# #             for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'class_', 'stream', 'created_by']:
# #                 st.session_state.pop(key, None)
# #         else:
# #             with col1.expander(f'Search {selected_client_type}', expanded=True):
# #                 search_input = st.text_input("Name or Appointment ID", key="search_input")
# #             results = []
# #             if search_input.strip():
# #                 results = filtered_df[
# #                     filtered_df.apply(
# #                         lambda row: (search_input.strip().upper() in str(row['appointment_id']).upper()) or
# #                                     (search_input.strip().lower() in str(row['name']).lower()), axis=1
# #                     )
# #                 ].values.tolist()

# #             if results:
# #                 options = [f"{row[3]} - {row[2]} - {row[7]}" for row in results]
# #                 current_appointment = st.session_state.get("appointment_id")
# #                 if current_appointment not in [row[3] for row in results]:
# #                     for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'class_', 'stream', 'created_by']:
# #                         st.session_state.pop(key, None)
# #                 with st.sidebar.expander('Search results', expanded=True):
# #                     st.write(f':orange[{len(options)} results for {search_input} found]')
# #                     selected = st.selectbox("Select Matching Client Record", options, key="client_select")

# #                 if selected:
# #                     selected_row = results[options.index(selected)]
# #                     if st.session_state.get("appointment_id") != selected_row[3]:
# #                         st.session_state.appointment_id = selected_row[0]      # appointment_id (0)
# #                         st.session_state.user_id = selected_row[1]             # user_id (1)
# #                         st.session_state.full_name = selected_row[2]           # name (2)
# #                         st.session_state.class_ = selected_row[3]              # class (3)
# #                         st.session_state.stream = selected_row[4]              # stream (4)
# #                         st.session_state.selected_term = selected_row[5]       # term (5)
# #                         st.session_state.selected_screen_type = selected_row[6]# screen_type (6)
# #                         st.session_state.created_by = selected_row[7]          # created_by (7)
# #                         # appointment_date (8) not stored in session_state currently

# #                         # st.rerun()
# #             else:
# #                 if search_input.strip():
# #                     st.warning("No matching clients/appointments found.")
# #                 for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'class_', 'stream', 'created_by']:
# #                     st.session_state.pop(key, None)

# #             if st.session_state.get("user_id"):
# #                 with st.sidebar.expander('Results', expanded=True):
# #                     st.subheader("📋 Selected Client Details")
# #                     st.markdown(f"""
# #                         **👤 Name:** {st.session_state.full_name}  
# #                         **🆔 User ID:** {st.session_state.user_id}  
# #                         **📅 Appointment ID:** {st.session_state.appointment_id}  
# #                         **📘 Term:** {st.session_state.selected_term}  
# #                         **🧾 Screen Type:** {st.session_state.selected_screen_type}  
# #                         **✍️ Created By:** {st.session_state.created_by}
# #                         """)

# #                     if selected_client_type == "Student":
# #                         st.markdown(f"""
# #                             **🏫 Class:** {st.session_state.get('class_', 'N/A')}  
# #                             **🌊 Stream:** {st.session_state.get('stream', 'N/A')}
# #                             """)


# #                 with col2.form('Assign Tools'):
# #                     tools_to_assign = st.multiselect("🧰 Select Tools", tools_list)
# #                     scheduled_date = st.date_input("📅 Scheduled Date").strftime("%Y-%m-%d")

# #                     if st.form_submit_button("✅ Assign Tools"):
# #                         if not tools_to_assign:
# #                             st.error("Please select tools to assign.")
# #                         else:
# #                             added, skipped = assign_tools_to_screen(
# #                                 st.session_state.appointment_id,
# #                                 st.session_state.user_id,
# #                                 st.session_state.created_by,
# #                                 tools_to_assign,
# #                                 scheduled_date,
# #                             )
# #                             if added:
# #                                 st.success(f"✅ {tools_to_assign} to {st.session_state.full_name}:  -- Assigned: {added}")
# #                             if skipped:
# #                                 st.warning(f"⚠️ {tools_to_assign} already assigned to {st.session_state.full_name}:Skipped {skipped}")
# #                             if added:
# #                                 send_notifications(st.session_state.full_name, ' & '.join(tools_to_assign), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
# #                             else:
# #                                 st.info("No new tools assigned, so no notifications sent.")

# #                 with col1.form("remove_tool_form"):
# #                     appointment_id = st.session_state.get("appointment_id")
# #                     tools_in_db_df = fetch_screen_tools(appointment_id, db)
# #                     if not tools_in_db_df.empty:
# #                         tools_in_db = tools_in_db_df['tool'].tolist()
# #                         tool_to_remove = st.selectbox("Select a Tool to Remove", tools_in_db)
# #                     else:
# #                         st.warning(f'No assigned tools yet for {appointment_id}')
# #                         tool_to_remove = None
# #                     remove = st.form_submit_button(":red[Delete]")
# #                     if remove and tool_to_remove:
# #                         remove_requested_tool(db, appointment_id, tool_to_remove)

# #             if st.checkbox('View Assigned Tools'):
# #                 appointment_id = st.session_state.get("appointment_id")
# #                 assigned_tools = fetch_screen_tools(appointment_id, db)
# #                 if not assigned_tools.empty:
# #                     st.dataframe(assigned_tools)
# #                 else:
# #                     st.warning(f'No assigned_tools on {appointment_id}')

# #     db.close()

# # if __name__ == "__main__":
# #     main()
# def main():
#     set_full_page_background('images/black_strip.jpg')
#     db = create_connection()

#     bulk_mode = st.toggle("Bulk Assign Mode", value=True)
#     tools_list = ["PHQ-4", "PHQ-9", "GAD-7", 'CAPS-14','SSQ','HSQ','SNAP-IV-C', "DASS-21", 'BDI', "SRQ"]
#     client_types = pd.read_sql("SELECT DISTINCT client_type FROM appointments", db)['client_type'].dropna().tolist()
#     terms = pd.read_sql("SELECT DISTINCT term FROM appointments", db)['term'].dropna().tolist()
#     screen_types = pd.read_sql("SELECT DISTINCT screen_type FROM appointments", db)['screen_type'].dropna().tolist()

#     year_df = pd.read_sql("SELECT DISTINCT strftime('%Y', appointment_date) AS year FROM appointments WHERE appointment_date IS NOT NULL", db)
#     available_years = sorted([int(y) for y in year_df['year'].dropna().unique()])
#     current_year = datetime.now().year
#     default_years = [current_year] if current_year in available_years else available_years[:1]

#     with st.sidebar.expander('FILTER OPTIONS', expanded=True):
#         selected_client_type = st.selectbox("Client Type", client_types)
#         selected_screen_type = st.selectbox("Screen Type", screen_types)
#         selected_term = st.selectbox("Term", terms)
#         selected_years, selected_months, selected_date_range = get_date_range_sidebar(db, available_years, default_years)

#     # --- FILTER QUERY ---
#     filters = []
#     sql_conditions = []

#     if selected_client_type:
#         sql_conditions.append("client_type = ?")
#         filters.append(selected_client_type)

#     if selected_screen_type:
#         sql_conditions.append("screen_type = ?")
#         filters.append(selected_screen_type)

#     if selected_term:
#         sql_conditions.append("term = ?")
#         filters.append(selected_term)

#     if selected_years:
#         year_placeholders = ",".join(["?"] * len(selected_years))
#         sql_conditions.append(f"strftime('%Y', appointment_date) IN ({year_placeholders})")
#         filters.extend([str(y) for y in selected_years])

#     if selected_months:
#         month_nums_selected = [list(calendar.month_name).index(m) for m in selected_months]
#         month_placeholders = ",".join(["?"] * len(month_nums_selected))
#         sql_conditions.append(f"strftime('%m', appointment_date) IN ({month_placeholders})")
#         filters.extend([f"{m:02d}" for m in month_nums_selected])

#     if selected_date_range and len(selected_date_range) == 2:
#         start_date = selected_date_range[0].strftime("%Y-%m-%d")
#         end_date = selected_date_range[1].strftime("%Y-%m-%d")
#         sql_conditions.append("date(appointment_date) BETWEEN ? AND ?")
#         filters.extend([start_date, end_date])

#     base_query = """
#         SELECT appointment_id, user_id, name, class, stream, term, screen_type, created_by, appointment_date
#         FROM appointments
#     """
#     final_query = base_query + (" WHERE " + " AND ".join(sql_conditions) if sql_conditions else "") + " ORDER BY appointment_date DESC"
#     filtered_df = pd.read_sql(final_query, db, params=filters)

#     # --- BULK MODE ---
#     if selected_client_type == "Student" and bulk_mode:
#         handle_bulk_mode(db, filtered_df, tools_list, selected_client_type)
#     else:
#         handle_individual_mode(db, filtered_df, tools_list, selected_client_type)

#     db.close()
# if __name__ == "__main__":
#     main()

def get_date_range_sidebar(db, available_years, default_years):
    """Handles year, month, and date range selection safely within the sidebar."""
    selected_years = st.multiselect("Year(s)", available_years, default=default_years)

    # --- MONTH SELECTION ---
    if selected_years:
        years_str = ','.join(f"'{y:04d}'" for y in selected_years)
        month_query = f"""
            SELECT DISTINCT strftime('%m', appointment_date) AS month 
            FROM appointments 
            WHERE appointment_date IS NOT NULL
            AND strftime('%Y', appointment_date) IN ({years_str})
        """
        month_df = pd.read_sql(month_query, db)
        available_month_nums = sorted([int(m) for m in month_df['month'].dropna().unique()])
        available_months = [calendar.month_name[m] for m in available_month_nums]
    else:
        available_month_nums = []
        available_months = []

    selected_months = st.multiselect("Month(s)", available_months, default=available_months)

    # --- DATE RANGE CALCULATION ---
    if selected_years and selected_months:
        month_nums_selected = [list(calendar.month_name).index(m) for m in selected_months]
        years_str = ','.join(f"'{y:04d}'" for y in selected_years)
        months_str = ','.join(f"'{m:02d}'" for m in month_nums_selected)

        date_range_query = f"""
            SELECT MIN(date(appointment_date)) as min_date, MAX(date(appointment_date)) as max_date
            FROM appointments
            WHERE appointment_date IS NOT NULL
            AND strftime('%Y', appointment_date) IN ({years_str})
            AND strftime('%m', appointment_date) IN ({months_str})
        """
        date_range_df = pd.read_sql(date_range_query, db)
    else:
        date_range_df = pd.read_sql("""
            SELECT MIN(date(appointment_date)) as min_date, MAX(date(appointment_date)) as max_date
            FROM appointments
            WHERE appointment_date IS NOT NULL
        """, db)

    min_date = pd.to_datetime(date_range_df.at[0, 'min_date'])
    max_date = pd.to_datetime(date_range_df.at[0, 'max_date'])
    today = datetime.today().date()

    # --- SAFETY CHECKS ---
    if pd.isnull(min_date) or pd.isnull(max_date):
        min_date = pd.Timestamp(today)
        max_date = pd.Timestamp(today)

    min_d = min_date.date()
    max_d = max_date.date()

    # Ensure defaults are within allowed range
    default_start = min(max(today, min_d), max_d)
    default_end = max(default_start, min(max_d, today))

    selected_date_range = st.date_input(
        "Date Range (Start - End)",
        value=(default_start, default_end),
        min_value=min_d,
        max_value=max_d
    )

    return selected_years, selected_months, selected_date_range


def main():
    set_full_page_background('images/black_strip.jpg')
    db = create_connection()

    bulk_mode = st.toggle("Bulk Assign Mode", value=True)
    tools_list = ["PHQ-4", "PHQ-9", "GAD-7", 'CAPS-14','SSQ','HSQ','SNAP-IV-C', "DASS-21", 'BDI', "SRQ"]
    client_types = pd.read_sql("SELECT DISTINCT client_type FROM appointments", db)['client_type'].dropna().tolist()
    terms = pd.read_sql("SELECT DISTINCT term FROM appointments", db)['term'].dropna().tolist()
    screen_types = pd.read_sql("SELECT DISTINCT screen_type FROM appointments", db)['screen_type'].dropna().tolist()

    year_df = pd.read_sql("SELECT DISTINCT strftime('%Y', appointment_date) AS year FROM appointments WHERE appointment_date IS NOT NULL", db)
    available_years = sorted([int(y) for y in year_df['year'].dropna().unique()])
    current_year = datetime.now().year
    default_years = [current_year] if current_year in available_years else available_years[:1]

    with st.sidebar.expander('FILTER OPTIONS', expanded=True):
        selected_client_type = st.selectbox("Client Type", client_types)
        selected_screen_type = st.selectbox("Screen Type", screen_types)
        selected_term = st.selectbox("Term", terms)
        selected_years, selected_months, selected_date_range = get_date_range_sidebar(db, available_years, default_years)

    # --- FILTER QUERY ---
    filters = []
    sql_conditions = []

    if selected_client_type:
        sql_conditions.append("client_type = ?")
        filters.append(selected_client_type)

    if selected_screen_type:
        sql_conditions.append("screen_type = ?")
        filters.append(selected_screen_type)

    if selected_term:
        sql_conditions.append("term = ?")
        filters.append(selected_term)

    if selected_years:
        year_placeholders = ",".join(["?"] * len(selected_years))
        sql_conditions.append(f"strftime('%Y', appointment_date) IN ({year_placeholders})")
        filters.extend([str(y) for y in selected_years])

    if selected_months:
        month_nums_selected = [list(calendar.month_name).index(m) for m in selected_months]
        month_placeholders = ",".join(["?"] * len(month_nums_selected))
        sql_conditions.append(f"strftime('%m', appointment_date) IN ({month_placeholders})")
        filters.extend([f"{m:02d}" for m in month_nums_selected])

    if selected_date_range and len(selected_date_range) == 2:
        start_date = selected_date_range[0].strftime("%Y-%m-%d")
        end_date = selected_date_range[1].strftime("%Y-%m-%d")
        sql_conditions.append("date(appointment_date) BETWEEN ? AND ?")
        filters.extend([start_date, end_date])

    base_query = """
        SELECT appointment_id, user_id, name, class, stream, term, screen_type, created_by, appointment_date
        FROM appointments
    """
    final_query = base_query + (" WHERE " + " AND ".join(sql_conditions) if sql_conditions else "") + " ORDER BY appointment_date DESC"
    filtered_df = pd.read_sql(final_query, db, params=filters)

    # --- BULK MODE ---
    if selected_client_type == "Student" and bulk_mode:
        class_options_df = pd.read_sql("SELECT DISTINCT class FROM appointments WHERE class IS NOT NULL", db)
        class_options = class_options_df['class'].dropna().tolist()
        stream_options_df = pd.read_sql("SELECT DISTINCT stream FROM appointments WHERE stream IS NOT NULL", db)
        stream_options = stream_options_df['stream'].dropna().tolist()

        with st.form("bulk_tool_form"):
            col1, col2 = st.columns(2)
            selected_classes = col1.multiselect("🎓 Filter by Class", class_options, default=class_options)
            selected_streams = col2.multiselect("🏞️ Filter by Stream", stream_options, default=stream_options)

            df_bulk = filtered_df.copy()
            if selected_classes:
                df_bulk = df_bulk[df_bulk['class'].isin(selected_classes)]
            if selected_streams:
                df_bulk = df_bulk[df_bulk['stream'].isin(selected_streams)]
            all_matching = df_bulk.dropna(subset=['appointment_id', 'user_id', 'created_by', 'name']).values.tolist()
            name_to_row = {row[2]: row for row in all_matching}
            selected_names = col1.multiselect(f"Select Specific {selected_client_type}s", list(name_to_row.keys()))
            selected_rows = [name_to_row[name] for name in selected_names] if selected_names else list(name_to_row.values())
            tools_to_assign = col2.multiselect("🧰 Select Tools to Assign", tools_list)
            scheduled_date = col1.date_input("📅 Scheduled Date").strftime("%Y-%m-%d")
            assign_tools_btn = st.form_submit_button("✅ Assign Tools (Bulk)")

        if assign_tools_btn:
            if not tools_to_assign:
                st.error("Select at least one tool to assign.")
            elif not selected_rows:
                st.warning("No records selected.")
            else:
                added, skipped = [], []
                for appointment_id, user_id, full_name, name, *rest in selected_rows:
                    a, s = assign_tools_to_screen(appointment_id, user_id, full_name, tools_to_assign, scheduled_date)
                    if a > 0:
                        added.append(name)
                    if s > 0:
                        skipped.append(name)
                if added:
                    st.success(f"✅ Tools assigned: {', '.join(added)}")
                if skipped:
                    st.warning(f"⚠️ Already assigned (not added): {', '.join(skipped)}")
                if added:
                    send_notifications("Bulk Admin", ' & '.join(tools_to_assign), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    st.info("No new tools assigned, so no notifications sent.")

        # Bulk Remove Tool
        existing_tools = set()
        for row in selected_rows:
            tools_df = fetch_screen_tools(row[1], db)
            if not tools_df.empty:
                existing_tools.update(tools_df['tool'].tolist())

        if existing_tools:
            with st.form("remove_tool_form"):
                col1, col2 = st.columns(2)
                to_remove = col2.selectbox("🗑️ Tool to Remove", sorted(existing_tools))
                remove_btn = st.form_submit_button("Remove Tool from Selected")

            if remove_btn:
                for row in selected_rows:
                    remove_requested_tool(db, row[0], row[1], to_remove)
                st.success(f"🧹 Removed '{to_remove}' from selected screens.")
        else:
            st.info("No tools currently assigned across selected.")

    # --- INDIVIDUAL MODE ---
    else:
        col1, col2 = st.columns([1.5, 2])
        if filtered_df.empty:
            st.warning("No matching clients/appointments found for the selected filters.")
            for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'class_', 'stream', 'created_by']:
                st.session_state.pop(key, None)
        else:
            with col1.expander(f'Search {selected_client_type}', expanded=True):
                search_input = st.text_input("Name or Appointment ID", key="search_input")
            results = []
            if search_input.strip():
                results = filtered_df[
                    filtered_df.apply(
                        lambda row: (search_input.strip().upper() in str(row['appointment_id']).upper()) or
                                    (search_input.strip().lower() in str(row['name']).lower()), axis=1
                    )
                ].values.tolist()

            if results:
                options = [f"{row[3]} - {row[2]} - {row[7]}" for row in results]
                current_appointment = st.session_state.get("appointment_id")
                if current_appointment not in [row[3] for row in results]:
                    for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'class_', 'stream', 'created_by']:
                        st.session_state.pop(key, None)
                with st.sidebar.expander('Search results', expanded=True):
                    st.write(f':orange[{len(options)} results for {search_input} found]')
                    selected = st.selectbox("Select Matching Client Record", options, key="client_select")

                if selected:
                    selected_row = results[options.index(selected)]
                    if st.session_state.get("appointment_id") != selected_row[3]:
                        st.session_state.appointment_id = selected_row[0]
                        st.session_state.user_id = selected_row[1]
                        st.session_state.full_name = selected_row[2]
                        st.session_state.class_ = selected_row[3]
                        st.session_state.stream = selected_row[4]
                        st.session_state.selected_term = selected_row[5]
                        st.session_state.selected_screen_type = selected_row[6]
                        st.session_state.created_by = selected_row[7]

            else:
                if search_input.strip():
                    st.warning("No matching clients/appointments found.")
                for key in ['user_id', 'appointment_id', 'full_name', 'selected_term', 'selected_screen_type', 'class_', 'stream', 'created_by']:
                    st.session_state.pop(key, None)

            if st.session_state.get("user_id"):
                with st.sidebar.expander('Results', expanded=True):
                    st.subheader("📋 Selected Client Details")
                    st.markdown(f"""
                        **👤 Name:** {st.session_state.full_name}  
                        **🆔 User ID:** {st.session_state.user_id}  
                        **📅 Appointment ID:** {st.session_state.appointment_id}  
                        **📘 Term:** {st.session_state.selected_term}  
                        **🧾 Screen Type:** {st.session_state.selected_screen_type}  
                        **✍️ Created By:** {st.session_state.created_by}
                        """)

                    if selected_client_type == "Student":
                        st.markdown(f"""
                            **🏫 Class:** {st.session_state.get('class_', 'N/A')}  
                            **🌊 Stream:** {st.session_state.get('stream', 'N/A')}
                            """)

                with col2.form('Assign Tools'):
                    tools_to_assign = st.multiselect("🧰 Select Tools", tools_list)
                    scheduled_date = st.date_input("📅 Scheduled Date").strftime("%Y-%m-%d")

                    if st.form_submit_button("✅ Assign Tools"):
                        if not tools_to_assign:
                            st.error("Please select tools to assign.")
                        else:
                            added, skipped = assign_tools_to_screen(
                                st.session_state.appointment_id,
                                st.session_state.user_id,
                                st.session_state.created_by,
                                tools_to_assign,
                                scheduled_date,
                            )
                            if added:
                                st.success(f"✅ {tools_to_assign} to {st.session_state.full_name}:  -- Assigned: {added}")
                            if skipped:
                                st.warning(f"⚠️ {tools_to_assign} already assigned to {st.session_state.full_name}: Skipped {skipped}")
                            if added:
                                send_notifications(st.session_state.full_name, ' & '.join(tools_to_assign), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            else:
                                st.info("No new tools assigned, so no notifications sent.")

                with col1.form("remove_tool_form"):
                    appointment_id = st.session_state.get("appointment_id")
                    tools_in_db_df = fetch_screen_tools(appointment_id, db)
                    if not tools_in_db_df.empty:
                        tools_in_db = tools_in_db_df['tool'].tolist()
                        tool_to_remove = st.selectbox("Select a Tool to Remove", tools_in_db)
                    else:
                        st.warning(f'No assigned tools yet for {appointment_id}')
                        tool_to_remove = None
                    remove = st.form_submit_button(":red[Delete]")
                    if remove and tool_to_remove:
                        remove_requested_tool(db, appointment_id, tool_to_remove)

            if st.checkbox('View Assigned Tools'):
                appointment_id = st.session_state.get("appointment_id")
                assigned_tools = fetch_screen_tools(appointment_id, db)
                if not assigned_tools.empty:
                    st.dataframe(assigned_tools)
                else:
                    st.warning(f'No assigned_tools on {appointment_id}')

    db.close()

    db.close()
if __name__ == '__main__':
    main()