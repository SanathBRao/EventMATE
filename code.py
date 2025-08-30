import streamlit as st
import sqlite3
import re

# -----------------------
# Database Initialization
# -----------------------
def init_db():
    conn = sqlite3.connect("eventmate.db", check_same_thread=False)
    c = conn.cursor()

    # Attendees table
    c.execute('''CREATE TABLE IF NOT EXISTS attendees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT
                )''')

    # 🔧 Ensure phone column exists
    try:
        c.execute("ALTER TABLE attendees ADD COLUMN phone TEXT;")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Schedule table
    c.execute('''CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT,
                    time TEXT,
                    hall TEXT
                )''')
    conn.commit()
    return conn, c


conn, c = init_db()

# -----------------------
# Registration Page
# -----------------------
def registration_page():
    st.header("📝 Event Registration")

    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        submit = st.form_submit_button("Register")

        if submit:
            # Validation
            if not name.strip() or not email.strip() or not phone.strip():
                st.error("⚠️ All fields are required.")
            elif not re.match(r"[^@]+@gmail\.com$", email):
                st.error("⚠️ Please enter a valid Gmail address.")
            else:
                c.execute("INSERT INTO attendees (name, email, phone) VALUES (?,?,?)",
                          (name, email, phone))
                conn.commit()
                st.success(f"✅ {name} registered successfully!")


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
# Admin Dashboard
# -----------------------
def admin_dashboard():
    st.header("🛠️ Admin Dashboard")

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

    # View Attendees
    st.subheader("👥 Registered Attendees")
    attendees = c.execute("SELECT * FROM attendees").fetchall()
    if attendees:
        for a in attendees:
            st.write(f"- {a[1]} ({a[2]}, 📞 {a[3] if a[3] else 'N/A'})")
    else:
        st.info("No attendees registered yet.")


# -----------------------
# Main Navigation
# -----------------------
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Registration", "Schedule", "Admin Dashboard"])

if page == "Registration":
    registration_page()
elif page == "Schedule":
    schedule_page()
elif page == "Admin Dashboard":
    admin_dashboard()
