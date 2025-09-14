import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os

DB_FILE = "eventmate.db"

# ---------------------------
# Utility Functions
# ---------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT CHECK(role IN ('user','admin'))
                )''')

    # Events
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    date TEXT,
                    location TEXT
                )''')

    # Attendees
    c.execute('''CREATE TABLE IF NOT EXISTS attendees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    username TEXT,
                    event_id INTEGER,
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )''')

    # Announcements
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    timestamp TEXT
                )''')

    # Insert default accounts if not exist
    c.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("admin", hash_password("admin123"), "admin"))
    c.execute("SELECT * FROM users WHERE username=?", ("user",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("user", hash_password("user123"), "user"))

    conn.commit()
    conn.close()

def show_announcements():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT message, timestamp FROM announcements ORDER BY id DESC")
    announcements = c.fetchall()
    conn.close()

    if announcements:
        st.subheader("📢 Latest Announcements")
        for msg, ts in announcements:
            st.markdown(
                f"""
                <div style="background-color:#f0f8ff; padding:15px; border-radius:10px; margin-bottom:10px;
                            box-shadow:0px 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="color:#2b547e;">📌 {msg}</h4>
                    <p style="font-size:12px; color:gray;">🕒 Posted on {ts}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No announcements yet.")

# ---------------------------
# Registration Page
# ---------------------------
def registration_page(event_id, event_name):
    st.subheader(f"📝 Register for {event_name}")

    with st.form("registration_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        submit = st.form_submit_button("Register")

        if submit:
            if not name or not email or not phone:
                st.error("⚠️ Please fill all fields.")
            elif "@gmail.com" not in email:
                st.error("⚠️ Please enter a valid Gmail address.")
            elif not phone.isdigit() or len(phone) != 10:
                st.error("⚠️ Phone number must be exactly 10 digits (numbers only).")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO attendees (name, email, phone, username, event_id) VALUES (?, ?, ?, ?, ?)",
                          (name, email, phone, st.session_state['username'], event_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Registered successfully for {event_name}!")

# ---------------------------
# User Dashboard
# ---------------------------
def user_dashboard():
    st.title("🎉 User Dashboard")

    show_announcements()
    st.divider()

    st.subheader("📅 Available Events")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    events = c.execute("SELECT id, name, date, location FROM events").fetchall()
    conn.close()

    if events:
        for event in events:
            with st.expander(f"{event[1]} ({event[2]} @ {event[3]})"):
                registration_page(event[0], event[1])
    else:
        st.info("No events available yet.")

    st.subheader("👥 My Registrations")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    regs = c.execute("""
        SELECT e.name, e.date, e.location, a.name, a.email, a.phone
        FROM attendees a
        JOIN events e ON a.event_id = e.id
        WHERE a.username=?
    """, (st.session_state['username'],)).fetchall()
    conn.close()

    if regs:
        for r in regs:
            st.success(f"🎯 {r[0]} on {r[1]} at {r[2]} | 👤 {r[3]} | ✉️ {r[4]} | 📞 {r[5]}")
    else:
        st.info("You haven’t registered for any events yet.")

# ---------------------------
# Admin Dashboard
# ---------------------------
def admin_dashboard():
    st.title("🛠️ Admin Dashboard")

    show_announcements()
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📅 Manage Events", "👥 View Attendees", "📢 Announcements"])

    with tab1:
        st.subheader("➕ Add Event")
        with st.form("event_form"):
            name = st.text_input("Event Name")
            date = st.date_input("Event Date")
            location = st.text_input("Location")
            submit = st.form_submit_button("Add Event")
            if submit:
                if name and location:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO events (name, date, location) VALUES (?, ?, ?)",
                              (name, str(date), location))
                    conn.commit()
                    conn.close()
                    st.success("✅ Event added successfully!")
                    st.experimental_rerun()

        st.subheader("📜 Existing Events")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        events = c.execute("SELECT id, name, date, location FROM events").fetchall()
        conn.close()
        for e in events:
            st.info(f"📌 {e[1]} | 🗓️ {e[2]} | 📍 {e[3]}")

    with tab2:
        st.subheader("👥 Registered Attendees")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        attendees = c.execute("""
            SELECT a.name, a.email, a.phone, e.name, e.date
            FROM attendees a
            JOIN events e ON a.event_id = e.id
        """).fetchall()
        conn.close()
        if attendees:
            for a in attendees:
                st.write(f"👤 {a[0]} | ✉️ {a[1]} | 📞 {a[2]} | 🎯 {a[3]} ({a[4]})")
        else:
            st.info("No attendees registered yet.")

    with tab3:
        st.subheader("➕ Post Announcement")
        msg = st.text_area("Announcement Message")
        if st.button("Post"):
            if msg.strip():
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO announcements (message, timestamp) VALUES (?, ?)",
                          (msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("✅ Announcement posted!")
                st.experimental_rerun()

# ---------------------------
# Login
# ---------------------------
def login_page():
    st.title("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT password, role FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and user[0] == hash_password(password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = user[1]
            st.success(f"✅ Logged in as {user[1].capitalize()}")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")

# ---------------------------
# Main
# ---------------------------
def main():
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.sidebar.success(f"👤 {st.session_state['username']} ({st.session_state['role']})")

        if st.session_state["role"] == "admin":
            admin_dashboard()
        elif st.session_state["role"] == "user":
            user_dashboard()

        if st.sidebar.button("🚪 Logout"):
            st.session_state.clear()
            st.experimental_rerun()

if __name__ == "__main__":
    main()
