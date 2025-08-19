DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime
import os, base64
import json, re
import pandas as pd
from streamlit_option_menu import option_menu
import file_per_appointment
DB = "users_db.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

def fetch_reports(conn):
    df = pd.read_sql(
        """
        SELECT id, compiled_by, session_type, date, data
        FROM session_reports
        ORDER BY date DESC
        """,
        conn,
        parse_dates=["date"],
    )
    return df

def _short_summary(session_type: str, data_json: dict) -> str:
    try:
        d = json.loads(data_json)
    except Exception:
        d = {}
    if session_type == "Consult":
        return f"{d.get('clients_seen', 0)} client(s)"
    if session_type == "Follow-Up":
        return f"{d.get('clients_followed', 0)} follow‑ups"
    if session_type == "Group Session":
        return d.get("topic", "Group Session")
    if session_type == "School Session":
        return f"{d.get('participants', 0)} participants"
    if session_type == "Classroom Session":
        return f"Classroom ({len(d.get('class_stream_map', {}))} classes)"
    return session_type  # fallback



def render_single_report(conn, report_id: int):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM session_reports WHERE id = ?", (report_id,))
    selected_report = cursor.fetchone()
    if not selected_report:
        st.error("Report not found.")
        return

    try:
        form_data = json.loads(selected_report["data"])
    except Exception:
        st.error("Invalid report data.")
        return

    # Styled CSS
    st.markdown("""
        <style>
            .preview-container {
                background-color: #EAEAEA;
                border: 2px solid #B0B0B0;
                padding: 10px 20px;
                border-radius: 20px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 15px;
            }
            .line {
                margin-bottom: 8px;
            }
            .label {
                font-family: 'Times New Roman', serif;
                font-size: 18px;
                font-weight: bold;
                color: #0056b3;
                font-style: italic;
                display: inline-block;
                width: 40%;
            }
            .text {
                font-family: 'Times New Roman', serif;
                font-size: 18px;
                color: #333;
                font-style: italic;
                display: inline-block;
                vertical-align: top;
                max-width: calc(100% - 200px);
                word-wrap: break-word;
            }
            .header {
                font-family: 'Times New Roman', serif;
                font-size: 20px;
                font-weight: bold;
                color: #222;
                margin-bottom: 15px;
            }
            a.client-link {
                color: green !important;
                text-decoration: underline !important;
                font-size: 16px;
                font-weight: bold;
                font-style: italic;
            }
            a.client-link:hover, a.client-link:visited, a.client-link:focus {
                color: green !important;
                text-decoration: underline !important;
            }
        </style>
    """, unsafe_allow_html=True)

    def render_line(label, value):
        return f"""<div class="line"><span class="label">{label}:</span><span class="text">{value if value else "N/A"}</span></div>"""

    html = f"""
    <div class="preview-container">
        <div class="header">📌 Report: {selected_report['session_type']} (Date: {selected_report['date']})</div>"""

    session_type = selected_report["session_type"]

    # ----------------- CONSULT REPORT -----------------
    if session_type == "Consult":
        html += render_line("📅 Session Date", form_data.get("session_date"))
        html += render_line("👥 Clients Seen", form_data.get("clients_seen"))
        remarks = form_data.get("remarks_per_client", {})

        if remarks:
            for i, (client, remark) in enumerate(remarks.items(), start=1):
                clean_name = re.sub(r"\s*-\s*\d{4}-\d{2}-\d{2}$", "", client).strip()
                clean_client = client.rstrip(" :")
                match = re.search(r"(APP-[\w\-]+)", clean_client)
                appointment_id = match.group(1) if match else "unknown"

                # Link navigates to the same app but with ?appointment_id=<id>
                html += f"""
                <div style='margin-left: 20px;'>
                    <div class="line">
                        <span class="label" style='font-size: 15px;'>
                            {i}. <a class="client-link" href="?appointment_id={appointment_id}">{clean_name}</a>:
                        </span>
                        <span class="text" style='color: black;'>{remark if remark else 'N/A'}</span>
                    </div>
                </div>"""
        else:
            html += render_line("👥 Clients Seen", "N/A")

        html += render_line("📝 Recommendations", form_data.get("general_remarks"))

    # ----------------- FOLLOW-UP REPORT -----------------
    elif session_type == "Follow-Up":
        html += render_line("👥 Clients Followed", form_data.get("clients_followed"))
        html += render_line("📝 Follow-Up Plan", form_data.get("follow_up_plan"))
        html += render_line("📌 Outcome/Remarks", form_data.get("outcome"))

    # ----------------- GROUP SESSION -----------------
    elif session_type == "Group Session":
        html += render_line("👥 Group Name", form_data.get("group_name"))
        html += render_line("🧑‍🤝‍🧑 Members Present", form_data.get("members_present"))
        html += render_line("📚 Topic", form_data.get("topic"))
        html += render_line("🎯 Theme", form_data.get("theme"))
        html += render_line("🗨️ Summary of Discussion", form_data.get("discussion_summary"))
        html += render_line("📝 Remarks", form_data.get("remarks"))
        html += render_line("➡️ Next Steps", form_data.get("next_steps"))

    # ----------------- SCHOOL SESSION -----------------
    elif session_type == "School Session":
        html += render_line("👥 Participants", form_data.get("participants"))
        html += render_line("🧩 Sub-Activities", form_data.get("sub_activities"))
        html += render_line("📝 Description", form_data.get("description"))
        html += render_line("📌 Outcome", form_data.get("outcome"))
        html += render_line("📝 Remarks", form_data.get("remarks"))

    # ----------------- CLASSROOM SESSION -----------------
    elif session_type == "Classroom Session":
        html += render_line("👥 Facilitators", ", ".join(form_data.get("facilitators", [])))
        for cls, streams in form_data.get("class_stream_map", {}).items():
            html += render_line(f"🏫 {cls}", ", ".join(streams))
        for topic, themes in form_data.get("topics_themes", {}).items():
            html += render_line("📚 Topic", topic)
            for theme, discussion in themes.items():
                html += render_line(f"📌 Theme: {theme}", discussion)
        html += render_line("🌟 Key Highlights", form_data.get("key_highlights"))
        html += render_line("💬 Feedback", form_data.get("feedback"))
        html += render_line("📝 Final Remarks", form_data.get("remarks"))

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # ----------------- APPOINTMENT DETAIL PAGE -----------------
    qs = st.query_params
    appointment_id = qs.get("appointment_id", None)

    if appointment_id:
        st.divider()
        st.subheader(f"📄 Appointment Details for {appointment_id}")
        from file_per_appointment import main as show_appointment
        show_appointment(appointment_id)







