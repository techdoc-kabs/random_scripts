







def view_appointment_requests():
    set_full_page_background('images/black_strip.jpg')
    conn = create_connection()
    query = """
        SELECT 
            a.id,
            a.client_name,
            a.client_email,
            a.client_phone,
            a.therapist_name,
            a.appointment_date,
            a.appointment_time,
            a.reason,
            a.created_at AS submitted_on,
            a.response,
            a.responder,
            a.response_date
        FROM appointment_requests a
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if df.empty:
        st.info("📭 No appointments found.")
        return
    df.index = df.index + 1
    df["appointment_date"] = pd.to_datetime(df["appointment_date"], errors='coerce').dt.strftime('%Y-%m-%d')
    df["submitted_on"] = pd.to_datetime(df["submitted_on"], errors='coerce').dt.strftime('%Y-%m-%d').fillna('—')
    df["response_date"] = pd.to_datetime(df["response_date"], errors='coerce').dt.strftime('%Y-%m-%d').fillna('—')
    df["response"] = df["response"].fillna("—")
    df["responder"] = df["responder"].fillna("—")
    st.markdown("""
        <style>
            .appt-table {
                border-collapse: collapse;
                width: 100%;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 15px;
                color: #eee;
            }
            .appt-table th, .appt-table td {
                border: 1px solid #444;
                padding: 10px 12px;
                text-align: left;
                vertical-align: top;
            }
            .appt-table th {
                background-color: #4A90E2;
                color: white;
                font-weight: 600;
            }
            .appt-table tbody tr:nth-child(even) {
                background-color: #1e1e1e;
            }
            .appt-table tbody tr:nth-child(odd) {
                background-color: #2c2c2c;
            }
            .name-cell { color: #FF9800; font-weight: 600; }
            .therapist-cell { color: #8BC34A; font-weight: 600; }
            .reason-cell { color: #2196F3; font-style: italic; }
            .meta-cell { color: #bbbbbb; font-size: 13px; }
            .response-cell { color: #FFC107; }
            .responder-cell { color: #00BCD4; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

    table_html = '<table class="appt-table">'
    table_html += """<thead>
            <tr>
                <th>#</th>
                <th>Client Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Therapist</th>
                <th>Date</th>
                <th>Time</th>
                <th>Reason</th>
                <th>Date Submitted</th>
                <th>Response</th>
                <th>Responder</th>
                <th>Response Date</th>
            </tr>
        </thead>
        <tbody>
    """

    for idx, row in df.iterrows():
        table_html += f"""<tr>
                <td>{idx}</td>
                <td class="name-cell">{row['client_name']}</td>
                <td class="meta-cell">{row['client_email']}</td>
                <td class="meta-cell">{row['client_phone']}</td>
                <td class="therapist-cell">{row['therapist_name']}</td>
                <td class="meta-cell">{row['appointment_date']}</td>
                <td class="meta-cell">{row['appointment_time']}</td>
                <td class="reason-cell">{row['reason']}</td>
                <td class="meta-cell">{row['submitted_on']}</td>
                <td class="response-cell">{row['response']}</td>
                <td class="responder-cell">{row['responder']}</td>
                <td class="meta-cell">{row['response_date']}</td>
            </tr>
        """

    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)