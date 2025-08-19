DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import json
from datetime import datetime
import os, base64
import json, re, sqlite3
import pandas as pd
from streamlit_option_menu import option_menu
def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None


@st.cache_data(show_spinner=False)
def build_classroom_topics_df(_conn):
    df = pd.read_sql(
        """
        SELECT date, compiled_by, data
        FROM session_reports
        WHERE session_type = 'Classroom Session'
        ORDER BY date DESC
        """,
        _conn,
        parse_dates=["date"],
    )

    records = []
    for _, row in df.iterrows():
        try:
            payload = json.loads(row["data"])
        except Exception:
            continue
        topics_map = payload.get("topics_themes", {})
        for topic, theme_dict in topics_map.items():
            for theme in theme_dict.keys():          # we only need the theme label
                records.append(
                    {
                        "date":       row["date"].date(),
                        "year":       row["date"].year,
                        "therapist":  row["compiled_by"],
                        "topic":      topic,
                        "theme":      theme,
                    }
                )
    return pd.DataFrame(records)


def display_classroom_summary(conn):
    st.markdown("""
        <style>
            table.zebra {border-collapse: collapse; width: 100%;}
            table.zebra th, table.zebra td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
                font-family: 'Segoe UI', sans-serif;
                vertical-align: top;
                white-space: pre-wrap;
            }
            table.zebra tr:nth-child(even) {background-color: #f9f9f9;}
            table.zebra th {
                background-color: #4CAF50;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("📘 Classroom Session Summary Table")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, compiled_by, data
        FROM session_reports
        WHERE session_type = 'Classroom Session'
        ORDER BY date DESC
    """)
    rows = cursor.fetchall()
    if not rows:
        st.warning("No Classroom Session reports found.")
        return
    table_rows = ""
    for row in rows:
        try:
            data = json.loads(row["data"])
        except Exception:
            continue

        date = row["date"].split(" ")[0]
        therapists = ", ".join(data.get("facilitators", []))

        class_stream_map = data.get("class_stream_map", {})
        class_stream_str = "; ".join(
            f"{cls}: {', '.join(streams)}" for cls, streams in class_stream_map.items() if streams
        ) or "N/A"

        topics_themes = data.get("topics_themes", {})
        
        # For each topic, combine all unique themes into one cell, no discussions, themes under same topic joined by comma
        for topic, theme_discussions in topics_themes.items():
            # Extract unique themes, ignoring discussions
            unique_themes = set(theme_discussions.keys())
            themes_cell = ", ".join(sorted(unique_themes))

            table_rows += f"""<tr><td>{date}</td><td>{therapists}</td><td>{class_stream_str}</td><td>{topic}</td><td>{themes_cell}</td></tr>
            """
    table_html = f"""<table class="zebra"><thead><tr><th>Date</th><th>Facilitators</th><th>Class - Streams</th><th>Topic</th>
                <th>Themes</th></tr></thead><tbody>{table_rows}</tbody></table>"""
    st.markdown(table_html, unsafe_allow_html=True)


def main():
    conn = create_connection()
    display_classroom_summary(conn)
    conn.close()
if __name__ == "__main__":
    main()