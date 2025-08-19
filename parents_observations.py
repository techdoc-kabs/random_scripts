import streamlit as st
import sqlite3
from datetime import date
import os, base64
from streamlit_javascript import st_javascript
import pandas as pd 
DB_PATH = "users_db.db"

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
def create_connection(db_path=DB_PATH):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None


def get_class_options():
    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT class FROM users WHERE class IS NOT NULL AND class != ''")
        classes = [row[0] for row in cur.fetchall()]
        conn.close()
        classes.sort()
        classes.append("Other (specify)")
        return classes
    return ["Other (specify)"]

def get_stream_options():
    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT stream FROM users WHERE stream IS NOT NULL AND stream != ''")
        streams = [row[0] for row in cur.fetchall()]
        conn.close()
        streams.sort()
        streams.append("Other (specify)")
        return streams
    return ["Other (specify)"]

def add_class_if_new(new_class):
    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE class = ?", (new_class,))
        exists = cur.fetchone()
        if not exists:
            cur.execute("INSERT INTO users (class) VALUES (?)", (new_class,))
            conn.commit()
        conn.close()

def add_stream_if_new(new_stream):
    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE stream = ?", (new_stream,))
        exists = cur.fetchone()
        if not exists:
            cur.execute("INSERT INTO users (stream) VALUES (?)", (new_stream,))
            conn.commit()
        conn.close()


