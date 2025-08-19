import streamlit as st
from streamlit_card import card
import sqlite3

import therapist
import base64
import os
from streamlit_javascript import st_javascript
import appointments
from streamlit_option_menu import option_menu

DB_PATH = "users_db.db"
def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    conn = create_connection()
    choice = option_menu(
            menu_title="",
            options=["Summary", "Activity_reports", "Topics"],
            icons=["plus-circle", "pencil-square", "table"],
            orientation = "horizontal",
            styles={
                            "container": {"padding": "8!important", "background-color": 'black','border': '0.01px dotted red'},
                            "icon": {"color": "red", "font-size": "15px"},
                            "nav-link": {"color": "#d7c4c1", "font-size": "15px","font-weight":'bold', "text-align": "left", "margin": "0px", "--hover-color": "red"},
                            "nav-link-selected": {"background-color": "green"},
                        },
            default_index=0)

    if choice == "Summary":
        import admin_summary_report
        admin_summary_report.main()

    elif choice == "Activity_reports":
        import report_table
        report_table.main()
    
    elif choice == "Topics":
        import topics
        topics.main()

    conn.close()
if __name__ == "__main__":
    main()
