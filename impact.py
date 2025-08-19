DB_PATH = "users_db.db"
import streamlit as st
import sqlite3

import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import os, io
import tempfile


def create_connection():
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.row_factory = sqlite3.Row
        db.isolation_level = None
        return db
    except sqlite3.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def get_student_info(db):
    query = """
    SELECT user_id, full_name, class, stream, gender 
    FROM users
    """
    return pd.read_sql_query(query, db)

def generate_tool_impact(db, table_name, score_col, status_col, tool_label):
    date_col = "submitted_at" if table_name == "functioning_responses" else "assessment_date"
    query = f"""
        SELECT
            a.user_id,
            a.appointment_id,
            a.screen_type,
            f.{date_col} AS assessment_date,
            f.{score_col} AS score,
            f.{status_col} AS status
        FROM appointments a
        JOIN {table_name} f ON a.appointment_id = f.appointment_id
        WHERE f.{score_col} IS NOT NULL
        ORDER BY a.user_id, f.{date_col} DESC
    """
    df = pd.read_sql_query(query, db)
    if df.empty:
        return pd.DataFrame()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    pre = df[df["screen_type"] == "PRE-SCREEN"] \
        .groupby("user_id").first().reset_index()[["user_id", "score", "status"]]

    post = df[df["screen_type"] == "POST-SCREEN"] \
        .groupby("user_id").first().reset_index()[["user_id", "score", "status"]]
    pre.rename(columns={"score": "score_pre", "status": "status_pre"}, inplace=True)
    post.rename(columns={"score": "score_post", "status": "status_post"}, inplace=True)
    merged = pd.merge(pre, post, on="user_id", how="inner")
    merged["score_change"] = merged["score_pre"] - merged["score_post"]
    def categorize(change):
        if pd.isna(change):
            return "Unknown"
        elif change > 0:
            return "Improved"
        elif change < 0:
            return "Deteriorated"
        else:
            return "No Change"

    merged["category"] = merged["score_change"].apply(categorize)
    merged["tool"] = tool_label

    return merged[[
        "user_id", "tool",
        "score_pre", "status_pre",
        "score_post", "status_post",
        "score_change", "category"]]

def style_dataframe(df):
    def highlight_category(val):
        color = {
            "Improved": "background-color: green; color: white",
            "No Change": "background-color: gray; color: white",
            "Deteriorated": "background-color: red; color: white"
        }
        return color.get(val, "")

    return df.style.applymap(highlight_category, subset=["Category"]).set_table_styles([
        {"selector": "th", "props": [("background-color", "blue")]}
    ])

def apply_dynamic_filters(df):
    with st.sidebar:
        impact_menu = option_menu(
                    menu_title="",
                    options=["All Results", 'Customize'],
                    icons=["table", "table"],
                    default_index=0,
                    orientation="vertical",
                    styles={
                            "container": {"padding": "8!important", "background-color": 'black','border': '0.01px dotted red'},
                            "icon": {"color": "red", "font-size": "15px"},
                            "nav-link": {"color": "#d7c4c1", "font-size": "15px","font-weight":'bold', "text-align": "left", "margin": "0px", "--hover-color": "red"},
                            "nav-link-selected": {"background-color": "green"},
                        },
                    key="impact_menu")
    if impact_menu == "All Results":
        return df.copy()

    elif impact_menu == 'Customize':
        filtered_df = df.copy()
        with st.sidebar.expander('FILTER OPTIONS', expanded=True):
            search_by = st.selectbox("Search by", ["Name", "User ID"])
            if search_by == "Name" and "Name" in df.columns:
                name_query = st.text_input("Enter name")
                if name_query:
                    filtered_df = filtered_df[filtered_df["Name"].str.contains(name_query, case=False, na=False)]
            elif search_by == "User ID" and "User ID" in df.columns:
                id_query = st.text_input("Enter User ID")
                if id_query:
                    filtered_df = filtered_df[filtered_df["User ID"].astype(str).str.contains(id_query, case=False, na=False)]
            with st.sidebar.expander('Filiters', expanded =True):
                for col in ["Category", "Class", "Stream", "Gender"]:
                    if col in df.columns:
                        options = df[col].dropna().unique().tolist()
                        selected = st.multiselect(f"{col}", options, default=options)
                        filtered_df = filtered_df[filtered_df[col].isin(selected)]
    return filtered_df




