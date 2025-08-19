DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime
import os, base64
import pandas as pd
from streamlit_option_menu import option_menu
import calendar

DB = "users_db.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None


######## summary reports
def _extract_meta(session_type: str, data_json: dict):
    """
    Extract participants count for all session types.
    Special logic for 'Consult' -> uses clients_seen or falls back to remarks_per_client length.
    """
    participants = None
    class_name  = data_json.get("class", None)
    term_name   = data_json.get("term", None)

    session_type_lower = session_type.strip().lower()

    if session_type_lower == "consult":
        participants = data_json.get("clients_seen", 0)
        try:
            participants = int(participants)
        except (TypeError, ValueError):
            participants = 0

        # Fallback: count remarks_per_client if clients_seen is 0
        if participants == 0:
            remarks = data_json.get("remarks_per_client", {})
            if isinstance(remarks, dict):
                participants = len(remarks)

    elif session_type_lower == "follow-up":
        participants = data_json.get("clients_followed", 0)

    elif session_type_lower == "group session":
        members = data_json.get("members_present", "")
        participants = len([m for m in members.split(",") if m.strip()])

    elif session_type_lower == "school session":
        participants = data_json.get("participants", 0)

    elif session_type_lower == "classroom session":
        streams_map = data_json.get("class_stream_map", {})
        participants = sum(len(v) for v in streams_map.values())

    try:
        participants = int(participants) if participants is not None else None
    except (TypeError, ValueError):
        participants = None

    return participants, class_name, term_name

@st.cache_data(show_spinner=False)
def build_activity_summary(_conn):
    df = pd.read_sql(
        "SELECT date, session_type, compiled_by, data FROM session_reports",
        _conn
    )
    df["date"] = pd.to_datetime(df["date"]).dt.date

    meta = df.apply(
        lambda row: _extract_meta(
            row["session_type"],
            json.loads(row["data"])
        ),
        axis=1, result_type="expand",
    )
    meta.columns = ["participants", "class", "term"]
    return pd.concat([df, meta], axis=1)


# -------------------------------------------------------------
def activity_summary_section(conn):
    df = build_activity_summary(conn)
    if df.empty:
        st.info("No session data found.")
        return

    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    with st.sidebar:
        st.markdown("### 🔍 Filters")

        year_options = sorted(df["year"].unique(), reverse=True)
        selected_years = st.multiselect("Year", year_options, default=year_options)
        df_year = df[df["year"].isin(selected_years)] if selected_years else df.copy()

        month_map = {i: calendar.month_name[i] for i in range(1, 13)}
        month_options = sorted(df_year["month"].unique())
        selected_months = st.multiselect(
            "Month",
            [month_map[m] for m in month_options],
            default=[month_map[m] for m in month_options],
        )
        selected_month_nums = [k for k, v in month_map.items() if v in selected_months]
        df_month = df_year[df_year["month"].isin(selected_month_nums)] if selected_month_nums else df_year.copy()

        if df_month.empty:
            st.warning("No data available for selected year/month combination.")
            return

        start_date = st.date_input("Start date", value=df_month["date"].min().date())
        end_date = st.date_input("End date", value=df_month["date"].max().date())

        df_range = df_month[
            (df_month["date"] >= pd.to_datetime(start_date)) &
            (df_month["date"] <= pd.to_datetime(end_date))
        ]

        classes = sorted(df_range["class"].dropna().unique())
        terms = sorted(df_range["term"].dropna().unique())
        therapists = sorted(df_range["compiled_by"].dropna().unique())

        cls_filter = st.multiselect("Class (optional)", classes)
        term_filter = st.multiselect("Term (optional)", terms)
        thp_filter = st.multiselect("Therapist (optional)", therapists)

    # Apply filters
    mask = pd.Series(True, index=df_range.index)
    if cls_filter:
        mask &= df_range["class"].isin(cls_filter)
    if term_filter:
        mask &= df_range["term"].isin(term_filter)
    if thp_filter:
        mask &= df_range["compiled_by"].isin(thp_filter)

    filtered = df_range[mask].copy()

    # Grouped summary
    summary = (
        filtered
        .groupby(["date", "session_type"], as_index=False)
        .agg(
            no_of_activities=("session_type", "size"),
            number_of_participants=("participants", "sum"),
        )
        .rename(columns={
            "session_type": "activity",
            "no_of_activities": "no of activities",
            "number_of_participants": "number of participants",
        })[["date", "activity", "no of activities", "number of participants"]]
    )

    if summary.empty:
        st.info("No results to display for the selected filters.")
        return

    table_rows = ""
    for i, row in summary.iterrows():
        table_rows += f""" <tr><td>{i+1}</td><td>{row['date'].strftime('%Y-%m-%d')}</td><td>{row['activity']}</td>
            <td>{int(row['no of activities'])}</td>
            <td>{int(row['number of participants']) if pd.notna(row['number of participants']) else 'N/A'}</td>
        </tr>
        """

    table_html = f"""
    <style>
        table.zebra {{
            border-collapse: collapse;
            width: 100%;
        }}
        table.zebra th, table.zebra td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
            color: white;
        }}
        table.zebra tr:nth-child(odd) {{
            background-color: #000000;
        }}
        table.zebra tr:nth-child(even) {{
            background-color: #1a1a1a;
        }}
        table.zebra th {{
            background-color: #4CAF50;
            color: white;
        }}
    </style>

    <table class="zebra">
        <thead>
            <tr>
                <th>#</th>
                <th>Date</th>
                <th>Activity</th>
                <th>No of Activities</th>
                <th>Number of Participants</th>
            </tr>
        </thead>
        <tbody>{table_rows}</tbody>
    </table>
    """

    st.markdown(table_html, unsafe_allow_html=True)


##### DRIVER CODE
def main():
    conn = create_connection()
    activity_summary_section(conn)
    conn.close()

if __name__ == "__main__":
    main()
