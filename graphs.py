DB_PATH = "users_db.db"
import pandas as pd
import os, base64
import appointments
from datetime import datetime
import seaborn as sns
import sqlite3

import plotly.express as px
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import io
import base64
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import tempfile
import plotly.express as px
import tempfile
from reportlab.platypus import Image

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
    }
}


def fetch_tool_data(db, appointment_id):
    cursor = db.cursor()
    data = {"appointment_id": appointment_id}

    def safe_query(table):
        try:
            # Check if 'assessment_date' column exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if "assessment_date" in columns:
                cursor.execute(f"""
                    SELECT * FROM {table}
                    WHERE appointment_id = ?
                    ORDER BY assessment_date DESC
                    LIMIT 1
                """, (appointment_id,))
            else:
                cursor.execute(f"""
                    SELECT * FROM {table}
                    WHERE appointment_id = ?
                    LIMIT 1
                """, (appointment_id,))
            return cursor.fetchone()
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                # st.warning(f"⚠️ Warning: Table '{table}' is missing.")
                return None
            else:
                raise e


    for tool_name, tool_info in TOOLS.items():
        row = safe_query(tool_info["table"])
        if row:
            for out_field, db_field in tool_info["fields"].items():
                data[out_field] = row[db_field]
        else:
            # No data for this tool - set all to None
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
    # Colors for suicide risk
    suicide_colors = {
        "High risk": "red",
        "Moderate risk": "yellow",
        "Low risk": "green",
        None: ""
    }
    # Colors for anxiety status
    anxiety_colors = {
        "Severe anxiety": "red",
        "Moderate anxiety": "orange",
        "Mild anxiety": "yellow",
        "Minimal anxiety": "green",
        None: ""
    }
    # Colors for PHQ-4 Severity
    phq4_colors = {
        "Severe": "red",
        "Moderate": "orange",
        "Mild": "yellow",
        "Normal": "green",
        "None": "green",
        None: ""
    }
    # Colors for functioning status
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

    if column == "Depression Status":
        return depression_colors.get(val, "")
    if column == "Suicide Risk":
        return suicide_colors.get(val, "")
    if column == "Anxiety Status":
        return anxiety_colors.get(val, "")
    if column == "PHQ-4 Severity":
        return phq4_colors.get(val, "")
    if column == "Functioning Status":
        return functioning_colors.get(val, "")
    if column in ["DASS Depression Score", "DASS Anxiety Score", "DASS Stress Score"]:
        if val is None:
            return ""
        if val >= 28:
            return "darkred"
        elif val >= 21:
            return "red"
        elif val >= 14:
            return "orange"
        elif val >= 10:
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

    styled = df.style \
        .apply(style_row, axis=1) \
        .set_table_styles([{
            'selector': 'thead th',
            'props': [('background-color', 'lightblue'), ('color', 'black'), ('font-weight', 'bold')]
        }]) \
        .hide(axis="index")

    return styled


def generate_combined_summary_table(db, return_unstyled=False):
    cursor = db.cursor()
    cursor.execute("""
        SELECT appointment_id, name, screen_type, class, stream, term, client_type, screening_tools
        FROM appointments
        WHERE screening_tools IS NOT NULL AND screening_tools != ''
        ORDER BY appointment_id
    """)
    rows = cursor.fetchall()
    cursor.close()

    all_data = []

    for row in rows:
        appointment_id = row["appointment_id"]
        
        # Fetch related tool data
        data = fetch_tool_data(db, appointment_id)

        # Add basic metadata
        data.update({
            "appointment_id": appointment_id,
            "name": row["name"],
            "screen_type": row["screen_type"],
            "class": row["class"],
            "stream": row["stream"],
            "term": row["term"],
            "client_type": row["client_type"]
        })

        # Add response dates from screening_tools JSON
        try:
            tools_dict = json.loads(row["screening_tools"]) if row["screening_tools"] else {}
            for tool_name, tool_data in tools_dict.items():
                response_date = tool_data.get("response_date", "")
                if response_date:
                    data[f"{tool_name}_response_date"] = response_date
        except Exception as e:
            st.warning(f"⚠️ Failed to parse screening_tools for appointment_id {appointment_id}: {e}")

        all_data.append(data)

    df = pd.DataFrame(all_data)
    return df if return_unstyled else style_combined_df(df)


def select_and_order_columns(df):
    st.sidebar.markdown("### 🗂 Select and Order Columns to Display")
    selected_columns = st.sidebar.multiselect(
        "Pick columns to display (drag to reorder if needed):",
        options=df.columns.tolist(),
        default=df.columns.tolist())
    if selected_columns:
        return df[selected_columns]
    else:
        st.sidebar.info("No columns selected, showing all columns.")
        return df


###### GRAPH DISPLY ######
import streamlit as st