def draw_header(canvas, doc):
    width, height = letter
    header_height = 750
    left_x = 30
    center_x = 150
    right_x = 450

    logo_left_path = "images/nag.png"
    logo_right_path = "images/my_logo.png"
    if os.path.exists(logo_left_path):
        canvas.drawImage(logo_left_path, left_x, header_height - 20, width=60, height=60)
    if os.path.exists(logo_right_path):
        canvas.drawImage(logo_right_path, right_x, header_height, width=100, height=30)

    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(center_x, 770, "LOGOS HEALTH & TECHCONSULTANTS LTD.")
    canvas.setFont("Helvetica", 12)
    canvas.drawString(center_x, header_height, "SOROTI UNIVERSITY")
    canvas.drawString(center_x, header_height - 15, "Kampala, Uganda")
    canvas.drawString(center_x, header_height - 30, "+256 781238761")
    canvas.drawString(center_x, header_height - 45, "kabpol14@gmail.com")
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(1)
    canvas.line(30, header_height - 60, 580, header_height - 60)

def no_header(canvas, doc):
    pass

def generate_impact_pdf(df, include_table, include_summary, include_chart, chart_type):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Spacer(1, 40))
    story.append(Paragraph("Impact Evaluation Report", styles['Heading2']))
    story.append(Spacer(1, 8))

    if include_table:
        story.append(Paragraph("Filtered Student Data", styles["Heading3"]))
        data = [["Name", "User ID", "Class", "Stream", "Gender", "Tool", "Pre", "Post", "Change", "Category"]]
        for _, row in df.iterrows():
            data.append([
                row["Name"], row["User ID"], row["Class"], row["Stream"], row["Gender"],
                row["Tool"], row["Pre-screen Score"], row["Post-screen Score"],
                row["Change"], row["Category"]
            ])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 8))

    if include_summary:
        story.append(Paragraph("Summary by Tool and Category", styles["Heading3"]))
        summary = df.groupby("Tool")["Category"].value_counts().unstack(fill_value=0)
        summary["Total"] = summary.sum(axis=1)
        summary_data = [["Tool", "Improved", "No Change", "Deteriorated", "Total"]]
        for tool, row in summary.iterrows():
            summary_data.append([
                tool,
                row.get("Improved", 0),
                row.get("No Change", 0),
                row.get("Deteriorated", 0),
                row["Total"]
            ])
        summary_table = Table(summary_data, repeatRows=1)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 8))

    if include_chart:
        chart_type = chart_type.lower()
        fig, ax = plt.subplots(figsize=(6.5, 4.3))
        if chart_type == "pie":
            cat_counts = df["Category"].value_counts()
            ax.pie(cat_counts, labels=cat_counts.index, autopct='%1.1f%%',
                   colors=["green", "gray", "red"])
            ax.set_title("Impact Evaluation by Assessment Tool")
        else:
            chart_data = df.groupby(["Tool", "Category"]).size().unstack(fill_value=0)
            chart_data.plot(kind="bar", stacked=True, ax=ax,
                            color={"Improved": "green", "No Change": "gray", "Deteriorated": "red"})
            ax.set_title("Tool Impact (Bar Chart)")
            ax.set_ylabel("Number of Students")
            ax.set_xlabel("Tool")
            plt.xticks(rotation=30)
            ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1), borderaxespad=0.)

        chart_path = os.path.join(tempfile.gettempdir(), "impact_chart.png")
        fig.tight_layout()
        fig.savefig(chart_path)
        plt.close(fig)
        story.append(RLImage(chart_path, width=6 * inch, height=4 * inch))
        story.append(Spacer(1, 9))
    doc.build(story, onFirstPage=draw_header, onLaterPages=no_header)
    buffer.seek(0)
    return buffer

import base64
def display_pdf(pdf_buffer):
    base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")
    pdf_display_html = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="500"></iframe>'
    st.markdown(pdf_display_html, unsafe_allow_html=True)


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



