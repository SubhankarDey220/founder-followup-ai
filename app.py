import streamlit as st
import sqlite3
import re
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

# ================= DATABASE SETUP =================

conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    owner TEXT,
    deadline TEXT,
    status TEXT,
    created_at TEXT,
    reminder_at TEXT,
    email_sent INTEGER DEFAULT 0
)
""")
conn.commit()

# ================= EMAIL FUNCTION =================

def send_email(task, owner, deadline):
    EMAIL_ADDRESS = "suvankar.dey1818@gmail.com"
    EMAIL_PASSWORD = "tyly xpyu utbr srwg"

    msg = EmailMessage()
    msg["Subject"] = "Follow-up Reminder"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    msg.set_content(f"""
Hi,

This is a follow-up reminder.

Task: {task}
Assigned to: {owner}
Deadline: {deadline}

— Founder Follow-Up AI
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ================= AUTO EMAIL CHECK =================

def check_and_send_auto_emails():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    tasks_to_send = cursor.execute(
        """
        SELECT id, task, owner, deadline 
        FROM tasks 
        WHERE reminder_at <= ? AND email_sent = 0
        """,
        (now,)
    ).fetchall()

    for t in tasks_to_send:
        send_email(t[1], t[2], t[3])
        cursor.execute(
            "UPDATE tasks SET email_sent = 1 WHERE id = ?",
            (t[0],)
        )
        conn.commit()

# ================= HELPER FUNCTIONS =================

def extract_task_details(text):
    task = "General Task"
    owner = "Unknown"
    deadline = "Not specified"

    words = text.split()
    if words:
        owner = words[0].replace(",", "")

    days = ["today","tomorrow","monday","tuesday","wednesday",
            "thursday","friday","saturday","sunday"]
    for d in days:
        if d in text.lower():
            deadline = d.capitalize()

    match = re.search(
        r"(send|share|prepare|complete|finish|update)(.*)",
        text,
        re.IGNORECASE
    )
    if match:
        task = match.group(0).strip()

    return task, owner, deadline


def add_task(task, owner, deadline, reminder_minutes):
    reminder_time = datetime.now() + timedelta(minutes=reminder_minutes)

    cursor.execute(
        """
        INSERT INTO tasks 
        (task, owner, deadline, status, created_at, reminder_at, email_sent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task,
            owner,
            deadline,
            "Pending",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            reminder_time.strftime("%Y-%m-%d %H:%M"),
            0
        )
    )
    conn.commit()


def get_tasks():
    return cursor.execute(
        "SELECT * FROM tasks ORDER BY id DESC"
    ).fetchall()


def mark_completed(task_id):
    cursor.execute(
        "UPDATE tasks SET status='Completed' WHERE id=?",
        (task_id,)
    )
    conn.commit()

# ================= STREAMLIT UI =================

st.set_page_config(page_title="Founder Follow-Up AI", layout="centered")

st.title("🤖 Founder Follow-Up AI Assistant")
st.caption("Never forget a follow-up again")

st.divider()

# ---- AUTO EMAIL CHECK ----
check_and_send_auto_emails()

# ---- INPUT SECTION ----
st.subheader("📥 Paste conversation / email / message")

text = st.text_area(
    "Example: Ravi, please send the pitch deck by Friday",
    height=120
)

reminder_minutes = st.number_input(
    "⏰ Send automatic follow-up after how many minutes?",
    min_value=1,
    value=60
)

if st.button("Extract & Add Task"):
    if text.strip() == "":
        st.warning("Please paste some text first.")
    else:
        task, owner, deadline = extract_task_details(text)
        add_task(task, owner, deadline, reminder_minutes)
        st.success("Task added successfully!")

st.divider()

# ---- DASHBOARD ----
st.subheader("📊 Task Dashboard")

tasks = get_tasks()

if not tasks:
    st.info("No tasks yet.")
else:
    for task in tasks:
        col1, col2, col3, col4, col5, col6 = st.columns([4, 2, 2, 3, 2, 3])

        with col1:
            st.write(f"📝 **{task[1]}**")
            st.caption(f"Created: {task[5]}")

        with col2:
            st.write(f"👤 {task[2]}")

        with col3:
            st.write(f"📅 {task[3]}")

        with col4:
            st.write(f"⏱ {task[6]}")

        with col5:
            if task[4] == "Pending":
                if st.button("✅ Done", key=f"complete_{task[0]}"):
                    mark_completed(task[0])
                    st.experimental_rerun()
            else:
                st.success("Done")

        with col6:
            if st.button("📧 Send Email", key=f"email_{task[0]}"):
                send_email(task[1], task[2], task[3])
                st.success("Email sent!")

st.divider()
st.caption("🚀 MVP for founder follow-ups & accountability")
