DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import pandas as pd
import json
import plotly.express as px
import os, base64
# ------------------- DATABASE CONNECTION ------------------- #
def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

# ------------------- FETCH TOOLS AND STATUSES ------------------- #
def fetch_screen_tools(db):
    cursor = db.cursor()
    cursor.execute("""
        SELECT appointment_id, name, screen_type, class, stream, term, client_type,
               screening_tools, actions
        FROM appointments
        WHERE screening_tools IS NOT NULL AND screening_tools != ''
        ORDER BY appointment_id
    """)
    screens = cursor.fetchall()
    cursor.close()

    records = []
    for row in screens:
        try:
            # Parse actions JSON
            actions = json.loads(row["actions"]) if row["actions"] else {}
            if not actions.get("screen", False):  # Skip if screen action not true
                continue
        except Exception as e:
            st.warning(f"Failed to parse actions for appointment_id {row['appointment_id']}: {e}")
            continue

        # Parse screening tools JSON
        try:
            tools_dict = json.loads(row["screening_tools"]) if row["screening_tools"] else {}
        except Exception as e:
            st.warning(f"Failed to parse screening_tools for appointment_id {row['appointment_id']}: {e}")
            tools_dict = {}

        for tool_name, tool_data in tools_dict.items():
            status = tool_data.get("status", "Pending")
            response_date = tool_data.get("response_date", "")
            scheduled_date = tool_data.get("scheduled_date", "")

            records.append({
                "appointment_id": row["appointment_id"],
                "name": row["name"],
                "client_type": row["client_type"],
                "class": row["class"],
                "stream": row["stream"],
                "term": row["term"],
                "screen_type": row["screen_type"],
                "tool": tool_name,
                "status": status,
                "response_date": response_date,
                "scheduled_date": scheduled_date
            })

    return pd.DataFrame(records)

# ------------------- CUMULATIVE FILTERS ------------------- #
def dynamic_cumulative_multiselect_filter(df):
    st.sidebar.markdown("### 🧩 Select Columns to Filter")
    filter_columns = st.sidebar.multiselect("Pick columns to filter by", df.columns.tolist())

    filtered_df = df.copy()
    for col in filter_columns:
        unique_vals = sorted(filtered_df[col].dropna().unique())
        selected_vals = st.sidebar.multiselect(f"Filter values for '{col}'", unique_vals, key=col)
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

    return filtered_df

# ------------------- SELECT AND ORDER COLUMNS ------------------- #
def select_and_order_columns(df):
    st.sidebar.markdown("### 🗂 Columns to Display")
    selected_columns = st.sidebar.multiselect(
        "Choose columns to show (drag to reorder):",
        options=df.columns.tolist(),
        default=df.columns.tolist()
    )
    return df[selected_columns] if selected_columns else df


# ------------------- STYLING (ONLY STATUS COLUMN) ------------------- #
def style_tool_status(df):
    def highlight_status(val):
        if isinstance(val, str):
            if val.strip().lower() == "completed":
                return "background-color: lightgreen; color: black"
            elif val.strip().lower() == "pending":
                return "background-color: yellow; color: black"
        return ""

    return df.style.applymap(highlight_status, subset=["status"]) \
                   .set_table_styles([
                        {'selector': 'thead th',
                         'props': [('background-color', '#0f62fe'),
                                   ('color', 'white'),
                                   ('font-weight', 'bold')]}
                   ]) \
                   .hide(axis="index")

# ------------------- DYNAMIC CHART ------------------- #
def plot_status_chart(df, chart_type="Bar Chart"):
    if df.empty:
        st.info("No data to plot.")
        return

    st.subheader(f"📊 {chart_type}")
    if chart_type == "Bar Chart":
        chart_data = df.groupby(["tool", "status"]).size().reset_index(name="count")
        fig = px.bar(chart_data,
                     x="tool", y="count", color="status", barmode="group",
                     color_discrete_map={"Completed": "green", "Pending": "orange"},
                     title="Tool Completion Status by Tool",
                     labels={"tool": "Tool", "count": "Count", "status": "Status"})
        fig.update_layout(xaxis_title="Tool", yaxis_title="Number of Screens", legend_title="Status")

    elif chart_type == "Pie Chart":
        pie_data = df["status"].value_counts().reset_index()
        pie_data.columns = ["status", "count"]
        fig = px.pie(pie_data, values="count", names="status",
                     color="status",
                     color_discrete_map={"Completed": "green", "Pending": "orange"},
                     title="Overall Status Distribution")

    else:
        st.warning("Unsupported chart type selected.")
        return

    st.plotly_chart(fig, use_container_width=True)

# ------------------- MAIN APP ------------------- #
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



def main():
    set_full_page_background('images/black_strip.jpg')
    db = create_connection()
    if not db:
        st.stop()
    df = fetch_screen_tools(db)
    if df.empty:
        st.warning("No screen data found.")
        st.stop()
    filtered_df = dynamic_cumulative_multiselect_filter(df)
    
    if st.checkbox('Plots'):
        chart_type = st.sidebar.radio("📈 Choose Chart Type:", ["Bar Chart", "Pie Chart"])
        plot_status_chart(filtered_df, chart_type)
    else:
        display_df = select_and_order_columns(filtered_df)
        st.subheader(f"Displaying {len(display_df)} records")
        styled = style_tool_status(display_df)
        st.markdown(styled.to_html(escape=False), unsafe_allow_html=True)
        
# ------------------- RUN ------------------- #
if __name__ == "__main__":
    main()
