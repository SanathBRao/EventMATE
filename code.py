import streamlit as st
import sqlite3

# ==========================
# DATABASE SETUP
# ==========================
def init_db():
    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()

    # Events table
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    date TEXT,
                    description TEXT)''')

    # Announcements table
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT)''')

    # Attendees table (linked to events)
    c.execute('''CREATE TABLE IF NOT EXISTS attendees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    FOREIGN KEY (event_id) REFERENCES events(id))''')

    # Admins table
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')

    # Ensure default admin exists
    c.execute("SELECT * FROM admins WHERE username=? AND password=?", ("admin", "admin"))
    if not c.fetchone():
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "admin"))

    conn.commit()
    conn.close()

# ==========================
# PAGES
# ==========================
def home_page():
    st.title("🏠 EventMate - Home")

    st.header("📢 Announcements")
    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()
    announcements = c.execute("SELECT message FROM announcements ORDER BY id DESC").fetchall()
    conn.close()

    if announcements:
        for ann in announcements:
            st.info(ann[0])
    else:
        st.write("No announcements yet.")

    st.header("📅 Upcoming Events")
    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()
    events = c.execute("SELECT id, name, date, description FROM events ORDER BY date ASC").fetchall()
    conn.close()

    if events:
        for event in events:
            with st.expander(f"{event[1]} ({event[2]})"):
                st.write(event[3])
                if st.button(f"Register for {event[1]}", key=f"reg_{event[0]}"):
                    st.session_state.selected_event = event[0]
                    st.session_state.page = "register"
                    st.rerun()
    else:
        st.write("No events available.")

def register_page():
    st.title("📝 Event Registration")

    event_id = st.session_state.get("selected_event", None)
    if not event_id:
        st.error("⚠️ No event selected.")
        return

    conn = sqlite3.connect("eventmate.db")
    c = conn.cursor()
    event = c.execute("SELECT name FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()

    if not event:
        st.error("Event not found.")
        return

    st.subheader(f"Register for {event[0]}")

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")

    if st.button("Submit Registration"):
        if not name or not email or not phone:
            st.error("All fields are required.")
        elif not email.endswith("@gmail.com"):
            st.error("Email must be a valid @gmail.com address.")
        else:
            conn = sqlite3.connect("eventmate.db")
            c = conn.cursor()
            c.execute("INSERT INTO attendees (event_id, name, email, phone) VALUES (?,?,?,?)",
                      (event_id, name, email, phone))
            conn.commit()
            conn.close()
            st.success("✅ Registered successfully!")

def admin_login():
    st.title("🔐 Admin Login")

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
    st.title("⚙️ Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["📢 Announcements", "📅 Events", "🧑‍🤝‍🧑 Attendees"])

    # Announcements
    with tab1:
        st.subheader("Manage Announcements")
        new_announcement = st.text_area("Add Announcement")
        if st.button("Post Announcement"):
            if new_announcement.strip():
                conn = sqlite3.connect("eventmate.db")
                c = conn.cursor()
                c.execute("INSERT INTO announcements (message) VALUES (?)", (new_announcement,))
                conn.commit()
                conn.close()
                st.success("✅ Announcement posted!")
                st.rerun()

    # Events
    with tab2:
        st.subheader("Manage Events")
        name = st.text_input("Event Name")
        date = st.date_input("Event Date")
        description = st.text_area("Description")
        if st.button("Add Event"):
            conn = sqlite3.connect("eventmate.db")
            c = conn.cursor()
            c.execute("INSERT INTO events (name, date, description) VALUES (?,?,?)",
                      (name, str(date), description))
            conn.commit()
            conn.close()
            st.success("✅ Event added!")
            st.rerun()

        conn = sqlite3.connect("eventmate.db")
        c = conn.cursor()
        events = c.execute("SELECT id, name, date FROM events").fetchall()
        conn.close()
        st.write("### Existing Events")
        for e in events:
            st.write(f"{e[1]} ({e[2]})")

    # Attendees
    with tab3:
        st.subheader("View Attendees by Event")
        conn = sqlite3.connect("eventmate.db")
        c = conn.cursor()
        events = c.execute("SELECT id, name FROM events").fetchall()
        conn.close()
        event_dict = {e[1]: e[0] for e in events}
        event_choice = st.selectbox("Select Event", list(event_dict.keys()) if event_dict else [])
        if event_choice:
            conn = sqlite3.connect("eventmate.db")
            c = conn.cursor()
            attendees = c.execute("SELECT name, email, phone FROM attendees WHERE event_id=?",
                                  (event_dict[event_choice],)).fetchall()
            conn.close()
            if attendees:
                st.table(attendees)
            else:
                st.write("No attendees yet.")

    if st.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

# ==========================
# MAIN
# ==========================
def main():
    init_db()

    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    menu = ["Home", "Register", "Admin"]
    choice = st.sidebar.radio("Navigate", menu)

    if choice == "Home":
        st.session_state.page = "home"
    elif choice == "Register":
        st.session_state.page = "register"
    elif choice == "Admin":
        if st.session_state.admin_logged_in:
            st.session_state.page = "admin_dashboard"
        else:
            st.session_state.page = "admin_login"

    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "admin_login":
        admin_login()
    elif st.session_state.page == "admin_dashboard":
        admin_dashboard()

if __name__ == "__main__":
    main()
