DB_PATH = "users_db.db"
import pandas as pd
import os
import appointments
from datetime import datetime
import seaborn as sns
import sqlite3

import plotly.express as px
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import base64
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import tempfile
from reportlab.platypus import Image
import io

def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None


def fetch_screen_data(db):
    cursor = db.cursor()
    cursor.execute("""
        SELECT appointment_id, name, screen_type, class, stream, term, client_type,
               tools, tools_statuses
        FROM appointments
        WHERE tools IS NOT NULL AND tools != '' AND actions = 'screen'
        ORDER BY appointment_id
    """)
    screens = cursor.fetchall()
    cursor.close()

    records = []
    for row in screens:
        try:
            tools_list = json.loads(row["tools"]) if row["tools"] else []
        except Exception as e:
            st.warning(f"Failed to parse tools for appointment_id {row['appointment_id']}: {e}")
            tools_list = []

        try:
            tools_statuses = json.loads(row["tools_statuses"]) if row["tools_statuses"] else {}
        except Exception as e:
            st.warning(f"Failed to parse tools_statuses for appointment_id {row['appointment_id']}: {e}")
            tools_statuses = {}

        for tool in tools_list:
            status = tools_statuses.get(tool, "Pending")
            records.append({
                "appointment_id": row["appointment_id"],
                "name": row["name"],
                "client_type": row["client_type"],
                "class": row["class"],
                "stream": row["stream"],
                "term": row["term"],
                "screen_type": row["screen_type"],
                "tool": tool,
                "status": status
            })

    return pd.DataFrame(records)


def generate_summary_dataframe(db, appointment_id):
    try:
        phq9_df = fetch_latest_phq9(db, appointment_id)
        gad7_df = fetch_latest_gad7(db, appointment_id)
        
        if not phq9_df.empty and not gad7_df.empty:
            summary_data = {
                "PHQ Score": phq9_df["PHQ Score"].values[0],
                "Depression Status": phq9_df["Depression Status"].values[0],
                'Suicide Score': phq9_df['Suicide Response'].values[0],
                "Suicide Risk": phq9_df["Suicide Risk"].values[0],
                "GAD-7 Score": gad7_df["GAD-7 Score"].values[0],
                "Anxiety Status": gad7_df["Anxiety Status"].values[0]
            }
            summary_df = pd.DataFrame([summary_data])
            return style_summary_dataframe(summary_df)

        elif not phq9_df.empty:
            summary_data = {
                "PHQ Score": phq9_df["PHQ Score"].values[0],
                "Depression Status": phq9_df["Depression Status"].values[0],
                'Suicide Score': phq9_df['Suicide Response'].values[0],
                "Suicide Risk": phq9_df["Suicide Risk"].values[0],
                "GAD-7 Score": "N/A",
                "Anxiety Status": "N/A"
            }
            summary_df = pd.DataFrame([summary_data])
            return style_summary_dataframe(summary_df)

        elif not gad7_df.empty:
            summary_data = {
                "PHQ Score": "N/A",
                "Depression Status": "N/A",
                'Suicide Score':'N/A',
                "Suicide Risk": "N/A",
                "GAD-7 Score": gad7_df["GAD-7 Score"].values[0],
                "Anxiety Status": gad7_df["Anxiety Status"].values[0]
            }
            summary_df = pd.DataFrame([summary_data])
            summary_df = summary_df.reset_index(drop=True)
            summary_df.index = summary_df.index + 1
            return style_summary_dataframe(summary_df)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return pd.DataFrame()


def fetch_screen_tools(db):
    # Example: Replace with real database call
    return pd.read_sql("SELECT * FROM screening_data", db)

# Filtering function

def main():
    db = create_connection()
    df_data = fetch_screen_data(db)
    st.write(df_data)

    st.markdown("#### 📊 Overall Summary")
    conditions = ["Depression Status", "Anxiety Status", "Suicide Risk", "Functioning"]
    summary_data = []
    for cond in conditions:
        value_counts = df_data[cond].value_counts(dropna=False)
        total = value_counts.sum()
        for value, count in value_counts.items():
            percentage = (count / total) * 100
            summary_data.append({
                "Condition": cond,
                "Category": value,
                "Count (Percentage)": f"{count} ({percentage:.1f}%)"})

    summary_df = pd.DataFrame(summary_data)
    prev = None
    for i in range(len(summary_df)):
        current = summary_df.at[i, "Condition"]
        if current == prev:
            summary_df.at[i, "Condition"] = ""
        else:
            prev = current
    st.table(summary_df.style.set_table_styles([
        {'selector': 'thead th', 'props': [('background-color', 'blue'), ('font-weight', 'bold'), ('color', 'white')]}]))
    st.markdown("##### Grouped Analysis by Condition")
    available_group_cols = ["Class", "Stream", "Term", "Screen_Type"]
    with st.sidebar.expander('GROUP ANALYSIS', expanded=True):
        group_cols = st.multiselect(
            "Select Grouping Columns",
            options=available_group_cols,
            default=available_group_cols)
        filters = {}
        for col in group_cols:
            unique_vals = sorted(df_data[col].dropna().unique().tolist())
            selected_vals = st.multiselect(f"Filter values for {col}", options=unique_vals, default=unique_vals)
            filters[col] = selected_vals
        selected_conditions = st.multiselect(
            "Select Conditions to Analyze",
            options=conditions, default=conditions)
    filtered_df = df_data.copy()
    for col, selected_vals in filters.items():
        filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
    grouped_dfs = {}
    if group_cols and selected_conditions:
        for cond in selected_conditions:
            group_df = generate_frequency_table(filtered_df, group_cols, cond)
            if not group_df.empty:
                safe_sheet_name = cond.replace(" ", "_")[:31]
                grouped_dfs[safe_sheet_name] = group_df
                st.markdown(f"##### {cond} by {', '.join(group_cols)}")
                st.table(group_df.style.set_table_styles([
                    {'selector': 'thead th', 'props': [('background-color', '#2ca02c'), ('color', 'white')]}]))
    if grouped_dfs:
        st.download_button(
            label="📥 Download All Data (Excel)",
            data=excel_buffer.getvalue(),
            file_name="summary_and_grouped_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("⚠️ No grouped data to include in the Excel file. Please check your filters or selection.")


if __name__ == "__main__":
    main()