def main():
    db = create_connection()
    set_full_page_background('images/black_strip.jpg')
    if db:
        student_info = get_student_info(db)
        phq9 = generate_tool_impact(db, "PHQ9_forms", "phq9_score", "depression_status", "Depression (PHQ-9)")
        gad = generate_tool_impact(db, "GAD7_forms", "gad_score", "anxiety_status", "Anxiety (GAD-7)")
        phq4= generate_tool_impact(db, "PHQ4_forms", "total_score", "severity", "PHQ-4(Initial screen)")
        suicide = generate_tool_impact(db, "phq9_forms", "suicide_response", "suicide_risk", "Suicide Risk")
        functioning = generate_tool_impact(db, "functioning_responses", "fnx_score", "difficulty_level", "Functioning status")
        

        combined = pd.concat([phq4, phq9, suicide, gad,   functioning], ignore_index=True)

        if not combined.empty:
            combined = pd.merge(combined, student_info, on="user_id", how="left")
            combined.index = combined.index + 1
            combined = combined.rename(columns={
                "full_name": "Name",
                "user_id": "User ID",
                "class": "Class",
                "stream": "Stream",
                "gender": "Gender",
                "tool": "Tool",
                "score_pre": "Pre-screen Score",
                "status_pre": "Pre-screen Status",
                "score_post": "Post-screen Score",
                "status_post": "Post-screen Status",
                "score_change": "Change",
                "category": "Category"
            })
            selected = option_menu(
                menu_title=None,
                options=["Dataframe", "Summary Data", "Visio", 'Report'],
                icons=["table", "bar-chart-line", "graph-up", 'printer'],
                default_index=0,
                orientation="horizontal",
                styles={
                        "container": {"padding": "8!important", "background-color": 'black','border': '0.01px dotted red'},
                        "icon": {"color": "red", "font-size": "15px"},
                        "nav-link": {"color": "#d7c4c1", "font-size": "15px","font-weight":'bold', "text-align": "left", "margin": "0px", "--hover-color": "red"},
                        "nav-link-selected": {"background-color": "green"},
                    },
                key="selected")
            combined = apply_dynamic_filters(combined)
            if selected == "Dataframe":
                st.markdown(f'###:blue[FILTERED STUDENTS:] :red[{len(combined)}]')
                styled_df = style_dataframe(combined[[
                    "Name", "User ID", "Class", "Stream", "Gender", "Tool",
                    "Pre-screen Score", "Pre-screen Status",
                    "Post-screen Score", "Post-screen Status",
                    "Change", "Category"
                ]])
                # st.dataframe(styled_df, use_container_width=True)
                st.table(styled_df)

            elif selected == "Summary Data":
                summary = combined.groupby("Tool")["Category"].value_counts().unstack(fill_value=0)
                summary["Total"] = summary.sum(axis=1)
                for col in ["Improved", "No Change", "Deteriorated"]:
                    if col not in summary.columns:
                        summary[col] = 0
                for col in ["Improved", "No Change", "Deteriorated"]:
                    pct = (summary[col] / summary["Total"] * 100).round(0).astype(int).astype(str) + "%"
                    summary[col] = summary[col].astype(int).astype(str) + " (" + pct + ")"

                styled_summary = summary[["Improved", "No Change", "Deteriorated", "Total"]].style.set_table_styles([
                    {"selector": "th", "props": [("background-color", "skyblue"), ("color", "black")]},
                    {"selector": "td", "props": [("background-color", "brown"), ("color", "white")]},])

                st.table(styled_summary)

            elif selected == "Visio":
                chart_data = combined.groupby(["Tool", "Category"]).size().reset_index(name="Count")
                chart_type = st.radio("Choose Chart Type", ["Bar Chart", "Pie Chart"])

                if chart_type == "Bar Chart":
                    fig = px.bar(
                        chart_data,
                        x="Tool",
                        y="Count",
                        color="Category",
                        barmode="group",
                        title="Tool Impact Summary",
                        color_discrete_map={
                            "Improved": "green",
                            "No Change": "gray",
                            "Deteriorated": "red"})
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "Pie Chart":
                    cat_counts = combined["Category"].value_counts().reset_index()
                    cat_counts.columns = ["Category", "Count"]
                    fig = px.pie(
                        cat_counts,
                        names="Category",
                        values="Count",
                        title="Distribution by Category",
                        color="Category",
                        color_discrete_map={
                            "Improved": "green",
                            "No Change": "gray",
                            "Deteriorated": "red"})
                    st.plotly_chart(fig, use_container_width=True)

            if selected == "Report":
                with st.sidebar.expander('GENERATE PDF REPORT', expanded=True):
                    include_table = st.toggle("Include Table", value=True)
                    include_summary = st.toggle("Include Summary", value=True)
                    include_chart = st.toggle("Include Chart", value=True)

                    if include_chart:
                        chart_type = st.radio("Chart Type", ["Bar", "Pie"], horizontal=True)
                    else:
                        chart_type = "bar"

                if st.checkbox("Generate Report"):
                    pdf_buffer = generate_impact_pdf(combined, include_table, include_summary, include_chart, chart_type)
                    display_pdf(pdf_buffer)
                    st.download_button("Download PDF", data=pdf_buffer.getvalue(), file_name="impact_report.pdf")
        else:
            st.info("No pre-post screening data available.")

if __name__ == "__main__":
    main()