def parents_observations():
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS parents_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- observation_type TEXT,
            class_name TEXT,
            stream_name TEXT,
            student_name TEXT,
            date_observed TEXT,
            observed_behavior TEXT,
            description TEXT,
            possible_cause TEXT,
            recommendation TEXT,
            urgency TEXT,
            submitted_by TEXT,
            submitted_on TEXT,
            response TEXT,
            responder TEXT,
            response_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_observation(data):
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO parents_observations (
            class_name, stream_name, student_name,
            date_observed, observed_behavior, description,
            possible_cause, recommendation, urgency,
            submitted_by, submitted_on
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()



# ---------- App ----------
parents_observations()
class_options = get_class_options()
stream_options = get_stream_options()

def get_full_name_from_username(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result["full_name"] if result else None

def fetch_users(db, search_input):
    cursor = db.cursor()
    if search_input.strip().upper().startswith("STUD-") or search_input.isdigit():
        query = """
        SELECT user_id, full_name, age, gender, class, stream
        FROM users
        WHERE user_id = ?
        """
        cursor.execute(query, (search_input.strip(),))
    else: 
        name_parts = search_input.strip().split()
        query_conditions = []
        params = []

        if len(name_parts) == 2:
            first_name, last_name = name_parts
            query_conditions.append("full_name LIKE ?")
            query_conditions.append("full_name LIKE ?")
            params.extend([f"%{first_name} {last_name}%", f"%{last_name} {first_name}%"])
        else:
            query_conditions.append("full_name LIKE ?")
            params.append(f"%{search_input}%")
        query = f"""
        SELECT user_id, full_name, age, gender, class, stream
        FROM users
        WHERE {" OR ".join(query_conditions)}
        """
        cursor.execute(query, tuple(params))
    return cursor.fetchall()


def multiselect_with_other(label, options, default=None):
    if "Other (specify)" not in options:
        options.append("Other (specify)")

    selected = st.multiselect(label, options, default=default if default else [])
    final_selection = [s for s in selected if s != "Other (specify)"]
    if "Other (specify)" in selected:
        custom_value = st.text_input(f"Specify other {label.lower()}", "")
        if custom_value.strip():
            final_selection.append(custom_value.strip())

    return final_selection


def view_observations():
    set_full_page_background('images/black_strip.jpg')
    conn = create_connection()

    query = """
        SELECT 
             class_name, stream_name, student_name,
            date_observed, observed_behavior, description,
            possible_cause, recommendation, urgency,
            submitted_by, submitted_on,
            response, responder, response_date
        FROM parents_observations
        ORDER BY date_observed DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.info("No observations found.")
        return

    df.index = df.index + 1
    df["date_observed"] = pd.to_datetime(df["date_observed"]).dt.strftime('%Y-%m-%d')
    df["submitted_on"] = pd.to_datetime(df["submitted_on"]).dt.strftime('%Y-%m-%d')
    df["response_date"] = pd.to_datetime(df["response_date"], errors='coerce').dt.strftime('%Y-%m-%d')
    df["response_date"] = df["response_date"].fillna('—')
    df["response"] = df["response"].fillna('—')
    df["responder"] = df["responder"].fillna('—')

    st.markdown("""
        <style>
            .obs-table {
                border-collapse: collapse;
                width: 100%;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 15px;
                color: #eee;
            }
            .obs-table th, .obs-table td {
                border: 1px solid #444;
                padding: 10px 12px;
                text-align: left;
                vertical-align: top;
            }
            .obs-table th {
                background-color: #4A90E2;
                color: white;
                font-weight: 600;
            }
            .obs-table tbody tr:nth-child(even) {
                background-color: #1e1e1e;
            }
            .obs-table tbody tr:nth-child(odd) {
                background-color: #2c2c2c;
            }
            .type-cell { color: #FF9800; font-weight: 600; }
            .behavior-cell { color: #8BC34A; font-weight: 600; }
            .cause-cell { color: #E91E63; font-weight: 500; }
            .recommend-cell { color: #2196F3; font-style: italic; }
            .response-cell { color: #FFD700; font-style: italic; } 
            .meta-cell { color: #bbbbbb; font-size: 13px; }
            .urgency-low { color: #4CAF50; font-weight: bold; }
            .urgency-moderate { color: #FFC107; font-weight: bold; }
            .urgency-high { color: #F44336; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    table_html = '<table class="obs-table">'
    table_html += """<thead>
            <tr>
                <th>#</th>
                <th>Student/Class</th>
                <th>Date Observed</th>
                <th>Observed Behavior</th>
                <th>Description</th>
                <th>Possible Cause</th>
                <th>Recommendation</th>
                <th>Urgency</th>
                <th>Submitted By</th>
                <th>Date Submitted</th>
                <th>Response</th>
                <th>Responder</th>
                <th>Response Date</th>
            </tr>
        </thead>
        <tbody>
    """
    for idx, row in df.iterrows():
        urgency_class = {
            "Low": "urgency-low",
            "Moderate": "urgency-moderate",
            "High": "urgency-high"
        }.get(row['urgency'], "meta-cell")
        if row['student_name']:
            student_class_display = f"{row['student_name']} ({row['class_name']} - {row['stream_name']})"
        else:
            student_class_display = f"{row['class_name']} - {row['stream_name']}"

        table_html += f"""<tr>
                <td>{idx}</td>
                <td class="meta-cell">{student_class_display}</td>
                <td class="meta-cell">{row['date_observed']}</td>
                <td class="behavior-cell">{row['observed_behavior']}</td>
                <td class="meta-cell">{row['description']}</td>
                <td class="cause-cell">{row['possible_cause']}</td>
                <td class="recommend-cell">{row['recommendation']}</td>
                <td class="{urgency_class}">{row['urgency']}</td>
                <td class="meta-cell">{row['submitted_by']}</td>
                <td class="meta-cell">{row['submitted_on']}</td>
                <td class="response-cell">{row['response']}</td>
                <td class="meta-cell">{row['responder']}</td>
                <td class="meta-cell">{row['response_date']}</td>
            </tr>
        """
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

def update_parents_observations_schema():
    conn = create_connection()
    c = conn.cursor()
    columns_to_add = {
        "response": "TEXT",
        "responder": "TEXT",
        "response_date": "TEXT"
    }
    for col, col_type in columns_to_add.items():
        try:
            c.execute(f"ALTER TABLE parents_observations ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            # Column already exists
            pass
    conn.commit()
    conn.close()

# ---------- MAIN ----------
def main():
    parents_observations()
    update_parents_observations_schema()
    class_options = get_class_options()
    stream_options = get_stream_options()
    username = st.session_state.get("user_name")
    parents_name = get_full_name_from_username(username)
    device_width = st_javascript("window.innerWidth", key="menu_device_width")
    if device_width is None:
        st.stop()
    is_mobile = device_width < 704
    margin_right = "300px" if not is_mobile  else "0"
    font_css = f"""
    <style>
    /* Default tab appearance */
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {{
      font-size: 16px;
      font-weight: bold;
      color: white;
      padding: 4px 10px;
      margin: 0;
      border: 2px solid brown;
      border-radius: 3%;
      background-color: orange;
      box-sizing: border-box;
      transition: all 0.3s ease-in-out;
    }}

    /* Active tab: make it green */
    button[data-baseweb="tab"][aria-selected="true"] > div[data-testid="stMarkdownContainer"] > p {{
      background-color: green !important;
      border-color: darkgreen !important;
      color: white !important;
    }}

    /* Add spacing between tabs */
    div[role="tablist"] > button {{
      margin-right: {margin_right};
    }}

    /* Content area of each tab */
    section[role="tabpanel"] {{
      padding: 16px 24px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      font-size: 18px;
      color: #333333;
    }}

    /* Style tables */
    section[role="tabpanel"] table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 2px;
    }}

    section[role="tabpanel"] th, section[role="tabpanel"] td {{
      border: 1px solid #ddd;
      padding: 8px;
    }}

    section[role="tabpanel"] th {{
      background-color: #00897b;
      color: red;
      text-align: left;
    }}
    </style>
    """
    st.markdown(font_css, unsafe_allow_html=True)
    section = st.tabs(["REPORT ISSUES", "SUBMISSIONS"])
    with section[0]:
        container = st.sidebar if not is_mobile else st
        student_name = ""
        student_class = None
        student_stream = None
        class_name = None
        stream_name = None
        selected_record = None
        st.markdown("##### Please help us understand your child by document any unusual behavior that you think need special attention and how you think we can be of help")
        container.subheader("STUDENT DETAILS")
        with container.expander("🔍 SEARCH", expanded=True):
            search_input = st.text_input("Enter Name or Student ID", "")
        results = fetch_users(create_connection(), search_input) if search_input.strip() else []
        if results:
            selection_container = st.sidebar if not is_mobile else st
            with selection_container.expander("Select", expanded=True):
                st.write(f"**{len(results)} result(s) found**")
                options = {f"{r['full_name']} - {r['user_id']}": r for r in results}
                selected_option = st.selectbox("Select a record:", list(options.keys()))
                selected_record = options[selected_option]
        if selected_record:
            def format_line(label, value):
                return f"<div style='margin-bottom:6px;'><span style='color:#c0392b; font-weight:bold;'>{label}:</span> <span style='color:#27ae60;'>{value}</span></div>"
            profile_fields = [
                ("Student ID", selected_record['user_id']),
                ("Name", selected_record['full_name']),
                ("Age", f"{selected_record['age']} Years"),
                ("Gender", selected_record['gender']),
                ("Class", selected_record['class']),
                ("Stream", selected_record['stream']),]
            profile_html = ''.join([format_line(label, value) for label, value in profile_fields])
            profile_container = st.sidebar if not is_mobile else st
            with profile_container.expander("STUDENT PROFILE", expanded=True):
                st.markdown(profile_html, unsafe_allow_html=True)
            student_name = selected_record['full_name']
            student_class = selected_record['class']
            student_stream = selected_record['stream']
        with st.expander('OBSERVATION FORM', expanded=True):
            col1,col2 = st.columns([1, 2])
            with col1:
                student_name = st.text_input("Student Name", value=student_name)
                class_name = multiselect_with_other("Class", class_options, default=[student_class] if student_class else [])
                stream_name = multiselect_with_other("Stream", stream_options, default=[student_stream] if student_stream else [])
                date_observed = st.date_input("Date of Observation", value=date.today())
            with col2:
           
                observed_behavior = multiselect_with_other(
                    "Observed Behavior", [
                        "Withdrawal from others", "Drop in academic performance",
                        "Aggressive behavior", "Unusual emotional reactions",
                        "Excessive absenteeism", "Other (specify)"
                    ])
                description = st.text_area("Please describe the observation")
                possible_cause = multiselect_with_other(
                    "Possible Cause / Trigger", [
                        "Stress from home", "Peer conflicts", "Major life change",
                        "Learning difficulties", "Unknown", "Other (specify)"
                    ])
                recommendation = multiselect_with_other(
                    "Recommended Action", [
                        " Counselor's interventon"," teacher's interventon",
                         "Other (specify)"])
            with col1:
                urgency = st.radio(
"Urgency Level",
["Low", "Moderate", "High"],
horizontal=True)

            submitted_by = parents_name   
            if st.button("Submit Observation"):
                if not observed_behavior:
                    st.error("⚠ Please specify the observed behavior.")
                elif not possible_cause:
                    st.error("⚠ Please specify the possible cause.")
                elif not recommendation:
                    st.error("⚠ Please specify the recommendation.")
                else:
                    for c in class_name:
                        if c not in class_options:
                            add_class_if_new(c)
                    for s in stream_name:
                        if s not in stream_options:
                            add_stream_if_new(s)
                    save_observation((
                        ", ".join(class_name),
                        ", ".join(stream_name),
                        student_name,
                        date_observed.strftime("%Y-%m-%d"),
                        ", ".join(observed_behavior),
                        description,
                        ", ".join(possible_cause),
                        ", ".join(recommendation),
                        urgency,
                        submitted_by,
                        date.today().strftime("%Y-%m-%d")
                    ))
                    st.success(f"✅ Thank you Mr/Miss {parents_name} for your submission!")

    with section[1]:
        view_observations()
if __name__ == "__main__":
    main()