import re


# def render_single_report(conn, report_id: int):
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM session_reports WHERE id = ?", (report_id,))
#     selected_report = cursor.fetchone()
#     if not selected_report:
#         st.error("Report not found.")
#         return

#     try:
#         form_data = json.loads(selected_report["data"])
#     except Exception:
#         st.error("Invalid report data.")
#         return

#     # CSS Styling
#     st.markdown("""
#         <style>
#             .preview-container {
#                 background-color: #EAEAEA;
#                 border: 2px solid #B0B0B0;
#                 padding: 10px 20px;
#                 border-radius: 20px;
#                 box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
#                 margin-bottom: 15px;
#             }
#             .line {
#                 margin-bottom: 8px;
#             }
#             .label {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 18px;
#                 font-weight: bold;
#                 color: #0056b3;
#                 font-style: italic;
#                 display: inline-block;
#                 width: 40%;
#             }
#             .text {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 18px;
#                 color: #333;
#                 font-style: italic;
#                 display: inline-block;
#                 vertical-align: top;
#                 max-width: calc(100% - 200px);
#                 word-wrap: break-word;
#             }
#             .header {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 20px;
#                 font-weight: bold;
#                 color: #222;
#                 margin-bottom: 15px;
#             }
#             a.client-link {
#                 color: green !important;
#                 text-decoration: underline !important;
#                 cursor: pointer;
#             }
#         </style>
#     """, unsafe_allow_html=True)

#     def render_line(label, value):
#         return f"""<div class="line"><span class="label">{label}:</span><span class="text">{value if value else "N/A"}</span></div>"""

#     html = f"""
#     <div class="preview-container">
#         <div class="header">📌 Report: {selected_report['session_type']} (Date: {selected_report['date']})</div>"""

#     session_type = selected_report["session_type"]

#     # Handle Consult Reports
#     if session_type == "Consult":
#         html += render_line("📅 Session Date", form_data.get("session_date"))
#         html += render_line("👥 Clients Seen", form_data.get("clients_seen"))
#         remarks = form_data.get("remarks_per_client", {})

