import streamlit as st
import sqlite3

# ----------------- DATABASE SETUP -----------------
def init_db():
    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()

    # Events
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    date TEXT,
                    time TEXT,
                    hall TEXT)''')

    # Attendees (linked to events)
    c.execute('''CREATE TABLE IF NOT EXISTS attendees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    FOREIGN KEY(event_id) REFERENCES events(id))''')

    # Announcements
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Admin credentials
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')

    # Default admin
    c.execute("SELECT * FROM admins WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "admin"))

    conn.commit()
    conn.close()

# ----------------- PAGES -----------------
def home_page():
    st.title("🏠 Welcome to EventMate")

    st.header("📢 Announcements")
    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()
    announcements = c.execute("SELECT message, created_at FROM announcements ORDER BY created_at DESC").fetchall()
    conn.close()

    if announcements:
        for msg, created in announcements:
            st.info(f"**{created}** — {msg}")
    else:
        st.write("No announcements yet.")

    st.header("📅 Upcoming Events")
    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()
    events = c.execute("SELECT id, title, description, date, time, hall FROM events").fetchall()
    conn.close()

    if events:
        for eid, title, desc, date, time, hall in events:
            with st.expander(f"📌 {title} — {date} {time} @ {hall}"):
                st.write(desc if desc else "No description available.")
                if st.button(f"Register for {title}", key=f"register_{eid}"):
                    st.session_state.page = "register"
                    st.session_state.selected_event = eid
                    st.rerun()
    else:
        st.write("No upcoming events.")

def register_page():
    st.title("📝 Event Registration")

    event_id = st.session_state.get("selected_event")
    if not event_id:
        st.warning("⚠️ No event selected.")
        return

    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()
    event = c.execute("SELECT title FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()

    if not event:
        st.error("Event not found.")
        return

    st.subheader(f"Register for: {event[0]}")

    name = st.text_input("Full Name")
    email = st.text_input("Email (must end with @gmail.com)")
    phone = st.text_input("Phone Number")

    if st.button("Submit Registration"):
        if not name or not email or not phone:
            st.error("All fields are required.")
        elif "@gmail.com" not in email:
            st.error("Email must be a valid Gmail address.")
        else:
            conn = sqlite3.connect("eventmate.db")
            c = conn.cursor()
            c.execute("INSERT INTO attendees (event_id, name, email, phone) VALUES (?, ?, ?, ?)",
                      (event_id, name, email, phone))
            conn.commit()
            conn.close()
            st.success("✅ Registration successful!")

def admin_login():
    st.title("🔑 Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = sqlite3.connect("eventmate.db")
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        conn.close()

        if admin:
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password.")

def admin_dashboard():
    st.title("📊 Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["📢 Announcements", "📅 Events", "📝 Registrations"])

    # ---------------- ANNOUNCEMENTS ----------------
    with tab1:
        st.subheader("Manage Announcements")
        msg = st.text_area("New Announcement")
        if st.button("Post Announcement"):
            if msg.strip():
                conn = sqlite3.connect("eventmate.db")
                c = conn.cursor()
                c.execute("INSERT INTO announcements (message) VALUES (?)", (msg,))
                conn.commit()
                conn.close()
                st.success("Announcement posted!")
                st.rerun()

        conn = sqlite3.connect("eventmate.db")
        c = conn.cursor()
        announcements = c.execute("SELECT id, message, created_at FROM announcements ORDER BY created_at DESC").fetchall()
        conn.close()

        for aid, message, created in announcements:
            st.write(f"📢 **{message}** ({created})")
            if st.button("Delete", key=f"del_ann_{aid}"):
                conn = sqlite3.connect("eventmate.db")
                c = conn.cursor()
                c.execute("DELETE FROM announcements WHERE id=?", (aid,))
                conn.commit()
                conn.close()
                st.warning("Announcement deleted.")
                st.rerun()

    # ---------------- EVENTS ----------------
    with tab2:
        st.subheader("Manage Events")
        title = st.text_input("Event Title")
        desc = st.text_area("Description")
        date = st.date_input("Date")
        time = st.time_input("Time")
        hall = st.text_input("Hall")

        if st.button("Add Event"):
            if title and hall:
                conn = sqlite3.connect("eventmate.db")
                c = conn.cursor()
                c.execute("INSERT INTO events (title, description, date, time, hall) VALUES (?, ?, ?, ?, ?)",
                          (title, desc, str(date), str(time), hall))
                conn.commit()
                conn.close()
                st.success("Event added successfully!")
                st.rerun()

        conn = sqlite3.connect("eventmate.db")
        c = conn.cursor()
        events = c.execute("SELECT id, title, date, time, hall FROM events").fetchall()
        conn.close()

        for eid, etitle, edate, etime, ehall in events:
            st.write(f"📌 {etitle} — {edate} {etime} @ {ehall}")
            if st.button("Delete", key=f"del_event_{eid}"):
                conn = sqlite3.connect("eventmate.db")
                c = conn.cursor()
                c.execute("DELETE FROM events WHERE id=?", (eid,))
                conn.commit()
                conn.close()
                st.warning("Event deleted.")
                st.rerun()

    # ---------------- REGISTRATIONS ----------------
    with tab3:
        st.subheader("Event Registrations")

        conn = sqlite3.connect("eventmate.db")
        c = conn.cursor()
        events = c.execute("SELECT id, title FROM events").fetchall()
        conn.close()

        if events:
            event_id = st.selectbox("Select Event", [eid for eid, _ in events],
                                    format_func=lambda x: dict(events)[x])

            conn = sqlite3.connect("eventmate.db")
            c = conn.cursor()
            attendees = c.execute("SELECT name, email, phone FROM attendees WHERE event_id=?", (event_id,)).fetchall()
            conn.close()

            if attendees:
                for name, email, phone in attendees:
                    st.write(f"👤 {name} — {email} — {phone}")
            else:
                st.write("No registrations for this event.")
        else:
            st.write("No events available.")

# ----------------- MAIN -----------------
def main():
    st.sidebar.title("📌 Navigation")
    choice = st.sidebar.radio("Go to", ["Home", "Register", "Admin"])

    if choice == "Home":
        home_page()
    elif choice == "Register":
        register_page()
    elif choice == "Admin":
        if st.session_state.get("admin_logged_in"):
            admin_dashboard()
        else:
            admin_login()

if __name__ == "__main__":
    init_db()
    main()
