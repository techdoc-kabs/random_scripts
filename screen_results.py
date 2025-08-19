DB_PATH = "users_db.db"
import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime
import sqlite3

import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import base64
def set_full_page_background(image_path):
    if not os.path.exists(image_path):
        return
    with open(image_path, "rb") as img:
        enc = base64.b64encode(img.read()).decode()
    st.markdown(f"""
        <style>
        [data-testid="stApp"] {{
            background-image: url('data:image/jpg;base64,{enc}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

def db_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.row_factory = sqlite3.Row
    return c



#### COLORS DESIGNED ######

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
        None: ""
    }

    

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


#### PHQ-4 ####
def fetch_latest_phq4(db, appointment_id):
    r = db.execute(
        """SELECT anxiety_score, depression_score, total_score, severity 
           FROM PHQ4_forms WHERE appointment_id=? ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame([r], columns=["Anxiety Score", "Depression Score",'Total Score', 'Severity' ]) if r else pd.DataFrame()

def style_phq4(df):
    return style_generic_df(df, ['Severity'])


##### PHQ9 ####
def fetch_latest_phq9(db, appointment_id):
    r = db.execute(
        """SELECT phq9_score, depression_status, suicide_response, suicide_risk
           FROM PHQ9_forms WHERE appointment_id=? ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame([r], columns=["PHQ Score", "Depression Status", "Suicide Response", "Suicide Risk"]) if r else pd.DataFrame()

def style_phq9(df):
    return style_generic_df(df, ["Depression Status", "Suicide Risk"])



##### GAD -7 ########
def fetch_latest_gad7(db, appointment_id):
    r = db.execute(
        """SELECT gad_score, anxiety_status FROM GAD7_forms WHERE appointment_id=?
           ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame([r], columns=["GAD-7 Score", "Anxiety Status"]) if r else pd.DataFrame()

def style_gad7(df):
    return style_generic_df(df, ["Anxiety Status"])



###### CAPS 14 ######
def fetch_latest_caps14(db, appointment_id):
    r = db.execute(
        """SELECT total_score, risk_level FROM CAPS_forms WHERE appointment_id=?
           ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame([r], columns=["CAPS Total Score", "CAPS Risk Level"]) if r else pd.DataFrame()

def style_caps14(df):
    return style_generic_df(df, ["CAPS Risk Level"])





####  DASS 21 ######
def fetch_latest_dass21(db, appointment_id):
    r = db.execute(
        """SELECT depression_score, depression_status,
                  anxiety_score, anxiety_status,
                  stress_score, stress_status,  total_score
           FROM dass21_forms
           WHERE appointment_id=?
           ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame(
        [r],
        columns=["Depression Score", "Depression Levels",
                 "Anxiety Score", "Anxiety Levels",
                 "Stress Score", "Stress Levels", 'Total Score']
    ) if r else pd.DataFrame()


def style_dass21(df):
    return style_generic_df(df, ["Depression Levels", "Anxiety Levels", "Stress Levels"])



#### HSQ ######
def fetch_latest_hsq(db, appointment_id):
    r = db.execute(
        """SELECT total_score, severity FROM HSQ_forms
           WHERE appointment_id=? ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame([r], columns=["HSQ Total Score", "HSQ Severity"]) if r else pd.DataFrame()

def style_hsq(df):
    return style_generic_df(df, ["HSQ Severity"])


###### SSQ ########

def fetch_latest_ssq(db, appointment_id):
    r = db.execute(
        """SELECT ssq_score, severity_level FROM SSQ_forms WHERE appointment_id=?
           ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame([r], columns=["SSQ Total Score", "SSQ Severity"]) if r else pd.DataFrame()

def style_ssq(df):
    return style_generic_df(df, ["SSQ Severity"])





###### FUNCTIONING #######
def fetch_fxn(db, appointment_id):
    r = db.execute("SELECT fnx_score, difficulty_level FROM functioning_responses WHERE appointment_id=? LIMIT 1", (appointment_id,)).fetchone()
    return pd.DataFrame([r], columns=['Functioning score',"Functioning Status"]) if r else pd.DataFrame()

def style_fxn(df):
    return style_generic_df(df, ["Functioning Status"])


def fetch_latest_snapivc(db, appointment_id):
    r = db.execute(
        """SELECT inatt_mean, hyper_mean, odd_mean, overall_mean FROM snap_iv_c_forms
           WHERE appointment_id=? ORDER BY assessment_date DESC LIMIT 1""", (appointment_id,)
    ).fetchone()
    return pd.DataFrame([r], columns=["Inattention Mean", "Hyperactivity Mean", "Oppositional Mean", "Overall Mean"]) if r else pd.DataFrame()

def style_snapivc(df):
    return style_generic_df(df, df.columns)



tools_config = {
    "PHQ-4": {"fetch": fetch_latest_phq4, "style": style_phq4, "title": "PHQ-4 Summary"},
    "PHQ-9": {"fetch": fetch_latest_phq9, "style": style_phq9, "title": "PHQ-9 Summary"},
    "GAD-7": {"fetch": fetch_latest_gad7, "style": style_gad7, "title": "GAD-7 Summary"},
    "CAPS-14": {"fetch": fetch_latest_caps14, "style": style_caps14, "title": "CAPS-14 Summary"},
    "SNAP-IV-C": {"fetch": fetch_latest_snapivc, "style": style_snapivc, "title": "SNAP-IV-C Summary"},
    "DASS-21": {"fetch": fetch_latest_dass21, "style": style_dass21, "title": "DASS-21 Summary"},
    "HSQ": {"fetch": fetch_latest_hsq, "style": style_hsq, "title": "HSQ Summary"},
    "SSQ": {"fetch": fetch_latest_ssq, "style": style_ssq, "title": "SSQ Summary"},
}


def style_generic_df(df, highlight_cols):
    def highlighter(val, col):
        color = get_color_for_value(col, val)
        return f"background-color: {color}; color: black" if color else ""

    styled = df.style
    for col in highlight_cols:
        styled = styled.applymap(lambda v, c=col: highlighter(v, c), subset=[col])
    return styled.set_table_styles([{
        'selector': 'thead th',
        'props': [('background-color', 'lightblue'), ('color', 'black'), ('font-weight', 'bold')]
    }]).hide(axis="index")


def main():
    db = db_conn()
    set_full_page_background('images/black_strip.jpg')

    appointment_id = st.session_state.get("appointment_id")
    if "appointment_id" in st.session_state:
        appointment_id = st.session_state["appointment_id"]

    row = db.execute("SELECT screening_tools FROM appointments WHERE appointment_id = ?", (appointment_id,)).fetchone()
    if not row:
        st.info("No screening record found")
        return

    try:
        tools_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    except Exception as e:
        st.error(f"Error parsing screening_tools: {e}")
        return

    if not tools_data:
        st.info("No tools assigned")
        return

    tools = list(tools_data.keys())
    statuses = {tool: tools_data[tool].get("status", "Pending") for tool in tools}
    tabs = st.tabs(tools + ['Functioning'])

    for i, tool in enumerate(tools):
        with tabs[i]:
            if tool not in tools_config:
                st.info(f"No config for {tool}")
                continue

            status = statuses[tool].strip()  

            if status == "NA":
                st.info(f"{tool} marked as Not Applicable (NA) ❌")
                continue
            elif status != "Completed":
                st.warning(f"{tool} is still pending ⏳")
                continue

            conf = tools_config[tool]
            df = conf['fetch'](db, appointment_id)

            if df.empty:
                st.info("No data yet")
            else:
                st.table(conf['style'](df))

    # Functioning tab
    with tabs[-1]:
        fdf = fetch_fxn(db, appointment_id)
        if not fdf.empty:
            st.table(style_fxn(fdf))
        else:
            st.info("No Functioning data")

if __name__ == "__main__":
    main()