#         if remarks:
#             for i, (client, remark) in enumerate(remarks.items(), start=1):
#                 clean_name = re.sub(r"\s*-\s*\d{4}-\d{2}-\d{2}$", "", client).strip()
#                 match = re.search(r"(App-[\w\-]+)", client, re.IGNORECASE)
#                 appointment_id = match.group(1) if match else None

#                 if appointment_id:
#                     if st.button(f"🔗 {clean_name}", key=f"btn_{i}"):
#                         st.session_state["appointment_id"] = appointment_id
#                         st.rerun()

#                 html += f"""
#                 <div style='margin-left: 20px;'>
#                     <div class="line">
#                         <span class="label" style='font-size: 15px; color: green;'>
#                             {i}. {clean_name}:
#                         </span>
#                         <span class="text" style='color: black;'>{remark if remark else 'N/A'}</span>
#                     </div>
#                 </div>"""
#         else:
#             html += render_line("👥 Clients Seen", "N/A")
#         html += render_line("📝 Recommendations", form_data.get("general_remarks"))

#     # Other Session Types
#     elif session_type == "Follow-Up":
#         html += render_line("👥 Clients Followed", form_data.get("clients_followed"))
#         html += render_line("📝 Follow-Up Plan", form_data.get("follow_up_plan"))
#         html += render_line("📌 Outcome/Remarks", form_data.get("outcome"))

#     elif session_type == "Group Session":
#         html += render_line("👥 Group Name", form_data.get("group_name"))
#         html += render_line("🧑‍🤝‍🧑 Members Present", form_data.get("members_present"))
#         html += render_line("📚 Topic", form_data.get("topic"))
#         html += render_line("🎯 Theme", form_data.get("theme"))
#         html += render_line("🗨️ Summary of Discussion", form_data.get("discussion_summary"))
#         html += render_line("📝 Remarks", form_data.get("remarks"))
#         html += render_line("➡️ Next Steps", form_data.get("next_steps"))
#     html += "</div>"
#     st.markdown(html, unsafe_allow_html=True)
#     if "appointment_id" in st.session_state and st.session_state["appointment_id"]:
#         st.divider()
#         import file_per_appointment
#         file_per_appointment.main(st.session_state["appointment_id"])

# import re

# import streamlit as st
# import json

# def render_single_report(conn, report_id: int):
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM session_reports WHERE id = ?", (report_id,))
#     selected_report = cursor.fetchone()
#     if not selected_report:
#         st.error("Report not found.")
#         return

#     try:
#         form_data = json.loads(selected_report["data"])
#     except Exception:
#         st.error("Invalid report data.")
#         return

#     # If we are in detail mode (appointment clicked)
#     if st.session_state.get("appointment_id"):
#         appointment_id = st.session_state["appointment_id"]
#         st.subheader(f"📌 Viewing Appointment: {appointment_id}")

#         # Back button
#         if st.button("⬅ Back to Report"):
#             st.session_state["appointment_id"] = None
#             st.rerun()

#         # Show appointment details
#         file_per_appointment.main(appointment_id)
#         return

#     # ----------- LIST MODE -----------
#     st.markdown("""
#         <style>
#             .preview-container {
#                 background-color: #EAEAEA;
#                 border: 2px solid #B0B0B0;
#                 padding: 10px 20px;
#                 border-radius: 20px;
#                 box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
#                 margin-bottom: 15px;
#             }
#             .line {
#                 margin-bottom: 8px;
#             }
#             .label {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 18px;
#                 font-weight: bold;
#                 color: #0056b3;
#                 font-style: italic;
#                 display: inline-block;
#                 width: 40%;
#             }
#             .text {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 18px;
#                 color: #333;
#                 font-style: italic;
#                 display: inline-block;
#                 vertical-align: top;
#                 max-width: calc(100% - 200px);
#                 word-wrap: break-word;
#             }
#             .header {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 20px;
#                 font-weight: bold;
#                 color: #222;
#                 margin-bottom: 15px;
#             }
#             .link-btn {
#                 color: green;
#                 font-weight: bold;
#                 text-decoration: underline;
#                 cursor: pointer;
#                 background: none;
#                 border: none;
#                 padding: 0;
#                 font-size: 16px;
#             }
#         </style>
#     """, unsafe_allow_html=True)

