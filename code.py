import streamlit as st
import sqlite3
import os

DB_FILE = "eventmate.db"

# ----------------------------
# Database Setup
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Announcements
    c.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL
        )
    """)

    # Events
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    # Attendees (linked to events)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    """)

    # Users/Admins
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('user','admin'))
        )
    """)

    # Insert default admin & user if not exist
    c.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "admin"))

    c.execute("SELECT * FROM users WHERE username=?", ("user",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("user", "user123", "user"))

    conn.commit()
    conn.close()

def reset_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()

# ----------------------------
# Login Page
# ----------------------------
def login_page():
    st.title("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        account = c.fetchone()
        conn.close()

        if account:
            role = account[0]
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.success(f"✅ Logged in as {role.capitalize()}")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")

# ----------------------------
# Home Page
# ----------------------------
def home_page():
    st.title("🏠 EventMate")
    st.subheader("📢 Announcements")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    announcements = c.execute("SELECT message FROM announcements ORDER BY id DESC").fetchall()
    if announcements:
        for ann in announcements:
            st.info(ann[0])
    else:
        st.write("No announcements yet.")

    st.subheader("📅 Upcoming Events")
    events = c.execute("SELECT id, name, date, location FROM events ORDER BY date").fetchall()
    conn.close()

    if events:
        for event in events:
            st.write(f"### {event[1]}")
            st.write(f"📆 Date: {event[2]}")
            st.write(f"📍 Location: {event[3]}")

            if st.session_state.get("role") == "user":
                if st.button(f"Register for {event[1]}", key=f"regbtn{event[0]}"):
                    st.session_state["register_event_id"] = event[0]
                    st.session_state["page"] = "register"
                    st.experimental_rerun()
    else:
        st.write("No events available.")

# ----------------------------
# Registration Page
# ----------------------------
def registration_page():
    event_id = st.session_state.get("register_event_id", None)
    if not event_id:
        st.error("⚠️ No event selected for registration.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    event = c.execute("SELECT name FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()

    st.title(f"📝 Register for {event[0]}")

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
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO attendees (name, email, phone, event_id) VALUES (?, ?, ?, ?)",
                          (name, email, phone, event_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Registered successfully for {event[0]}!")

# ----------------------------
# Admin Dashboard
# ----------------------------
def admin_dashboard():
    st.title("🛠️ Admin Dashboard")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Announcements
    st.subheader("📢 Manage Announcements")
    with st.form("add_announcement"):
        message = st.text_input("New Announcement")
        submit = st.form_submit_button("Add")
        if submit and message:
            c.execute("INSERT INTO announcements (message) VALUES (?)", (message,))
            conn.commit()
            st.success("✅ Announcement added!")
            st.experimental_rerun()

    announcements = c.execute("SELECT id, message FROM announcements ORDER BY id DESC").fetchall()
    for ann in announcements:
        if st.button(f"❌ Delete: {ann[1][:30]}...", key=f"delann{ann[0]}"):
            c.execute("DELETE FROM announcements WHERE id=?", (ann[0],))
            conn.commit()
            st.success("✅ Announcement deleted!")
            st.experimental_rerun()

    # Events
    st.subheader("📅 Manage Events")
    with st.form("add_event"):
        name = st.text_input("Event Name")
        date = st.date_input("Event Date")
        location = st.text_input("Event Location")
        submit = st.form_submit_button("Add Event")
        if submit and name and location:
            c.execute("INSERT INTO events (name, date, location) VALUES (?, ?, ?)", (name, str(date), location))
            conn.commit()
            st.success("✅ Event added!")
            st.experimental_rerun()

    events = c.execute("SELECT id, name FROM events ORDER BY date").fetchall()
    for event in events:
        st.write(f"### {event[1]}")
        attendees = c.execute("SELECT name, email, phone FROM attendees WHERE event_id=?", (event[0],)).fetchall()
        if attendees:
            st.table(attendees)
        else:
            st.write("No attendees yet.")

    conn.close()

# ----------------------------
# Main App Navigation
# ----------------------------
def main():
    st.sidebar.title("📌 Navigation")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.sidebar.success(f"Logged in as {st.session_state['username']} ({st.session_state['role']})")

        menu = ["Home"]
        if st.session_state["role"] == "user":
            menu.append("Register")
        if st.session_state["role"] == "admin":
            menu.append("Admin")

        choice = st.sidebar.radio("Go to", menu)

        if choice == "Home":
            home_page()
        elif choice == "Register" and st.session_state["role"] == "user":
            registration_page()
        elif choice == "Admin" and st.session_state["role"] == "admin":
            admin_dashboard()

        if st.sidebar.button("🚪 Logout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["role"] = ""
            st.success("Logged out successfully.")
            st.experimental_rerun()

# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    init_db()
    main()
