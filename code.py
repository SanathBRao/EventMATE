import streamlit as st
import sqlite3
import re
from datetime import datetime

# ---------------- DATABASE ---------------- #
DB_NAME = "events.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Announcements
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    # Schedule
    c.execute('''CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    hall TEXT NOT NULL
                )''')
    # Attendees
    c.execute('''CREATE TABLE IF NOT EXISTS attendees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(event_id) REFERENCES schedule(id)
                )''')
    conn.commit()
    conn.close()

init_db()

# ---------------- HELPER FUNCTIONS ---------------- #
def validate_email(email):
    return bool(re.match(r"[^@]+@gmail\.com$", email))

def validate_phone(phone):
    return phone.isdigit() and (7 <= len(phone) <= 12)

# ---------------- USER SIDE ---------------- #
def home():
    st.title("🎉 EventMate – Event Management System")

    # Show Announcements
    st.header("📢 Announcements")
    conn = get_connection()
    c = conn.cursor()
    announcements = c.execute("SELECT message, created_at FROM announcements ORDER BY id DESC").fetchall()
    conn.close()
    if announcements:
        for msg, ts in announcements:
            st.info(f"{msg} \n\n ⏰ {ts}")
    else:
        st.write("No announcements yet.")

    # Show Schedule
    st.header("📅 Event Schedule")
    conn = get_connection()
    c = conn.cursor()
    events = c.execute("SELECT id, event_name, date, time, hall FROM schedule ORDER BY date, time").fetchall()
    conn.close()
    if events:
        for eid, name, date, time, hall in events:
            st.write(f"**{name}**  \n📍 {hall} | 📅 {date} | 🕒 {time}")
    else:
        st.write("No events scheduled yet.")

    # Register for an Event
    st.header("📝 Register for an Event")
    if events:
        event_choice = st.selectbox("Select Event", [f"{eid} - {name}" for eid, name, _, _, _ in events])
        event_id = int(event_choice.split(" - ")[0])
        name = st.text_input("Your Name")
        email = st.text_input("Your Email (must be @gmail.com)")
        phone = st.text_input("Phone Number")

        if st.button("Register"):
            if not name or not email or not phone:
                st.error("⚠️ All fields are required.")
            elif not validate_email(email):
                st.error("⚠️ Email must be a valid @gmail.com address.")
            elif not validate_phone(phone):
                st.error("⚠️ Phone must be digits (7-12).")
            else:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO attendees (event_id, name, email, phone) VALUES (?,?,?,?)",
                          (event_id, name, email, phone))
                conn.commit()
                conn.close()
                st.success("✅ Registration successful!")
    else:
        st.info("No events available to register.")

# ---------------- ADMIN SIDE ---------------- #
def admin_dashboard():
    st.subheader("📊 Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["Announcements", "Schedule", "Attendees"])

    # -------- ANNOUNCEMENTS -------- #
    with tab1:
        st.write("### Manage Announcements")
        msg = st.text_area("New Announcement", key="announcement_input")
        if st.button("Post Announcement"):
            if msg.strip():
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO announcements (message) VALUES (?)", (msg,))
                conn.commit()
                conn.close()
                st.success("✅ Announcement posted!")
                st.session_state["announcement_input"] = ""  # clear
            else:
                st.warning("⚠️ Cannot post empty announcement.")

        # Show + delete announcements
        conn = get_connection()
        c = conn.cursor()
        announcements = c.execute("SELECT id, message FROM announcements ORDER BY id DESC").fetchall()
        conn.close()
        if announcements:
            for aid, text in announcements:
                col1, col2 = st.columns([4,1])
                with col1:
                    st.info(f"🆔 {aid} — {text}")
                with col2:
                    if st.button("❌ Delete", key=f"del_a{aid}"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM announcements WHERE id=?", (aid,))
                        conn.commit()
                        conn.close()
                        st.success("Announcement deleted!")
                        st.experimental_rerun()
        else:
            st.info("No announcements yet.")

    # -------- SCHEDULE -------- #
    with tab2:
        st.write("### Manage Schedule")
        with st.form("add_event"):
            name = st.text_input("Event Name")
            date = st.date_input("Date")
            time = st.time_input("Time")
            hall = st.text_input("Hall")
            submitted = st.form_submit_button("Add Event")
            if submitted:
                if name and hall:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO schedule (event_name, date, time, hall) VALUES (?,?,?,?)",
                              (name, str(date), str(time), hall))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Event '{name}' added!")
                    st.experimental_rerun()
                else:
                    st.error("⚠️ Event name and hall are required.")

        # Show + delete events
        conn = get_connection()
        c = conn.cursor()
        events = c.execute("SELECT id, event_name, date, time, hall FROM schedule").fetchall()
        conn.close()
        if events:
            for eid, name, date, time, hall in events:
                col1, col2 = st.columns([4,1])
                with col1:
                    st.write(f"🆔 {eid} — {name} ({date} {time} - {hall})")
                with col2:
                    if st.button("❌ Delete", key=f"del_e{eid}"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM schedule WHERE id=?", (eid,))
                        conn.commit()
                        conn.close()
                        st.success("Event deleted!")
                        st.experimental_rerun()
        else:
            st.info("No events scheduled.")

    # -------- ATTENDEES -------- #
    with tab3:
        st.write("### Registered Attendees")
        conn = get_connection()
        c = conn.cursor()
        events = c.execute("SELECT id, event_name FROM schedule").fetchall()

        if not events:
            st.warning("No events available yet.")
        else:
            event_choice = st.selectbox("Select Event", [f"{e[0]} - {e[1]}" for e in events])
            event_id = int(event_choice.split(" - ")[0])
            attendees = c.execute("SELECT name, email, phone FROM attendees WHERE event_id=?", (event_id,)).fetchall()
            conn.close()
            if attendees:
                for a in attendees:
                    st.write(f"👤 {a[0]} | ✉️ {a[1]} | 📞 {a[2]}")
            else:
                st.info("No attendees registered for this event.")

# ---------------- ADMIN LOGIN ---------------- #
def admin_login():
    st.header("🔑 Admin Login")

    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if st.session_state["admin_logged_in"]:
        admin_dashboard()
        if st.button("🚪 Logout"):
            st.session_state["admin_logged_in"] = False
            st.success("Logged out successfully.")
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == "admin" and password == "admin123":
                st.session_state["admin_logged_in"] = True
                st.success("✅ Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

# ---------------- MAIN APP ---------------- #
def main():
    st.sidebar.title("📌 Navigation")
    choice = st.sidebar.radio("Go to", ["Home", "Admin Login"])
    if choice == "Home":
        home()
    elif choice == "Admin Login":
        admin_login()

if __name__ == "__main__":
    main()
