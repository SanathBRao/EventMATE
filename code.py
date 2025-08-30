import streamlit as st
import sqlite3
import re

# -----------------------
# Database Initialization
# -----------------------
def init_db():
    conn = sqlite3.connect("eventmate.db", check_same_thread=False)
    c = conn.cursor()

    # Schedule table
    c.execute('''CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT,
                    time TEXT,
                    hall TEXT
                )''')

    # Attendees table (linked to schedule)
    c.execute('''CREATE TABLE IF NOT EXISTS attendees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    event_id INTEGER,
                    FOREIGN KEY (event_id) REFERENCES schedule(id)
                )''')

    # Announcements
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    date TEXT
                )''')

    conn.commit()
    return conn, c

conn, c = init_db()

# -----------------------
# Home Page (Announcements)
# -----------------------
def home_page():
    st.header("🎉 Welcome to EventMate")
    st.subheader("📢 Latest Announcements")

    announcements = c.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    if announcements:
        for a in announcements:
            st.info(f"📌 {a[1]}  —  🗓 {a[2]}")
    else:
        st.write("No announcements yet.")

# -----------------------
# Registration Page
# -----------------------
def registration_page():
    st.header("📝 Event Registration")

    schedules = c.execute("SELECT * FROM schedule").fetchall()
    if not schedules:
        st.warning("⚠️ No events available for registration.")
        return

    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        event_choice = st.selectbox("Select Event", [f"{s[1]} ({s[2]}, Hall {s[3]})" for s in schedules])
        submit = st.form_submit_button("Register")

        if submit:
            if not name.strip() or not email.strip() or not phone.strip():
                st.error("⚠️ All fields are required.")
            elif not re.match(r"[^@]+@gmail\.com$", email):
                st.error("⚠️ Please enter a valid Gmail address.")
            else:
                event_id = schedules[[f"{s[1]} ({s[2]}, Hall {s[3]})" for s in schedules].index(event_choice)][0]
                c.execute("INSERT INTO attendees (name, email, phone, event_id) VALUES (?,?,?,?)",
                          (name, email, phone, event_id))
                conn.commit()
                st.success(f"✅ {name} registered successfully for {event_choice}!")

# -----------------------
# Schedule Page
# -----------------------
def schedule_page():
    st.header("📅 Event Schedule")
    schedules = c.execute("SELECT * FROM schedule").fetchall()

    if not schedules:
        st.info("No events scheduled yet.")
    else:
        for s in schedules:
            st.write(f"**{s[1]}** 🕒 {s[2]} 📍 Hall {s[3]}")

# -----------------------
# Admin Login
# -----------------------
def admin_login():
    st.header("🔑 Admin Login")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "admin" and password == "admin123":  # demo credentials
                st.session_state.admin_logged_in = True
                st.success("✅ Logged in successfully!")
            else:
                st.error("❌ Invalid credentials")
    else:
        admin_dashboard()

# -----------------------
# Admin Dashboard
# -----------------------
def admin_dashboard():
    st.header("🛠️ Admin Dashboard")

    # Announcements
    st.subheader("📢 Post Announcement")
    with st.form("announcement_form"):
        message = st.text_area("Announcement")
        date = st.text_input("Date (e.g., 30-Aug-2025)")
        submit_announcement = st.form_submit_button("Post")

        if submit_announcement:
            if not message or not date:
                st.error("⚠️ All fields required")
            else:
                c.execute("INSERT INTO announcements (message, date) VALUES (?,?)",
                          (message, date))
                conn.commit()
                st.success("✅ Announcement posted!")

    # Add Schedule
    st.subheader("➕ Add Event to Schedule")
    with st.form("schedule_form"):
        event_name = st.text_input("Event Name")
        time = st.text_input("Time (e.g., 10:00 AM)")
        hall = st.text_input("Hall")
        submit_schedule = st.form_submit_button("Add Event")

        if submit_schedule:
            if not event_name or not time or not hall:
                st.error("⚠️ All fields are required.")
            else:
                c.execute("INSERT INTO schedule (event_name, time, hall) VALUES (?,?,?)",
                          (event_name, time, hall))
                conn.commit()
                st.success(f"✅ Event '{event_name}' added successfully!")

    # Delete Schedule
    st.subheader("🗑️ Delete Event from Schedule")
    schedules = c.execute("SELECT * FROM schedule").fetchall()
    if schedules:
        schedule_dict = {f"{s[1]} ({s[2]}, Hall {s[3]})": s[0] for s in schedules}
        selected_event = st.selectbox("Select Event to Delete", list(schedule_dict.keys()))
        if st.button("Delete Event"):
            c.execute("DELETE FROM schedule WHERE id=?", (schedule_dict[selected_event],))
            conn.commit()
            st.success("✅ Event deleted successfully!")

    # View Attendees (per event)
    st.subheader("👥 Registered Attendees")
    schedules = c.execute("SELECT * FROM schedule").fetchall()
    if schedules:
        selected_event = st.selectbox("Select Event to View Attendees", 
                                      [f"{s[1]} ({s[2]}, Hall {s[3]})" for s in schedules])
        event_id = schedules[[f"{s[1]} ({s[2]}, Hall {s[3]})" for s in schedules].index(selected_event)][0]
        attendees = c.execute("SELECT name, email, phone FROM attendees WHERE event_id=?", (event_id,)).fetchall()
        if attendees:
            for a in attendees:
                st.write(f"- {a[0]} ({a[1]}, 📞 {a[2]})")
        else:
            st.info("No attendees registered for this event yet.")

    # Logout
    if st.button("🚪 Logout"):
        st.session_state.admin_logged_in = False
        st.success("Logged out successfully")

# -----------------------
# Main Navigation
# -----------------------
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Home", "Registration", "Schedule", "Admin Login"])

if page == "Home":
    home_page()
elif page == "Registration":
    registration_page()
elif page == "Schedule":
    schedule_page()
elif page == "Admin Login":
    admin_login()
