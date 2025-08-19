DB_PATH = "users_db.db"
import mysql.connector
from mysql.connector import Error
import streamlit as st


def sqlite3.connect('your_sqlite_db_path.db'):
    try:
        connection = mysql.connector.connect(
            host=st.secrets["db_host"],       
            user=st.secrets["db_user"],       
            password=st.secrets["db_password"],
            database=st.secrets["db_name"],   
            port=st.secrets.get("db_port", 3306)  
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"❌ Error while connecting to MySQL: {e}")
        return None