def set_visualization_settings(df):
    with st.sidebar.expander('GROUP BY', expanded=True):
        # Group-by options (predefined, but filtered by what exists in df)
        potential_group_cols = ['client_type',"screen_type", 'term', "class", "stream",  "gender"]
        group_by_columns = st.multiselect(
            "Group By (optional, you can select multiple)", 
            options=[col for col in potential_group_cols if col in df.columns],
            default=[])
        group_filters = {}
        for col in group_by_columns:
            unique_vals = df[col].dropna().unique().tolist()
            selected_vals = st.multiselect(
                f"Select values for {col}", 
                options=unique_vals, 
                default=unique_vals, 
                key=f"group_filter_{col}"
            )
            group_filters[col] = selected_vals
        available_conditions = [col for col in df.columns if col in ["Depression Status", "Anxiety Status", "Suicide Risk", "Functioning Status"]]
        selected_conditions = st.multiselect(
            "Select Conditions to Visualize",
            options=available_conditions,
            default=available_conditions
        )

    return group_by_columns, group_filters, selected_conditions



def filter_and_display_graph(df, group_by_columns, selected_conditions):
    if df.empty:
        st.warning("No data available for visualization based on the current filters.")
        return

    with st.sidebar.expander('CHART FILTER', expanded=True):
        chart_type = st.radio("Select Chart Type", ["Bar Chart", "Pie Chart"], horizontal=True)
    


    color_maps = {
        "Depression Status": {
            "Severe depression": "red",
            "Moderately severe depression": "orange",
            "Moderate depression": "yellow",
            "Mild depression": "blue",
            "Minimal depression": "green"
        },
        "Anxiety Status": {
            "Severe anxiety": "red",
            "Moderate anxiety": "orange",
            "Mild anxiety": "yellow",
            "Minimal anxiety": "green"
        },
        "Suicide Risk": {
            "High": "red",
            "Moderate": "yellow",
            "Low": "green"
        },
        "Functioning": {
            "Extremely difficult": "red",
            "Very difficult": "orange",
            "Somewhat difficult": "yellow",
            "Not difficult at all": "green"}}

    for condition_column in selected_conditions:
        color_map = color_maps.get(condition_column, {})
        group_cols = group_by_columns + [condition_column] if group_by_columns else [condition_column]
        plot_data = df.groupby(group_cols).size().reset_index(name="Count")
        if group_by_columns:
            total_counts = plot_data.groupby(group_by_columns)["Count"].transform("sum")
        else:
            total_count = plot_data["Count"].sum()
            total_counts = pd.Series([total_count] * len(plot_data))
        plot_data["Percentage"] = (plot_data["Count"] / total_counts * 100).round(1)
        if chart_type == "Bar Chart":
            plot_data["Group"] = plot_data[group_by_columns].astype(str).agg(" - ".join, axis=1) if group_by_columns else "Overall"
            fig = px.bar(
                plot_data,
                x="Group",
                y="Count",
                color=condition_column,
                color_discrete_map=color_map,
                text=plot_data["Count"].astype(str) + " (" + plot_data["Percentage"].astype(str) + "%)",
                barmode="stack")
            fig.update_layout(
                title=f"{condition_column} by {' + '.join(group_by_columns) if group_by_columns else 'Overall'}",
                xaxis_title="Group",
                yaxis_title="Count",
                legend_title=condition_column,
                xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Pie Chart":
            if group_by_columns:
                for values, sub_data in plot_data.groupby(group_by_columns):
                    label = " - ".join(str(v) for v in values) if isinstance(values, tuple) else str(values)
                    fig = px.pie(
                        sub_data,
                        names=condition_column,
                        values="Count",
                        title=f"{condition_column} - {label}",
                        color=condition_column,
                        color_discrete_map=color_map,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.pie(
                    plot_data,
                    names=condition_column,
                    values="Count",
                    title=f"{condition_column} - Overall",
                    color=condition_column,
                    color_discrete_map=color_map,
                )
                st.plotly_chart(fig, use_container_width=True)





def apply_date_filters(df):
    date_cols = [col for col in df.columns if col.endswith("_response_date")]
    valid_date_col = next((col for col in date_cols if df[col].notna().any()), None)
    if not valid_date_col:
        st.info("No valid response date columns found for filtering.")
        return df
    df["response_date"] = pd.to_datetime(df[valid_date_col], errors="coerce")
    df["Year"] = df["response_date"].dt.year
    df["Month"] = df["response_date"].dt.strftime('%B')
    st.sidebar.markdown("### 📅 Filter by Date")
    available_years = sorted(df["Year"].dropna().unique())
    available_months = df["Month"].dropna().unique().tolist()
    selected_years = st.sidebar.multiselect("Select Year(s)", available_years, default=available_years)
    selected_months = st.sidebar.multiselect("Select Month(s)", available_months, default=available_months)
    filtered_df = df[
        df["Year"].isin(selected_years) &
        df["Month"].isin(selected_months)]
    return filtered_df.drop(columns=["response_date", "Year", "Month"], errors="ignore")


def main():
    db = create_connection()
    set_full_page_background('images/black_strip.jpg')
    df = generate_combined_summary_table(db, return_unstyled=True)
    df = apply_date_filters(df)
    group_by_columns, group_filters, selected_conditions = set_visualization_settings(df)

    for col, selected_vals in group_filters.items():
        if selected_vals:
            df = df[df[col].isin(selected_vals)]

    filter_and_display_graph(df, group_by_columns, selected_conditions)

if __name__ == "__main__":
    main()