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
import pandas as pd
import seaborn as sns
def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

TOOLS = {
    # ─────────────────────────── EXISTING ───────────────────────────
    "PHQ-9": {
        "table": "PHQ9_forms",
        "fields": {
            "PHQ Score": "phq9_score",
            "Depression Status": "depression_status",
            "Suicide Score": "suicide_response",
            "Suicide Risk": "suicide_risk"
        }
    },
    "GAD-7": {
        "table": "GAD7_forms",
        "fields": {
            "GAD-7 Score": "gad_score",
            "Anxiety Status": "anxiety_status"
        }
    },
    "PHQ-4": {
        "table": "PHQ4_forms",
        "fields": {
            "PHQ-4 Total Score": "total_score",
            "PHQ-4 Anxiety Score": "anxiety_score",
            "PHQ-4 Depression Score": "depression_score",
            "PHQ-4 Severity": "severity"
        }
    },
    "DASS-21": {
        "table": "DASS21_forms",
        "fields": {
            "DASS Depression Score": "depression_score",
            "DASS Anxiety Score": "anxiety_score",
            "DASS Stress Score": "stress_score"
        }
    },
    "Functioning": {
        "table": "functioning_responses",
        "fields": {
            "Functioning Status": "difficulty_level"
        }
    },

    # ─────────────────────────── NEW ADDITIONS ───────────────────────────
    "CAPS-14": {
        "table": "CAPS_forms",
        "fields": {
            "CAPS Total Score": "total_score",
            "CAPS Risk Level": "risk_level"
        }
    },
    "SSQ": {
        "table": "SSQ_forms",
        "fields": {
            "SSQ Total Score": "ssq_score",
            "SSQ Severity": "severity_level"
        }
    },
    "HSQ": {
        "table": "HSQ_forms",
        "fields": {
            "HSQ Total Score": "hsq_score",
            "HSQ Severity": "severity_level"
        }
    },
    "SNAP-IV": {           # or rename to "SNAP-IV-C" if you prefer
        "table": "snap_iv_c_forms",
        "fields": {
            "Inattention Mean": "inatt_mean",
            "Hyperactivity Mean": "hyper_mean",
            "Oppositional Mean": "odd_mean",
            "Overall Mean": "overall_mean"
        }
    }
}


def fetch_tool_data(db, appointment_id):
    cursor = db.cursor()
    data = {"appointment_id": appointment_id}

    def safe_query(table, date_col=None):
        try:
            if date_col:
                query = f"""
                    SELECT * FROM {table}
                    WHERE appointment_id = ?
                    ORDER BY {date_col} DESC LIMIT 1
                """
            else:
                query = f"""
                    SELECT * FROM {table}
                    WHERE appointment_id = ?
                    LIMIT 1
                """
            cursor.execute(query, (appointment_id,))
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]  # Get column names
                return dict(zip(columns, row))  # Convert tuple to dict
            return None
        except sqlite3.OperationalError as e:
            if "no such column" in str(e).lower() or "no such table" in str(e).lower():
                st.warning(f"Warning: Problem querying {table}: {e}")
                return None
            else:
                raise e

    for tool_name, tool_info in TOOLS.items():
        date_col = tool_info.get("assessment_date")  # Use date_column if defined
        row = safe_query(tool_info["table"], date_col)
        if row:
            for out_field, db_field in tool_info["fields"].items():
                data[out_field] = row.get(db_field, None)  # Use .get() to avoid KeyError
        else:
            for out_field in tool_info["fields"].keys():
                data[out_field] = None

    cursor.close()
    return data


