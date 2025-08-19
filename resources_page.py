DB_PATH = "users_db.db"
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu
import os, base64
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu
import auth 
import sqlite3

import bcrypt
import time
import uuid
import parents_resources

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
    font_css = """
    <style>
    /* Default tab appearance */
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
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
    }

    /* Active tab: make it green */
    button[data-baseweb="tab"][aria-selected="true"] > div[data-testid="stMarkdownContainer"] > p {
      background-color: green !important;
      border-color: darkgreen !important;
      color: white !important;
    }

    /* Add spacing between tabs */
    div[role="tablist"] > button {
      margin-right: 300px;
      margin-left: 10px;
    }

    /* Content area of each tab */
    section[role="tabpanel"] {
      padding: 16px 24px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      font-size: 18px;
      color: #333333;
    }

    /* Style tables */
    section[role="tabpanel"] table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 2px;
    }

    section[role="tabpanel"] th, section[role="tabpanel"] td {
      border: 1px solid #ddd;
      padding: 8px;
    }

    section[role="tabpanel"] th {
      background-color: #00897b;
      color: red;
      text-align: left;
    }
    </style>
    """
    st.markdown(font_css, unsafe_allow_html=True)
    section = st.tabs(["Common Mental Health challenges", "Learn self-Help Techniques"])

    with section[0]:
        import cont
        cont.main()
    with section[1]:
        import help_tech
        help_tech.main()

if __name__ == "__main__":
    main()