#     def render_line(label, value):
#         return f"""<div class="line"><span class="label">{label}:</span><span class="text">{value if value else "N/A"}</span></div>"""

#     html = f"""
#     <div class="preview-container">
#         <div class="header">📌 Report: {selected_report['session_type']} (Date: {selected_report['date']})</div>"""

#     session_type = selected_report["session_type"]

#     if session_type == "Consult":
#         html += render_line("📅 Session Date", form_data.get("session_date"))
#         html += render_line("👥 Clients Seen", form_data.get("clients_seen"))
#         remarks = form_data.get("remarks_per_client", {})

#         if remarks:
#             for i, (client, remark) in enumerate(remarks.items(), start=1):
#                 clean_name = re.sub(r"\s*-\s*\d{4}-\d{2}-\d{2}$", "", client).strip()
#                 match = re.search(r"(App-[\w\-]+)", client, re.IGNORECASE)
#                 appointment_id = match.group(1) if match else None

#                 if appointment_id:
#                     # Render a clickable button for each appointment
#                     if st.button(f"🔗 {clean_name}", key=f"appt_{appointment_id}"):
#                         st.session_state["appointment_id"] = appointment_id
#                         st.rerun()

#                 html += f"""
#                 <div style='margin-left: 20px;'>
#                     <div class="line">
#                         <span class="label" style='font-size: 15px; color: green;'>
#                             {i}. {clean_name}:
#                         </span>
#                         <span class="text" style='color: black;'>{remark if remark else 'N/A'}</span>
#                     </div>
#                 </div>"""
#         else:
#             html += render_line("👥 Clients Seen", "N/A")
#         html += render_line("📝 Recommendations", form_data.get("general_remarks"))

#     html += "</div>"
#     st.markdown(html, unsafe_allow_html=True)


# def display_reports_section(conn, compiled_by):
#     st.markdown("""
#         <style>
#             .preview-container {
#                 background-color: #EAEAEA;
#                 border: 2px solid #B0B0B0;
#                 padding: 10px 20px;
#                 border-radius: 20px;
#                 box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
#                 margin-bottom: 15px;
#             }
#             .line {
#                 margin-bottom: 8px;
#             }
#             .label {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 18px;
#                 font-weight: bold;
#                 color: #0056b3;
#                 font-style: italic;
#                 display: inline-block;
#                 width: 40%;
#             }
#             .text {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 18px;
#                 color: #333;
#                 font-style: italic;
#                 display: inline-block;
#                 vertical-align: top;
#                 max-width: calc(100% - 200px);
#                 word-wrap: break-word;
#             }
#             .header {
#                 font-family: 'Times New Roman', serif;
#                 font-size: 20px;
#                 font-weight: bold;
#                 color: #222;
#                 margin-bottom: 15px;
#             }
#         </style>
#     """, unsafe_allow_html=True)

#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM session_reports WHERE compiled_by = ? ORDER BY date DESC", (compiled_by,))
#     reports = cursor.fetchall()
#     if not reports:
#         st.info("No reports found.")
#         return

#     report_options = [f"{r['id']} - {r['session_type']} - {r['date']}" for r in reports]
#     selected_report_str = st.selectbox("Select report to view", options=report_options)
#     selected_report_id = int(selected_report_str.split("|")[0].strip())
#     selected_report = next((r for r in reports if r["id"] == selected_report_id), None)
#     if not selected_report:
#         st.error("Selected report not found.")
#         return
#     try:
#         form_data = json.loads(selected_report["data"])
#     except Exception:
#         st.error("Failed to load report data.")
#         return
#     def render_line(label, value):
#         return f"""<div class="line"><span class="label">{label}:</span><span class="text">{value if value else "N/A"}</span></div>"""
#     html = f"""
#     <div class="preview-container">
#         <div class="header">📌 Report: {selected_report['session_type']} (Date: {selected_report['date']})</div>"""