def get_color_for_value(column, val):
    depression_colors = {
        "Severe depression": "red",
        "Moderately Severe depression": "orange",
        "Moderate depression": "yellow",
        "Mild depression": "blue",
        "Minimal depression": "green",
        None: ""
    }
    suicide_colors = {
        "High risk": "red",
        "Moderate risk": "yellow",
        "Low risk": "green",
        None: ""
    }
    anxiety_colors = {
        "Severe anxiety": "red",
        "Moderate anxiety": "orange",
        "Mild anxiety": "yellow",
        "Minimal anxiety": "green",
        None: ""
    }
    phq4_colors = {
        "Severe": "red",
        "Moderate": "orange",
        "Mild": "yellow",
        "Normal": "green",
        "None": "green",
        None: ""
    }
    functioning_colors = {
        "Extremely difficult": "red",
        "Very difficult": "#CB4154",
        "Somewhat difficult": "yellow",
        "Not difficult at all": "green",
        None: ""
    }
    dass_colors = {
        "Extremely Severe": "darkred",
        "Severe": "red",
        "Moderate": "orange",
        "Mild": "yellow",
        "Normal": "green",
        None: ""
    }
    caps_colors = {
        "High": "red",
        "Moderate": "yellow",
        "Low": "green",
        None: ""
    }
    severity_colors = {
        "Severe": "red",
        "Moderate": "orange",
        "Mild": "yellow",
        "Minimal": "green",
        None: ""}
    if column == "Depression Status":
        return depression_colors.get(val, "")
    if column == "Suicide Risk":
        return suicide_colors.get(val, "")
    if column == "Anxiety Status":
        return anxiety_colors.get(val, "")
    if column in ["Severity"]:
        return phq4_colors.get(val, "")
    if column == "Functioning Status":
        return functioning_colors.get(val, "")
    if column == "CAPS Risk Level":
        return caps_colors.get(val, "")
    if column in ["SSQ Severity", "HSQ Severity", "Severity Level", "Risk Level"]:
        return severity_colors.get(val, "")
    if column in ["Depression Levels", "Anxiety Levels", "Stress Levels"]:
        return dass_colors.get(val, "")
    if column in ["Inattention Mean", "Hyperactivity Mean", "Oppositional Mean", "Overall Mean"]:
        if val is None:
            return ""
        if val >= 2.5:
            return "red"
        elif val >= 2.0:
            return "orange"
        elif val >= 1.5:
            return "yellow"
        else:
            return "green"
    return ""

def style_combined_df(df):
    def style_row(row):
        styles = []
        for col in df.columns:
            color = get_color_for_value(col, row[col])
            if color:
                styles.append(f"background-color: {color}; color: black")
            else:
                styles.append("")
        return styles
    styled = (
        df.style
          .apply(style_row, axis=1)
          .set_table_styles([{
              "selector": "thead th",
              "props": [("background-color", "lightblue"),
                        ("color", "black"),
                        ("font-weight", "bold")]
          }])
          .hide(axis="index"))
    return styled


def generate_frequency_table(df, group_cols, condition_col):
    grouped = df.groupby(group_cols + [condition_col]).size().reset_index(name='Count')
    total_per_group = grouped.groupby(group_cols)['Count'].transform('sum')
    grouped['Percentage'] = (grouped['Count'] / total_per_group * 100)
    grouped['Count (Percentage)'] = grouped.apply(
        lambda row: f"{row['Count']} ({row['Percentage']:.1f}%)", axis=1)
    grouped = grouped.sort_values(group_cols + [condition_col]).reset_index(drop=True)
    for col in group_cols:
        prev_val = None
        for i in range(len(grouped)):
            if grouped.at[i, col] == prev_val:
                grouped.at[i, col] = ""
            else:
                prev_val = grouped.at[i, col]

    return grouped[group_cols + [condition_col, 'Count (Percentage)']]



def generate_combined_summary_data(db, return_unstyled=False):
    cursor = db.cursor()
    cursor.execute("""
        SELECT appointment_id, name, screen_type, class, stream, term, client_type, 
               screening_tools, actions
        FROM appointments
        WHERE screening_tools IS NOT NULL AND screening_tools != ''
        ORDER BY appointment_id""")
    rows = cursor.fetchall()
    cursor.close()

    all_data = []
    for row in rows:
        try:
            actions = json.loads(row["actions"]) if row["actions"] else {}
            if not actions.get("screen", False):
                continue
        except Exception as e:
            st.warning(f"Failed to parse actions for {row['appointment_id']}: {e}")
            continue
        appointment_id = row["appointment_id"]
        data = fetch_tool_data(db, appointment_id)
        data.update({
            "name": row["name"],
            "screen_type": row["screen_type"],
            "class": row["class"],
            "stream": row["stream"],
            "term": row["term"],
            "client_type": row["client_type"]})
        try:
            tools_dict = json.loads(row["screening_tools"]) if row["screening_tools"] else {}
            for tool, tool_info in tools_dict.items():
                if isinstance(tool_info, dict):
                    response_date = tool_info.get("response_date")
                    if response_date:
                        data[f"{tool}_response_date"] = response_date
        except Exception as e:
            st.warning(f"Failed to parse screening_tools for {appointment_id}: {e}")

        all_data.append(data)

    df = pd.DataFrame(all_data)
    date_cols = [col for col in df.columns if col.endswith("_response_date")]
    valid_date_col = next((col for col in date_cols if df[col].notna().any()), None)

    if valid_date_col:
        df["response_date"] = pd.to_datetime(df[valid_date_col], errors="coerce")
        df["Year"] = df["response_date"].dt.year
        df["Month"] = df["response_date"].dt.strftime('%B')
        st.sidebar.markdown("### 📅 Filter by Date")
        years = sorted(df["Year"].dropna().unique())
        months = df["Month"].dropna().unique().tolist()
        selected_years = st.sidebar.multiselect("Select Year(s)", years, default=years)
        selected_months = st.sidebar.multiselect("Select Month(s)", months, default=months)
        df = df[
            df["Year"].isin(selected_years) &
            df["Month"].isin(selected_months)]
        df.drop(columns=["response_date", "Year", "Month"], inplace=True, errors="ignore")
    return df



