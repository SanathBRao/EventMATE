import streamlit as st
import sqlite3

# ---------------- DATABASE ---------------- #
DB_NAME = "eventmate.db"

def reset_db():
    """Drop and recreate tables (use during dev to avoid schema mismatch)."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()

    # Drop old tables
    c.execute("DROP TABLE IF EXISTS attendees")
    c.execute("DROP TABLE IF EXISTS schedule")
    c.execute("DROP TABLE IF EXISTS announcements")

    # Create tables again
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            hall TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES schedule(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

# Run reset once (wipe old DB schema)
reset_db()


# ---------------- USER PAGES ---------------- #
def show_announcements():
    st.header("📢 Announcements")
    conn = get_connection()
    c = conn.cursor()
    announcements = c.execute("SELECT message FROM announcements ORDER BY id DESC").fetchall()
    conn.close()
    if announcements:
        for a in announcements:
            st.success(a[0])
    else:
        st.info("No announcements yet.")

def register_for_event():
    st.header("📝 Register for an Event")
    conn = get_connection()
    c = conn.cursor()
    events = c.execute("SELECT id, event_name, date, time, hall FROM schedule").fetchall()

    if not events:
        st.warning("No events available for registration yet.")
        return

    event_choices = {f"{e[1]} ({e[2]} {e[3]} - {e[4]})": e[0] for e in events}
    choice = st.selectbox("Select Event", list(event_choices.keys()))
    event_id = event_choices[choice]

    with st.form("registration_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email (must end with @gmail.com)")
        phone = st.text_input("Phone Number")
        submitted = st.form_submit_button("Register")

        if submitted:
            if not name or not email or not phone:
                st.error("⚠️ All fields are required.")
            elif "@gmail.com" not in email:
                st.error("⚠️ Please enter a valid Gmail address.")
            else:
                c.execute("INSERT INTO attendees (event_id, name, email, phone) VALUES (?,?,?,?)",
                          (event_id, name, email, phone))
                conn.commit()
                st.success(f"✅ {name}, you are registered for {choice}!")

    conn.close()

def view_schedule():
    st.header("📅 Event Schedule")
    conn = get_connection()
    c = conn.cursor()
    schedule = c.execute("SELECT event_name, date, time, hall FROM schedule").fetchall()
    conn.close()

    if schedule:
        for s in schedule:
            st.info(f"📌 **{s[0]}** — {s[1]} {s[2]} @ {s[3]}")
    else:
        st.warning("No events scheduled yet.")


# ---------------- ADMIN ---------------- #
def admin_dashboard():
    st.subheader("📊 Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["Announcements", "Schedule", "Attendees"])

    # Manage Announcements
    with tab1:
        st.write("### Add Announcement")
        msg = st.text_area("New Announcement")
        if st.button("Post Announcement"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO announcements (message) VALUES (?)", (msg,))
            conn.commit()
            conn.close()
            st.success("Announcement posted!")

    # Manage Schedule
    with tab2:
        st.write("### Add Event to Schedule")
        with st.form("add_event"):
            name = st.text_input("Event Name")
            date = st.date_input("Date")
            time = st.time_input("Time")
            hall = st.text_input("Hall")
            submitted = st.form_submit_button("Add Event")
            if submitted:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO schedule (event_name, date, time, hall) VALUES (?,?,?,?)",
                          (name, str(date), str(time), hall))
                conn.commit()
                conn.close()
                st.success(f"Event '{name}' added!")

        st.write("### Current Schedule")
        conn = get_connection()
        c = conn.cursor()
        events = c.execute("SELECT id, event_name, date, time, hall FROM schedule").fetchall()
        conn.close()
        if events:
            for e in events:
                st.write(f"🆔 {e[0]} — {e[1]} ({e[2]} {e[3]} - {e[4]})")
        else:
            st.info("No events scheduled.")

    # View Attendees
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
            if attendees:
                for a in attendees:
                    st.write(f"👤 {a[0]} | ✉️ {a[1]} | 📞 {a[2]}")
            else:
                st.info("No attendees registered for this event.")
        conn.close()


def admin_login():
    st.header("🔑 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            admin_dashboard()
        else:
            st.error("Invalid credentials")


# ---------------- MAIN APP ---------------- #
def main():
    st.sidebar.title("📌 EventMate Navigation")
    choice = st.sidebar.radio("Go to", ["Home", "Register", "Schedule", "Admin"])

    if choice == "Home":
        show_announcements()
    elif choice == "Register":
        register_for_event()
    elif choice == "Schedule":
        view_schedule()
    elif choice == "Admin":
        admin_login()

if __name__ == "__main__":
    main()