#     session_type = selected_report["session_type"]
#     if session_type == "Consult":
#         html += render_line("📅 Session Date", form_data.get("session_date"))
#         html += render_line("👥 Clients Seen", form_data.get("clients_seen"))
#         remarks = form_data.get("remarks_per_client", {})
#         if remarks:
#             for i, (client, remark) in enumerate(remarks.items(), start=1):
#                 clean_name = re.sub(r"\s*-\s*\d{4}-\d{2}-\d{2}$", "", client).strip()
#                 clean_client = client.rstrip(" :") 
#                 match = re.search(r"(APP-[\w\-]+)", clean_client)
#                 appointment_id = match.group(1) if match else "unknown"
#                 html += f"""
#                 <div style='margin-left: 20px;'>
#                     <div class="line">
#                         <span class="label" style='color: green; font-size : 15px;'>
#                             {i}. <a href="?appointment_id={appointment_id}" style="color: green; text-decoration: underline;">{clean_name}</a>:
#                         </span>
#                         <span class="text" style='color: black;'>{remark if remark else 'N/A'}</span>
#                     </div>
#                 </div>"""

#         else:
#             html += render_line("👥 Clients Seen", "N/A")
#         html += render_line("📝Recommendations", form_data.get("general_remarks"))
#         html += "</div>"

#     elif session_type == "Follow-Up":
#         html += render_line("👥 Clients Followed", form_data.get("clients_followed"))
#         html += render_line("📝 Follow-Up Plan", form_data.get("follow_up_plan"))
#         html += render_line("📌 Outcome/Remarks", form_data.get("outcome"))

#     elif session_type == "Group Session":
#         html += render_line("👥 Group Name", form_data.get("group_name"))
#         html += render_line("🧑‍🤝‍🧑 Members Present", form_data.get("members_present"))
#         html += render_line("📚 Topic", form_data.get("topic"))
#         html += render_line("🎯 Theme", form_data.get("theme"))
#         html += render_line("🗨️ Summary of Discussion", form_data.get("discussion_summary"))
#         html += render_line("📝 Remarks", form_data.get("remarks"))
#         html += render_line("➡️ Next Steps", form_data.get("next_steps"))

#     elif session_type == "School Session":
#         html += render_line("👥 Participants", form_data.get("participants"))
#         html += render_line("🧩 Sub-Activities", form_data.get("sub_activities"))
#         html += render_line("📝 Description", form_data.get("description"))
#         html += render_line("📌 Outcome", form_data.get("outcome"))
#         html += render_line("📝 Remarks", form_data.get("remarks"))

#     elif session_type == "Classroom Session":
#         html += render_line("👥 Facilitators", ", ".join(form_data.get("facilitators", [])))
#         for cls, streams in form_data.get("class_stream_map", {}).items():
#             html += render_line(f"🏫 {cls}", ", ".join(streams))
#         for topic, themes in form_data.get("topics_themes", {}).items():
#             html += render_line("📚 Topic", topic)
#             for theme, discussion in themes.items():
#                 html += render_line(f"📌 Theme: {theme}", discussion)
#         html += render_line("🌟 Key Highlights", form_data.get("key_highlights"))
#         html += render_line("💬 Feedback", form_data.get("feedback"))
#         html += render_line("📝 Final Remarks", form_data.get("remarks"))

#     html += "</div>"
#     st.markdown(html, unsafe_allow_html=True)

# def get_full_name_from_username(username):
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
#     result = cursor.fetchone()
#     conn.close()
#     return result["full_name"] if result else None


import json
import os

SEEN_FILE = "seen_reports.json"

def load_seen_reports():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_reports(seen_set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_set), f)

