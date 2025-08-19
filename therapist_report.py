DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime
import os, base64
import json
import pandas as pd
from streamlit_option_menu import option_menu
import re
import file_per_appointment
DB = "users_db.db"

##### DESISGN FXN ######
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



###### CREATE TABLE ##########
def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

def create_reports_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_type TEXT,
            date TEXT,
            compiled_by TEXT,
            data TEXT
        )
    """)
    conn.commit()




def insert_report(conn, session_type, form_data, compiled_by):
    cursor = conn.cursor()
    form_data_json = json.dumps(form_data, sort_keys=True)  # sort_keys to ensure consistent comparison
    cursor.execute("""
        SELECT COUNT(*) FROM session_reports
        WHERE session_type = ? AND compiled_by = ? AND data = ?
    """, (session_type, compiled_by, form_data_json))
    exists = cursor.fetchone()[0]

    if exists:
        st.warning("⚠️ A similar report already exists. Submission cancelled.")
        return
    cursor.execute("""
        INSERT INTO session_reports (session_type, date, compiled_by, data)
        VALUES (?, ?, ?, ?)
    """, (
        session_type,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        compiled_by,
        form_data_json
    ))
    conn.commit()


###### FTETCH FXNS   #######
def fetch_reports(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM session_reports ORDER BY date DESC")
    rows = cursor.fetchall()
    return rows


def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None




def fetch_therapist_clients(therapist):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM appointments")
    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]
    conn.close()

    results = []

    for row in rows:
        row_dict = dict(zip(col_names, row))
        try:
            actions = json.loads(row_dict.get("actions", "{}"))
            assigned = json.loads(row_dict.get("assigned_therapist", "{}"))

            consult_true = actions.get("consult") is True
            therapist_assigned = therapist in assigned.get("consult", [])

            if consult_true and therapist_assigned:
                results.append(row_dict)
        except json.JSONDecodeError:
            continue

    return pd.DataFrame(results) if results else pd.DataFrame()

import calendar
from datetime import datetime, date
def get_distinct_years(conn):
    query = """
    SELECT DISTINCT strftime('%Y', appointment_date) AS year
    FROM appointments
    ORDER BY year
    """
    cursor = conn.cursor()
    cursor.execute(query)
    years = [int(row[0]) for row in cursor.fetchall() if row[0] is not None]
    return years

def get_distinct_months(conn, year):
    query = """
    SELECT DISTINCT strftime('%m', appointment_date) AS month
    FROM appointments
    WHERE strftime('%Y', appointment_date) = ?
    ORDER BY month
    """
    cursor = conn.cursor()
    cursor.execute(query, (str(year),))
    months = [int(row[0]) for row in cursor.fetchall() if row[0] is not None]
    return months
def get_date_range_for_months(conn, year, months):
    placeholders = ",".join("?" for _ in months)
    query = f"""
    SELECT MIN(appointment_date), MAX(appointment_date)
    FROM appointments
    WHERE strftime('%Y', appointment_date) = ?
      AND strftime('%m', appointment_date) IN ({placeholders})
    """
    params = [str(year)] + [f"{m:02d}" for m in months]
    cursor = conn.cursor()
    cursor.execute(query, params)
    min_date_str, max_date_str = cursor.fetchone()

    min_date = datetime.fromisoformat(min_date_str).date() if min_date_str else None
    max_date = datetime.fromisoformat(max_date_str).date() if max_date_str else None
    return min_date, max_date




##### CRETATE REPORTS TEMPLATES #####
def create_report_section(db, compiled_by):
    conn = create_connection()
    years = get_distinct_years(conn)
    if not years:
        st.warning("No appointments found to filter by date.")
        return
    with st.sidebar.expander('FILTER OPTIONS', expanded=True):
        selected_year = st.selectbox("Select Year", years)
        months = get_distinct_months(conn, selected_year)
        month_names = [calendar.month_name[m] for m in months]
        selected_month_names = st.multiselect("Select Month(s)", month_names, default=month_names)
        selected_month_nums = [list(calendar.month_name).index(m) for m in selected_month_names]
        if selected_month_nums:
            min_date, max_date = get_date_range_for_months(conn, selected_year, selected_month_nums)
            if min_date and max_date:
                start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
                end_date = st.date_input("End Date", value=max_date, min_value=start_date, max_value=max_date)
            else:
                st.warning("No appointment dates found for the selected months.")
                start_date = None
                end_date = None
        else:
            st.info("Please select at least one month to choose start and end dates.")
            start_date = None
            end_date = None

    if "edit_mode" not in st.session_state:
        st.session_state["edit_mode"] = False
    if "edit_report_id" not in st.session_state:
        st.session_state["edit_report_id"] = None
    if "edit_form_data" not in st.session_state:
        st.session_state["edit_form_data"] = {}
    set_full_page_background('images/black_strip.jpg')
    create_reports_table(conn)
    username = st.session_state.get('user_name')
    therapist_name = username
    if "view_file_mode" not in st.session_state:
        st.session_state["view_file_mode"] = False
    if "appointment_id" not in st.session_state:
        st.session_state["appointment_id"] = None

    if st.session_state["view_file_mode"] and st.session_state["appointment_id"]:
        import file_per_appointment
        file_per_appointment.main(st.session_state["appointment_id"])
        if st.button("🔙 Back to Reporting Form"):
            st.session_state["view_file_mode"] = False
            st.rerun()
        return
    with st.sidebar.expander('FORM TYPE', expanded=True):
        session_type = st.selectbox("📌 Select Session Type", ['',"Consult", "Follow-Up", "Group Session", "Classroom Session", "School Session"])
    form_data = {}
    st.subheader(f"📋 {session_type} report")
    
    with st.expander("FORMS", expanded=True):
        if session_type == "Consult":
            st.write("Therapist:", therapist_name)
            clients_df = fetch_therapist_clients(therapist_name)
            if clients_df.empty:
                st.warning("⚠️ No consults found for you.")
                st.stop()
            if "selected_labels" not in st.session_state:
                st.session_state["selected_labels"] = []
            if "remarks_per_client" not in st.session_state:
                st.session_state["remarks_per_client"] = {}
            if "general_remarks" not in st.session_state:
                st.session_state["general_remarks"] = ""
            clients_df["label"] = clients_df.apply(
                lambda r: f"{r['name']} - {r['appointment_id']}", axis=1)
            selected_labels = st.multiselect(
                "Select clients seen in this session:",
                options=clients_df["label"].tolist(),
                default=st.session_state["selected_labels"],
                key="multi_client_selector",)
            st.session_state["selected_labels"] = selected_labels
            form_data["clients_seen"] = len(selected_labels)
            st.number_input("📌 Total Clients Seen",
                            value=form_data["clients_seen"],
                            disabled=True)
            st.markdown("### 📝 Remarks per Client")
            remarks_per_client = {}
            for label in selected_labels:
                row = clients_df[clients_df["label"] == label]
                if not row.empty:
                    appointment_id = row.iloc[0]["appointment_id"]
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        remark_value = st.session_state["remarks_per_client"].get(label, "")
                        remark = st.text_area(f"Remarks for {label}",
                                              value=remark_value,
                                              key=f"remark_{label}")
                        remarks_per_client[label] = remark
                    with col2:
                        if st.button("🗃️File", key=f"open_{appointment_id}"):
                            st.session_state.update({
                                "view_file_mode": True,
                                "appointment_id": appointment_id,
                                "remarks_per_client": remarks_per_client,
                                "general_remarks": st.session_state.get("general_remarks", "")
                            })
                            st.rerun()
                else:
                    st.warning(f"⚠️ Client '{label}' not found in data.")

            form_data["remarks_per_client"] = remarks_per_client
            form_data["general_remarks"] = st.text_area(
                "🖊️ Recommendations",
                value=st.session_state["general_remarks"],
                key="general_remarks",)
            if st.button("✅ Submit Session Report"):
                insert_report(conn, session_type, form_data, compiled_by)
                st.success("✅ Report submitted successfully!")

        elif session_type == "Follow-Up":
            form_data["clients_followed"] = st.number_input("Clients Followed-Up", min_value=1)
            form_data["follow_up_plan"] = st.text_area("Follow-Up Plan")
            form_data["outcome"] = st.text_area("Outcome/Remarks")
            if st.button("✅ Submit Session Report"):
                insert_report(conn, session_type, form_data, compiled_by)
                st.success("✅ Report submitted successfully!")
        elif session_type == "Group Session":
            form_data["group_name"] = st.text_input("Group Name")
            form_data["members_present"] = st.text_area("Members Present (comma-separated)")
            form_data["topic"] = st.text_input("Topic")
            form_data["theme"] = st.text_input("Theme")
            form_data["discussion_summary"] = st.text_area("Summary of Discussion")
            form_data["remarks"] = st.text_area("Remarks")
            form_data["next_steps"] = st.text_area("Next Steps")
            if st.button("✅ Submit Session Report"):
                insert_report(conn, session_type, form_data, compiled_by)
                st.success("✅ Report submitted successfully!")
        elif session_type == "School Session":
            form_data["participants"] = st.number_input("Number of Participants", min_value=1)
            form_data["sub_activities"] = st.text_area("Sub-Activities")
            form_data["description"] = st.text_area("Description")
            form_data["outcome"] = st.text_area("Outcome")
            form_data["remarks"] = st.text_area("Remarks")
            if st.button("✅ Submit Session Report"):
                insert_report(conn, session_type, form_data, compiled_by)
                st.success("✅ Report submitted successfully!")
        elif session_type == "Classroom Session":
            st.markdown("### 🏫 Classroom Session Reporting")
            form_data["facilitators"] = st.multiselect("👥 Facilitators", options=[
                "Therapist A", "Therapist B", "Peer Leader", "Counselor", "Health Worker"])
            st.markdown("### 🏷️ Class & Stream Selection")
            class_options = ["S1", "S2", "S3", "S4", "S5", "S6"]
            stream_options = ["Red", "Blue", "Green", "Yellow", "White", "Purple"]
            selected_classes = st.multiselect("🏫 Select Classes", class_options)
            form_data["class_stream_map"] = {}

            for cls in selected_classes:
                st.markdown(f"#### Streams for {cls}")
                selected_streams = st.multiselect(
                    f"Select Streams for {cls}",
                    options=stream_options,
                    key=f"stream_select_{cls}"
                )
                form_data["class_stream_map"][cls] = selected_streams

            st.markdown("### 📚 Topics, Themes, and Discussions")
            available_topics = [
                "Stress Management", "Substance Use", "Goal Setting", "Relationships",
                "Reproductive Health", "Bullying", "Peer Pressure"
            ]
            available_themes = [
                "Understanding", "Coping Strategies", "Consequences",
                "Support Systems", "Preventive Actions"
            ]
            selected_topics = st.multiselect("📚 Select Topics Covered", available_topics)
            form_data["topics_themes"] = {}
            for topic in selected_topics:
                st.markdown(f"#### Topic: {topic}")
                selected_themes = st.multiselect(
                    f"📌 Select Themes under '{topic}'",
                    options=available_themes,
                    key=f"theme_select_{topic}"
                )
                theme_discussions = {}
                for theme in selected_themes:
                    discussion = st.text_area(
                        f"💬 Discussion for Theme '{theme}' under Topic '{topic}'",
                        key=f"discussion_{topic}_{theme}"
                    )
                    theme_discussions[theme] = discussion
                form_data["topics_themes"][topic] = theme_discussions

            st.markdown("### 📝 Summary & Reflections")
            form_data["key_highlights"] = st.text_area("🌟 Key Highlights")
            form_data["feedback"] = st.text_area("💬 Feedback / Comments")
            form_data["remarks"] = st.text_area("🖊️ Final Remarks")

            submitted = st.button("✅ Submit Report")
            if submitted:
                insert_report(conn, session_type, form_data, compiled_by)
                st.success("✅ Report submitted successfully!")


def get_distinct_report_years(conn, compiled_by):
    query = """
        SELECT DISTINCT strftime('%Y', date) AS year FROM session_reports
        WHERE compiled_by = ? ORDER BY year
    """
    return [int(row[0]) for row in conn.execute(query, (compiled_by,)).fetchall() if row[0]]

def get_distinct_report_months(conn, compiled_by, year):
    query = """
        SELECT DISTINCT strftime('%m', date) AS month FROM session_reports
        WHERE compiled_by = ? AND strftime('%Y', date) = ?
        ORDER BY month
    """
    return [int(row[0]) for row in conn.execute(query, (compiled_by, str(year))).fetchall() if row[0]]

def get_report_date_range(conn, compiled_by, year, months):
    placeholders = ",".join("?" for _ in months)
    query = f"""
        SELECT MIN(date), MAX(date) FROM session_reports
        WHERE compiled_by = ? AND strftime('%Y', date) = ? AND strftime('%m', date) IN ({placeholders})
    """
    params = [compiled_by, str(year)] + [f"{m:02d}" for m in months]
    min_date_str, max_date_str = conn.execute(query, params).fetchone()
    min_date = datetime.fromisoformat(min_date_str).date() if min_date_str else None
    max_date = datetime.fromisoformat(max_date_str).date() if max_date_str else None
    return min_date, max_date


def update_report(conn, report_id, session_type, form_data, compiled_by):
    cursor = conn.cursor()
    data_json = json.dumps(form_data)
    query = """
        UPDATE session_reports
        SET session_type = ?, data = ?, compiled_by = ?
        WHERE id = ?
    """
    cursor.execute(query, (session_type, data_json, compiled_by, report_id))
    conn.commit()


######### EDIT FUNCTION ######
def edit_report_section(conn, compiled_by):
    # st.header("✏️ Edit Existing Session Report")
    with st.sidebar.expander('FILTER OPTIONS', expanded=True):
        years = get_distinct_report_years(conn, compiled_by)
        selected_year = st.selectbox("Select Year", years)
        months = get_distinct_report_months(conn, compiled_by, selected_year)
        month_names = [calendar.month_name[m] for m in months]
        selected_month_names = st.multiselect("Select Month(s)", month_names, default=month_names)
        selected_month_nums = [list(calendar.month_name).index(m) for m in selected_month_names]

        if selected_month_nums:
            min_date, max_date = get_report_date_range(conn, compiled_by, selected_year, selected_month_nums)
            if not min_date or not max_date:
                st.warning("No reports found in selected months.")
                return
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
            end_date = st.date_input("End Date", value=max_date, min_value=start_date, max_value=max_date)
        else:
            st.warning("Select at least one month to view and filter reports.")
            return
    if st.session_state.get("view_file_mode") and st.session_state.get("appointment_id"):
        import file_per_appointment
        file_per_appointment.main(st.session_state["appointment_id"])
        if st.button("🔙 Back to Editing Form"):
            st.session_state["view_file_mode"] = False
            st.rerun()
        return

    query = """
        SELECT * FROM session_reports
        WHERE compiled_by = ?
          AND date BETWEEN ? AND ?
        ORDER BY date DESC
    """
    cursor = conn.cursor()
    cursor.execute(query, (compiled_by, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
    reports = cursor.fetchall()

    if not reports:
        st.info("No reports found within selected date range.")
        return

    report_options = [f"{r['id']} - {r['session_type']} - {r['date']}" for r in reports]
    with st.sidebar.expander('Select Report',expanded=True):
        selected_report_str = st.selectbox("Select a report to edit", options=report_options)
    selected_report_id = int(selected_report_str.split("-")[0].strip())
    selected_report = next((r for r in reports if r["id"] == selected_report_id), None)

    if not selected_report:
        st.error("Selected report not found.")
        return

    try:
        form_data = json.loads(selected_report["data"])
    except Exception as e:
        st.error(f"Failed to load report data: {e}")
        return
    with st.expander('REPORT', expanded=True):
        session_type = selected_report["session_type"]
        st.subheader(f"Editing Report: {session_type} (ID: {selected_report_id})")
        updated_form_data = {}

        if session_type == "Consult":
            st.write(f"Therapist: {compiled_by}")
            try:
                session_date_val = datetime.strptime(form_data.get("session_date", ""), "%Y-%m-%d").date()
            except Exception:
                session_date_val = datetime.today().date()

            updated_form_data["session_date"] = st.date_input("Session Date", value=session_date_val).strftime("%Y-%m-%d")
            clients_df = fetch_therapist_clients(compiled_by)
            clients_df["label"] = clients_df.apply(
                lambda row: f"{row['name']} - {row['appointment_id']}", axis=1)

            prev_selected_labels = list(form_data.get("remarks_per_client", {}).keys())
            selected_labels = st.multiselect(
                "Select clients who were seen during this session:",
                options=clients_df["label"].tolist(),
                default=prev_selected_labels,
                key="edit_multi_client_selector"
            )
            updated_form_data["clients_seen"] = len(selected_labels)
            st.number_input("Total Clients Seen", value=updated_form_data["clients_seen"], disabled=True)

            prev_remarks = form_data.get("remarks_per_client", {})
            new_remarks = {}

            st.markdown("### Remarks per Client")
            for label in selected_labels:
                row = clients_df[clients_df["label"] == label]
                if not row.empty:
                    appointment_id = row.iloc[0]["appointment_id"]
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        prev_remark = prev_remarks.get(label, "")
                        remark = st.text_area(f"Remarks for {label}", value=prev_remark, key=f"edit_remark_{label}")
                        new_remarks[label] = remark
                    with col2:
                        if st.button("🗃️File", key=f"open_edit_{appointment_id}"):
                            # Save current remarks before switching to file view
                            st.session_state.update({
                                "view_file_mode": True,
                                "appointment_id": appointment_id,
                                "remarks_per_client": new_remarks,
                                "general_remarks": updated_form_data.get("general_remarks", form_data.get("general_remarks", ""))
                            })
                            st.rerun()
                else:
                    st.warning(f"⚠️ Client '{label}' not found in data.")

            updated_form_data["remarks_per_client"] = new_remarks

            updated_form_data["general_remarks"] = st.text_area("Recommendations", value=form_data.get("general_remarks", ""))
            if st.button("✅ Update report"):
                update_report(conn, selected_report_id, session_type, updated_form_data, compiled_by)
                st.success("✅ Report updated successfully!")



        elif session_type == "Follow-Up":
            updated_form_data["clients_followed"] = st.number_input(
                "Clients Followed-Up", min_value=1, value=form_data.get("clients_followed", 1))
            updated_form_data["follow_up_plan"] = st.text_area(
                "Follow-Up Plan", value=form_data.get("follow_up_plan", ""))
            updated_form_data["outcome"] = st.text_area(
                "Outcome/Remarks", value=form_data.get("outcome", ""))
        elif session_type == "Group Session":
            updated_form_data["group_name"] = st.text_input(
                "Group Name", value=form_data.get("group_name", ""))
            updated_form_data["members_present"] = st.text_area(
                "Members Present (comma-separated)", value=form_data.get("members_present", ""))
            updated_form_data["topic"] = st.text_input(
                "Topic", value=form_data.get("topic", ""))
            updated_form_data["theme"] = st.text_input(
                "Theme", value=form_data.get("theme", ""))
            updated_form_data["discussion_summary"] = st.text_area(
                "Summary of Discussion", value=form_data.get("discussion_summary", ""))
            updated_form_data["remarks"] = st.text_area(
                "Remarks", value=form_data.get("remarks", ""))
            updated_form_data["next_steps"] = st.text_area(
                "Next Steps", value=form_data.get("next_steps", ""))

        elif session_type == "School Session":
            updated_form_data["participants"] = st.number_input(
                "Number of Participants", min_value=1, value=form_data.get("participants", 1))
            updated_form_data["sub_activities"] = st.text_area(
                "Sub-Activities", value=form_data.get("sub_activities", ""))
            updated_form_data["description"] = st.text_area(
                "Description", value=form_data.get("description", ""))
            updated_form_data["outcome"] = st.text_area(
                "Outcome", value=form_data.get("outcome", ""))
            updated_form_data["remarks"] = st.text_area(
                "Remarks", value=form_data.get("remarks", ""))

        elif session_type == "Classroom Session":
            facilitators = ["Therapist A", "Therapist B", "Peer Leader", "Counselor", "Health Worker"]
            updated_form_data["facilitators"] = st.multiselect(
                "Facilitators", options=facilitators, default=form_data.get("facilitators", []))

            class_options = ["S1", "S2", "S3", "S4", "S5", "S6"]
            stream_options = ["Red", "Blue", "Green", "Yellow", "White", "Purple"]
            updated_form_data["class_stream_map"] = {}
            selected_classes = list(form_data.get("class_stream_map", {}).keys())
            selected_classes = st.multiselect("Select Classes", options=class_options, default=selected_classes)
            for cls in selected_classes:
                prev_streams = form_data.get("class_stream_map", {}).get(cls, [])
                selected_streams = st.multiselect(
                    f"Streams for {cls}",
                    options=stream_options,
                    default=prev_streams,
                    key=f"edit_stream_{cls}"
                )
                updated_form_data["class_stream_map"][cls] = selected_streams

            available_topics = [
                "Stress Management", "Substance Use", "Goal Setting", "Relationships",
                "Reproductive Health", "Bullying", "Peer Pressure"
            ]
            available_themes = [
                "Understanding", "Coping Strategies", "Consequences",
                "Support Systems", "Preventive Actions"
            ]

            prev_topics = form_data.get("topics_themes", {}).keys()
            selected_topics = st.multiselect("Select Topics Covered", options=available_topics, default=list(prev_topics))
            updated_form_data["topics_themes"] = {}
            for topic in selected_topics:
                prev_theme_dict = form_data.get("topics_themes", {}).get(topic, {})
                selected_themes = st.multiselect(
                    f"Themes under '{topic}'",
                    options=available_themes,
                    default=list(prev_theme_dict.keys()),
                    key=f"edit_theme_{topic}"
                )
                theme_discussions = {}
                for theme in selected_themes:
                    prev_discussion = prev_theme_dict.get(theme, "")
                    discussion = st.text_area(
                        f"Discussion for Theme '{theme}' under Topic '{topic}'",
                        value=prev_discussion,
                        key=f"edit_discussion_{topic}_{theme}"
                    )
                    theme_discussions[theme] = discussion
                updated_form_data["topics_themes"][topic] = theme_discussions

            updated_form_data["key_highlights"] = st.text_area("Key Highlights", value=form_data.get("key_highlights", ""))
            updated_form_data["feedback"] = st.text_area("Feedback / Comments", value=form_data.get("feedback", ""))
            updated_form_data["remarks"] = st.text_area("Final Remarks", value=form_data.get("remarks", ""))
            
            if st.button("Update Report"):
                updated_row = {
                    "date": updated_form_data.get("session_date") or selected_report["date"],
                    "compiled_by": compiled_by,
                    "session_type": selected_report["session_type"],
                    "data": json.dumps(updated_form_data)
                }
                update_report(conn, selected_report_id, updated_row)
                st.success("✅ Report updated successfully!")
                st.rerun()



def get_full_name_from_username(username):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    res = cur.fetchone()
    conn.close()
    return res["full_name"] if res else None


###### DISPLAY FNCTION #######

def _set_qs(keep: dict = {}, drop: list = []):
    for k in drop:
        st.query_params.pop(k, None)
    for k, v in keep.items():
        st.query_params[k] = str(v)


@st.dialog('.', width='large')
def appointment_details_dialog(appointment_id: str, report_id: int):
    file_per_appointment.main(appointment_id)
    if st.button("❌ Close"):
        _set_qs(keep=dict(report_id=report_id), drop=["appointment_id"])
        st.rerun()

def display_reports_section(conn, compiled_by):
    st.markdown(
        """
        <style>
            .preview-container {background-color:#EAEAEA;border:2px solid #B0B0B0;padding:10px 20px;
                border-radius:20px;box-shadow:2px 2px 5px rgba(0,0,0,0.1);margin-bottom:15px;}
            .line{margin-bottom:8px;}
            .label{font-family:'Times New Roman',serif;font-size:18px;font-weight:bold;
                   color:#0056b3;font-style:italic;display:inline-block;width:40%;}
            .text{font-family:'Times New Roman',serif;font-size:18px;color:#333;font-style:italic;
                  display:inline-block;vertical-align:top;max-width:calc(100% - 200px);word-wrap:break-word;}
            .header{font-family:'Times New Roman',serif;font-size:20px;font-weight:bold;color:#222;margin-bottom:15px;}
            a.client-link{color:green;text-decoration:underline;font-style:italic;font-weight:bold;font-size:16px;}
        </style>
        """,
        unsafe_allow_html=True,)
    cur = conn.cursor()
    cur.execute("SELECT * FROM session_reports WHERE compiled_by=? ORDER BY date DESC", (compiled_by,))
    reports = cur.fetchall()
    if not reports:
        st.info("No reports found.")
        return
    options = [f"{r['id']} - {r['session_type']} - {r['date']}" for r in reports]
    qs = st.query_params
    url_rep = int(qs.get("report_id", reports[0]["id"]))
    default_idx = next((i for i,s in enumerate(options) if s.startswith(f"{url_rep} ")), 0)
    with st.sidebar.expander('REPORTS', expanded= True):

        selected = st.selectbox("Select report to view", options, index=default_idx, key="report_box")
    rep_id = int(selected.split("-")[0].strip())
    report = next(r for r in reports if r["id"] == rep_id)
    _set_qs(keep=dict(report_id=rep_id))
    try:
        form = json.loads(report["data"])
    except Exception:
        st.error("Failed to load report data.")
        return

    def line(lbl, val):
        return f"<div class='line'><span class='label'>{lbl}:</span><span class='text'>{val or 'N/A'}</span></div>"
    html = [ "<div class='preview-container'>",f"<div class='header'>📌 Report: {report['session_type']} (Date: {report['date']})</div>",]
    if report["session_type"] == "Consult":
        html += [line("📅 Session Date", form.get("session_date")), line("👥 Clients Seen", form.get("clients_seen"))]

        for i, (lbl, remark) in enumerate(form.get("remarks_per_client", {}).items(), 1):
            name = re.sub(r"\s*-\s*\d{4}-\d{2}-\d{2}$", "", lbl).strip()
            m = re.search(r"(APP-[\w-]+)", lbl)
            app_id = m.group(1) if m else None

            if app_id:
                url = f"?report_id={rep_id}&appointment_id={app_id}"
                html.append(f"<div class='line'><span class='label'>{i}. <a class='client-link' href='{url}'>{name}</a>:</span>"f"<span class='text'>{remark or 'N/A'}</span></div>")
            else:
                html.append(line(f"{i}. {name}", remark))

        html.append(line("📝 Recommendations", form.get("general_remarks")))
    elif report["session_type"] == "Follow-Up":
        html += [
            line("👥 Clients Followed‑Up", form.get("clients_followed")),
            line("📑 Follow‑Up Plan",      form.get("follow_up_plan")),
            line("📝 Outcome / Remarks",   form.get("outcome")),]
    elif report["session_type"] == "Group Session":
        members = ", ".join(m.strip() for m in form.get("members_present", "").split(",") if m.strip())
        html += [
            line("👥 Group Name",          form.get("group_name")),
            line("👤 Members Present",     members or "N/A"),
            line("📚 Topic",               form.get("topic")),
            line("🎨 Theme",               form.get("theme")),
            line("💬 Discussion Summary",  form.get("discussion_summary")),
            line("📝 Remarks",             form.get("remarks")),
            line("🚀 Next Steps",          form.get("next_steps")),
        ]

    # -------------------- CLASSROOM SESSION ------------------------------------------
    elif report["session_type"] == "Classroom Session":
        facilitators = ", ".join(form.get("facilitators", []))
        cs_map = "; ".join(
            f"{cls}: {', '.join(streams)}" if streams else cls
            for cls, streams in form.get("class_stream_map", {}).items()
        )
        topic_blocks = []
        for topic, themes in form.get("topics_themes", {}).items():
            if themes:
                theme_text = "; ".join(f"{th}: {desc}" if desc else th for th, desc in themes.items())
                topic_blocks.append(f"{topic} ({theme_text})")
            else:
                topic_blocks.append(topic)
        topics_text = "; ".join(topic_blocks)
        html += [
            line("👥 Facilitators",        facilitators or "N/A"),
            line("🏫 Classes & Streams",   cs_map or "N/A"),
            line("📚 Topics & Themes",     topics_text or "N/A"),
            line("🌟 Key Highlights",      form.get("key_highlights")),
            line("💬 Feedback / Comments", form.get("feedback")),
            line("🖊️ Final Remarks",       form.get("remarks")),
        ]

    # -------------------- SCHOOL SESSION ---------------------------------------------
    elif report["session_type"] == "School Session":
        html += [
            line("👥 Participants",   form.get("participants")),
            line("📌 Sub‑Activities", form.get("sub_activities")),
            line("📄 Description",    form.get("description")),
            line("🎯 Outcome",        form.get("outcome")),
            line("📝 Remarks",        form.get("remarks")),
        ]

    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)
    if "appointment_id" in qs:
        appointment_details_dialog(qs["appointment_id"], rep_id)



##### DRVER CODE ######
# ---------------------------- MAIN DRIVER FUNCTION ----------------------------
def main():
    conn = create_connection()

    set_full_page_background('images/black_strip.jpg')
    if "edit_mode" not in st.session_state:
        st.session_state["edit_mode"] = False
    if "edit_report_id" not in st.session_state:
        st.session_state["edit_report_id"] = None
    if "edit_form_data" not in st.session_state:
        st.session_state["edit_form_data"] = {}
    username = st.session_state.get("user_name")
    therapist_name = username
    clients = fetch_therapist_clients(therapist_name)
    choice = option_menu(
            menu_title="",
            options=["Add", "Edit", "Display"],
            icons=["plus-circle", "pencil-square", "eye"],
            orientation = "horizontal",
            styles={"container": {"padding": "8!important", "background-color": 'black','border': '0.01px dotted red'},
                    "icon": {"color": "red", "font-size": "15px"},
                            "nav-link": {"color": "#d7c4c1", "font-size": "15px","font-weight":'bold', "text-align": "left", "margin": "0px", "--hover-color": "red"},
                            "nav-link-selected": {"background-color": "green"},
                        },
            default_index=0)

    if choice == "Add":
        create_report_section(conn, therapist_name)

    elif choice == "Edit":
        edit_report_section(conn, therapist_name)
    elif choice == "Display":
        display_reports_section(conn, therapist_name)

    conn.close()

if __name__ == "__main__":
    main()
