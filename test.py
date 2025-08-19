DB_PATH = "users_db.db"
import sqlite3

import json
import streamlit as st
DB = "users_db.db"

def create_connection():
    """
    Create and return a database connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn

def extract_clients_seen(db):
    """
    Fetch Consult sessions and extract number of clients seen.
    """
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id, date, compiled_by, data FROM session_reports WHERE session_type = 'Consult'")
        rows = cursor.fetchall()

        results = []
        for row in rows:
            try:
                data_dict = json.loads(row["data"] or '{}')
            except json.JSONDecodeError:
                data_dict = {}

            # Extract clients_seen
            clients_seen = int(data_dict.get("clients_seen", 0))
            if clients_seen == 0:
                remarks = data_dict.get("remarks_per_client", {})
                if isinstance(remarks, dict):
                    clients_seen = len(remarks)

            results.append({
                "id": row["id"],
                "date": row["date"],
                "compiled_by": row["compiled_by"],
                "clients_seen": clients_seen
            })

        return results

    except Exception as e:
        print(f"Error extracting clients_seen: {e}")
        return []
    finally:
        cursor.close()

def test_clients_seen():
    """
    Test function to print all Consult sessions with clients_seen.
    """
    conn = create_connection()
    data = extract_clients_seen(conn)
    if not data:
        st.write("No Consult session records found.")
    else:
        st.write("Consult Sessions and Clients Seen:")
        print("---------------------------------")
        for record in data:
            st.write(f"ID: {record['id']} | Date: {record['date']} | By: {record['compiled_by']} | Clients Seen: {record['clients_seen']}")
    conn.close()

if __name__ == "__main__":
    test_clients_seen()
