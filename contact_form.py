DB_PATH = "users_db.db"
import streamlit as st
import smtplib
import sqlite3

import datetime
from streamlit_option_menu import option_menu
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError
import time
import base64
import os
import pandas as pd
import datetime

server = st.secrets["SERVER"]
port = st.secrets["PORT"]
u = st.secrets["U"]
secret = st.secrets["SECRET"]
recipient = st.secrets["RECIPIENT"]

def set_full_page_background(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            [data-testid="stApp"] {{
                background-image: url("data:image/jpg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    return conn



def display_message_log():
    st.subheader("Message Logs")
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM messages_table ORDER BY date DESC, time DESC", conn)
    if df.empty:
        st.info("No messages yet.")
    else:
        df.index += 1
        df = df.drop(['id', 'user_id', 'username'], axis=1)
        st.table(df)


def my_message_log(username):
    st.subheader("Message Logs")
    conn = create_connection()
    df = pd.read_sql_query("""
        SELECT username, name, email, contact,
               message, responded date, time
        FROM messages_table
        ORDER BY date DESC, time DESC
    """, conn)
    conn.close()
    
    df = df[df['username'] == username]

    if not df.empty:
        df.index += 1
        st.dataframe(df)
    else:
        st.info("No messages yet for this user.")
def mark_message_responded(message_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("UPDATE messages_table SET responded = 1 WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()



def fetch_user_details_by_username(username):
    connection = create_connection()
    user_details = {}
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            record = cursor.fetchone()
            user_details = dict(record) if record else {}
        except Exception as e:
            st.error(f"Error fetching user details: {e}")
        finally:
            cursor.close()
            connection.close()
    return user_details


def display_admin_notifications():
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, email, message, date, time 
        FROM messages_table 
        WHERE responded = 0 
        ORDER BY date DESC, time DESC
    """)
    messages = cur.fetchall()

    if not messages:
        st.success("✅ No new messages.")
        return
    st.subheader("📥 New Messages")
    for msg in messages:
        with st.expander(f"📩 From: {msg['name']} | {msg['date']} {msg['time']}"):
            st.write(f"**Email**: {msg['email']}")
            st.write(f"**Message**: {msg['message']}")
            reply = st.text_area("✏️ Reply to this message", key=f"reply_{msg['id']}")
            if st.button("Send Reply", key=f"send_{msg['id']}"):
                send_email_response(msg['email'], reply)
                mark_message_responded(msg['id'])
                st.success("✅ Response sent.")
                st.rerun()
                
    conn.close()




def send_email_response(recipient_email, message_body):
    try:
        validate_email(recipient_email, check_deliverability=True)
        server_conn = smtplib.SMTP(server, port)
        server_conn.starttls()
        server_conn.login(u, secret)
        subject = "Re: Your Message"
        msg = MIMEMultipart()
        msg["From"] = u
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message_body, "plain"))
        server_conn.sendmail(u, recipient_email, msg.as_string())
        server_conn.quit()
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")




def create_message_table():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            username TEXT,
            name TEXT,
            email TEXT,
            contact TEXT,
            client_type TEXT,
            message TEXT,
            sent_date TEXT,
            sent_time TEXT,
            response TEXT,
            response_date TEXT,
            response_time TEXT,
            responder TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_current_date_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

def save_message_to_db(user):
    conn = create_connection()
    cur = conn.cursor()
    sent_date, sent_time = get_current_date_time()

    cur.execute("""
        INSERT INTO messages_table (
            user_id, username, name, email, contact, client_type, message,
            sent_date, sent_time, response, response_date, response_time, responder
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.get("user_id"),
        user.get("username"),
        user.get("name"),
        user.get("email"),
        user.get("contact"),
        user.get("client_type"),
        user.get("message"),
        sent_date,
        sent_time,
        None,  # response
        None,  # response_date
        None,  # response_time
        None   # responder
    ))
    conn.commit()
    conn.close()

def fetch_user_details_by_username(username):
    connection = create_connection()
    user_details = {}
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        record = cursor.fetchone()
        user_details = dict(record) if record else {}
    except Exception as e:
        st.error(f"Error fetching user details: {e}")
    finally:
        cursor.close()
        connection.close()
    return user_details

def get_all_messages_df(username=None):
    conn = create_connection()
    if username:
        query = """
            SELECT  message, sent_date, sent_time,
                   response, response_date, response_time, responder
            FROM messages_table
            WHERE username = ?
            ORDER BY sent_date DESC, sent_time DESC
        """
        df = pd.read_sql_query(query, conn, params=(username,))
    else:
        query = """
            SELECT  message, sent_date, sent_time,
                   response, response_date, response_time, responder
            FROM messages_table
            ORDER BY sent_date DESC, sent_time DESC
        """
        df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.info("No messages found.")
        return

    df.index = df.index + 1
    df["sent_on"] = pd.to_datetime(df["sent_date"] + ' ' + df["sent_time"]).dt.strftime('%Y-%m-%d %H:%M')
    df["response"] = df["response"].fillna('—')
    df["response_date"] = df["response_date"].fillna('—')
    df["response_time"] = df["response_time"].fillna('—')
    df["responder"] = df["responder"].fillna('—')

    st.markdown("""
        <style>
            .message-table {
                border-collapse: collapse;
                width: 100%;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 15px;
                color: #eee;
            }
            .message-table th, .message-table td {
                border: 1px solid #444;
                padding: 12px 15px;
                text-align: left;
            }
            .message-table th {
                background-color: #4A90E2;
                color: white;
                font-weight: 600;
            }
            .message-table tbody tr:nth-child(even) {
                background-color: #1e1e1e;
            }
            .message-table tbody tr:nth-child(odd) {
                background-color: #2c2c2c;
            }
            .msg-cell {
                color: #8BC34A;
                font-weight: 600;
            }
            .meta-cell {
                color: #bbbbbb;
                font-size: 13px;
            }
            .resp-cell {
                color: #2196F3;
                font-style: italic;
            }
        </style>
    """, unsafe_allow_html=True)

    table_html = '<table class="message-table">'
    table_html += """
        <thead>
            <tr>
                <th>#<th>Message</th><th>Sent On</th><th>Reply</th><th>Reply Date</th>
                <th>Reply Time</th><th>Reply from</th>
            </tr>
        </thead><tbody>
    """
    for idx, row in df.iterrows():
        table_html += f"""<tr><td>{idx}</td>
            <td class="msg-cell">{row['message']}</td>
            <td class="meta-cell">{row['sent_on']}</td>
            <td class="resp-cell">{row['response']}</td>
            <td class="meta-cell">{row['response_date']}</td>
            <td class="meta-cell">{row['response_time']}</td>
            <td class="meta-cell">{row['responder']}</td>
        </tr>"""
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

def main():
    set_full_page_background("images/white_touch.jpg")
    create_message_table()
    contact_menu = option_menu(
        menu_title='',
        orientation='horizontal',
        menu_icon='',
        options=['Send Message', 'View Messages'],
        icons=["book", "eye"],
        styles={
            "container": {"padding": "8!important", "background-color": "black", "border": "2px solid red"},
            "icon": {"color": "red", "font-size": "17px"},
            "nav-link": {
                "color": "#d7c4c1", "font-size": "17px", "font-weight": "bold",
                "text-align": "left", "--hover-color": "#d32f2f"
            },
            "nav-link-selected": {"background-color": "green"},
        },
        key="file_menu"
    )

    username = st.session_state.get("user_name")
    if not username:
        st.warning("Please log in first.")
        return
    user = fetch_user_details_by_username(username)
    if not user:
        st.error("User details not found.")
        return

    if contact_menu == 'Send Message':
        set_full_page_background("images/black_strip.jpg")
        with st.form(key="contact_form", clear_on_submit=True):
            st.subheader("✉️ SEND US A MESSAGE")
            col1, col2 = st.columns([2, 3])
            name = col1.text_input(":orange[NAME]", value=user.get("full_name", ""))
            email = col1.text_input(":orange[Email]", value=user.get("email", ""))
            contact = col1.text_input(":orange[Contact]", value=user.get("contact", ""))
            message = col2.text_area(":orange[💬 Message]", height=250)
            submit = st.form_submit_button(label="Send")
            client_type = user.get('role')

            if submit:
                if not name or not email or not message:
                    st.error("Please fill out all required fields.")
                else:
                    try:
                        validate_email(email, check_deliverability=True)
                        user_data = {
                            "user_id": user.get("user_id"),
                            "username": user.get("username"),
                            "name": name,
                            "email": email,
                            "contact": contact,
                            "message": message,
                            "client_type": client_type
                        }
                        save_message_to_db(user_data)
                        st.success(f"Dear :red[{name}], your message has been received! We shall get back to you soon.")
                        time.sleep(3)
                        st.rerun()
                    except EmailNotValidError as e:
                        st.error(f"Invalid email address: {e}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

    elif contact_menu == 'View Messages':
        set_full_page_background("images/black_strip.jpg")
        get_all_messages_df(username)

if __name__ == "__main__":
    main()