def detailed_reports_section(conn):
    st.markdown("""
        <style>
        /* Enclose entire table */
        .table-container {
            border: 2px solid #1e90ff;
            border-radius: 6px;
            margin-top: 15px;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Remove spacing between columns */
        .stColumns > div {
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin: 0 !important;
        }

        /* Remove spacing between rows */
        .block-container div[data-testid="column"] {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            margin: 0px !important;
        }

        /* Header row styling */
        .header-row {
            background-color: #1e90ff;
            color: white;
            padding: 10px 12px;
            font-weight: 700;
            border-bottom: 1px solid #0b3d66;
            font-size: 16px;
            text-align: left;
        }

        /* Data row cell */
        .data-row {
            background-color: black;
            color: #d7d7d7;
            padding: 10px 12px !important;
            border-bottom: 1px solid #333;
            font-size: 15px;
        }

        /* Alternate row colors */
        .row-even .data-row {
            background-color: #1a1a1a;
        }
        .row-odd .data-row {
            background-color: #121212;
        }

        /* Status colors */
        .status-new {
            color: #ff4d4d;
            font-weight: 700;
        }
        .status-seen {
            color: #32cd32;
            font-weight: 700;
        }

        button:hover {
            background-color: #155d9c;
            border-color: #0b3d66;
        }

        /* Details section */
        .report-details {
            background: #222;
            padding: 10px;
            margin-top: 10px;
            border-radius: 4px;
            font-family: 'Times New Roman', serif;
            font-size: 15px;
            color: #eee;
            border: 1.5px solid #1e90ff;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("📋 Detailed Session Reports")
    reports = fetch_reports(conn)
    if reports.empty:
        st.info("No reports found.")
        return
    therapists = ["All"] + sorted(reports['compiled_by'].unique())
    with st.sidebar.expander('FILTER', expanded=True):
        selected_therapist = st.selectbox("Filter by Therapist", therapists)
        available_years = sorted(reports['date'].dt.year.unique())
        selected_years = st.multiselect("Select Year(s)", available_years, default=available_years)
        if selected_years:
            reports = reports[reports['date'].dt.year.isin(selected_years)]
            available_months = sorted(reports['date'].dt.month.unique())
            month_names = [datetime(1900, m, 1).strftime('%B') for m in available_months]
            month_map = dict(zip(month_names, available_months))
            selected_months = st.multiselect("Select Month(s)", month_names)
            if selected_months:
                month_nums = [month_map[m] for m in selected_months]
                reports = reports[reports['date'].dt.month.isin(month_nums)]
        min_date, max_date = reports['date'].min(), reports['date'].max()
        start_date, end_date = st.date_input(
            "Select Date Range", 
            [min_date, max_date]
        )
    if isinstance(start_date, datetime) and isinstance(end_date, datetime):
        reports = reports[(reports['date'].dt.date >= start_date) & (reports['date'].dt.date <= end_date)]

    if selected_therapist != "All":
        reports = reports[reports['compiled_by'] == selected_therapist]

    if "expanded_report_id" not in st.session_state:
        st.session_state.expanded_report_id = None
    seen_reports = load_seen_reports()
    with st.expander('Table View', expanded=True):
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        header_cols = st.columns([0.5, 2, 2, 2, 1, 1])
        header_cols[0].markdown("<div class='header-row'>#</div>", unsafe_allow_html=True)
        header_cols[1].markdown("<div class='header-row'>Therapist</div>", unsafe_allow_html=True)
        header_cols[2].markdown("<div class='header-row'>Activity Report</div>", unsafe_allow_html=True)
        header_cols[3].markdown("<div class='header-row'>Date Submitted</div>", unsafe_allow_html=True)
        header_cols[4].markdown("<div class='header-row'>Status</div>", unsafe_allow_html=True)
        header_cols[5].markdown("<div class='header-row'>Action</div>", unsafe_allow_html=True)

        for idx, r in enumerate(reports.itertuples(), start=1):
            report_id = r.id
            row_class = "row-even" if idx % 2 == 0 else "row-odd"
            cols = st.columns([0.5, 2, 2, 2, 1, 1])
            cols[0].markdown(f"<div class='data-row {row_class}'>{idx}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div class='data-row {row_class}'>{r.compiled_by}</div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div class='data-row {row_class}'>{r.session_type}</div>", unsafe_allow_html=True)
            cols[3].markdown(f"<div class='data-row {row_class}'>{r.date.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

            if report_id in seen_reports:
                cols[4].markdown(f"<div class='data-row {row_class} status-seen'>Seen</div>", unsafe_allow_html=True)
            else:
                cols[4].markdown(f"<div class='data-row {row_class} status-new'>New</div>", unsafe_allow_html=True)

            btn_label = "Hide" if st.session_state.expanded_report_id == report_id else "View"
            if cols[5].button(btn_label, key=f"toggle_report_{report_id}"):
                if st.session_state.expanded_report_id == report_id:
                    st.session_state.expanded_report_id = None
                else:
                    st.session_state.expanded_report_id = report_id
                    seen_reports.add(report_id)
                    save_seen_reports(seen_reports)
                st.rerun()

    if st.session_state.expanded_report_id:
        render_single_report(conn, st.session_state.expanded_report_id)
      






def main():
    conn = create_connection()  
    detailed_reports_section(conn)
    conn.close()
if __name__ == "__main__":
    main()