def main():
    db = create_connection()
    choice = option_menu(
        menu_title="",
        options=["Summary", "BreakDown"],
        icons=["pencil-square", "table"],
        orientation="horizontal",
        default_index=0)
    df_data = generate_combined_summary_data(db)
    conditions = ["Depression Status", "Anxiety Status", "Suicide Risk", "Functioning Status"]
    available_group_cols = ["class", "stream", "term", "screen_type"]
    summary_data = []
    for cond in conditions:
        if cond in df_data.columns:
            value_counts = df_data[cond].value_counts(dropna=False)
            total = value_counts.sum()
            for value, count in value_counts.items():
                percentage = (count / total) * 100
                summary_data.append({
                    "Condition": cond,
                    "Category": value,
                    "Count (Percentage)": f"{count} ({percentage:.1f}%)"
                })
    summary_df = pd.DataFrame(summary_data) 
    group_cols = []
    filters = {}
    selected_conditions = []
    with st.sidebar.expander('GROUP ANALYSIS', expanded=True):
        group_cols = st.multiselect(
            "Select Grouping Columns",
            options=available_group_cols,
            default=available_group_cols
        )
        for col in group_cols:
            if col in df_data.columns:
                unique_vals = sorted(df_data[col].dropna().unique().tolist())
                selected_vals = st.multiselect(
                    f"Filter values for {col}",
                    options=unique_vals,
                    default=unique_vals
                )
                filters[col] = selected_vals
        selected_conditions = st.multiselect(
            "Select Conditions to Analyze",
            options=conditions,
            default=conditions
        )

    if choice == "Summary":
        prev = None
        color_palette = sns.color_palette("Set3", n_colors=10).as_hex()
        condition_colors = {}
        color_index = 0

        for i in range(len(summary_df)):
            current = summary_df.at[i, "Condition"]
            if current == prev:
                summary_df.at[i, "Condition"] = ""
            else:
                if current not in condition_colors:
                    condition_colors[current] = color_palette[color_index % len(color_palette)]
                    color_index += 1
                prev = current

        # Assign row colors based on full-row "Condition"
        def style_rows_by_condition(row):
            condition = row["Condition"]
            color = condition_colors.get(condition, "")
            return [f"background-color: {color}; color: black" if color else "" for _ in row]

        st.table(summary_df.style
                 .apply(style_rows_by_condition, axis=1)
                 .set_table_styles([
                     {'selector': 'thead th', 'props': [('background-color', 'navy'), ('color', 'white')]}
                 ])
                 .hide(axis="index"))
    elif choice == "BreakDown":
        filtered_df = df_data.copy()
        for col, selected_vals in filters.items():
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

        grouped_dfs = {}
        if group_cols and selected_conditions:
            for cond in selected_conditions:
                if cond in filtered_df.columns:
                    group_df = generate_frequency_table(filtered_df, group_cols, cond)

                    if not group_df.empty:
                        safe_sheet_name = cond.replace(" ", "_")[:31]
                        grouped_dfs[safe_sheet_name] = group_df
                        st.markdown(f"###### {cond} by {', '.join(group_cols)}")
                        st.table(group_df.style.set_table_styles([
                            {'selector': 'thead th', 'props': [('background-color', 'skyblue'), ('color', 'white')]}
                        ]))

        if grouped_dfs:
            combined_df = pd.concat(grouped_dfs.values())
            csv_buffer = io.StringIO()
            combined_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download All Data (CSV)",
                data=csv_buffer.getvalue(),
                file_name="summary_and_grouped_data.csv",
                mime="text/csv"
            )
        else:
            st.info("⚠️ No grouped data to display. Please check your filters or selections.")

if __name__ == "__main__":
    main()
