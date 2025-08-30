import streamlit as st
import sqlite3
import re

# ======================
# 📂 Database Setup
# ======================
conn = sqlite3.connect("eventmate.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT,
                time TEXT,
                hall TEXT
            )''')
conn.commit()

# ======================
# 🎨 Streamlit UI
# ======================
st.set_page_config(page_title="EventMate App", layout="wide")
st.title("🎉 EventMate – Event Management App")

menu = ["Home", "Register", "Admin Dashboard"]
choice = st.sidebar.selectbox("📌 Navigate", menu)

# ======================
# 🏠 Home
# ======================
if choice == "Home":
    st.header("📢 Announcements")
    announcements = c.execute("SELECT message FROM announcements").fetchall()
    if announcements:
        for ann in announcements:
            st.info(f"📌 {ann[0]}")
    else:
        st.write("No announcements yet.")

    st.header("📅 Event Schedule")
    schedule = c.execute("SELECT event, time, hall FROM schedule").fetchall()
    if schedule:
        for s in schedule:
            st.success(f"**{s[0]}** → 🕒 {s[1]} • Hall {s[2]}")
    else:
        st.write("No schedule available.")

# ======================
# 📝 Registration
# ======================
elif choice == "Register":
    st.header("📝 Register for Event")
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        submit = st.form_submit_button("Register")

    if submit:
        if not name.strip() or not email.strip() or not phone.strip():
            st.error("⚠️ All fields are required!")
        elif not re.match(r"[^@]+@gmail\.com$", email):
            st.error("⚠️ Email must be a valid Gmail address (ends with @gmail.com).")
        else:
            c.execute("INSERT INTO attendees (name, email, phone) VALUES (?,?,?)",
                      (name, email, phone))
            conn.commit()
            st.success("✅ Successfully Registered!")

# ======================
# 🔑 Admin Dashboard
# ======================
elif choice == "Admin Dashboard":
    st.header("🛠 Admin Dashboard")
    tabs = st.tabs(["👥 Attendees", "📢 Announcements", "📅 Schedule"])

    # 👥 Manage Attendees
    with tabs[0]:
        st.subheader("👥 Registered Attendees")
        attendees = c.execute("SELECT id, name, email, phone FROM attendees").fetchall()
        if attendees:
            for a in attendees:
                with st.expander(f"{a[1]} ({a[2]})"):
                    st.write(f"📞 Phone: {a[3]}")
                    if st.button("🗑 Delete", key=f"del_att_{a[0]}"):
                        c.execute("DELETE FROM attendees WHERE id=?", (a[0],))
                        conn.commit()
                        st.success("Attendee deleted!")
                        st.rerun()
        else:
            st.info("No attendees registered yet.")

    # 📢 Manage Announcements
    with tabs[1]:
        st.subheader("📢 Add New Announcement")
        with st.form("add_announcement"):
            new_msg = st.text_input("Announcement Message")
            add_submit = st.form_submit_button("Add")
        if add_submit and new_msg.strip():
            c.execute("INSERT INTO announcements (message) VALUES (?)", (new_msg,))
            conn.commit()
            st.success("✅ Announcement added!")
            st.rerun()

        st.subheader("📜 Existing Announcements")
        anns = c.execute("SELECT id, message FROM announcements").fetchall()
        if anns:
            for ann in anns:
                with st.expander(f"📌 {ann[1]}"):
                    new_text = st.text_input("Edit Message", value=ann[1], key=f"edit_ann_{ann[0]}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Update", key=f"upd_ann_{ann[0]}"):
                            c.execute("UPDATE announcements SET message=? WHERE id=?", (new_text, ann[0]))
                            conn.commit()
                            st.success("Announcement updated!")
                            st.rerun()
                    with col2:
                        if st.button("🗑 Delete", key=f"del_ann_{ann[0]}"):
                            c.execute("DELETE FROM announcements WHERE id=?", (ann[0],))
                            conn.commit()
                            st.success("Announcement deleted!")
                            st.rerun()
        else:
            st.info("No announcements yet.")

    # 📅 Manage Schedule
    with tabs[2]:
        st.subheader("📅 Add New Schedule Item")
        with st.form("add_schedule"):
            event_name = st.text_input("Event Name")
            time = st.text_input("Time (e.g., 9:00 AM - 6:00 PM)")
            hall = st.text_input("Hall No/Name")
            add_submit = st.form_submit_button("Add Schedule")

        if add_submit:
            if event_name.strip() and time.strip() and hall.strip():
                c.execute("INSERT INTO schedule (event, time, hall) VALUES (?,?,?)",
                          (event_name, time, hall))
                conn.commit()
                st.success(f"✅ Schedule added for {event_name}")
                st.rerun()
            else:
                st.error("⚠️ Please fill all fields.")

        st.subheader("📜 Existing Schedule")
        schedule = c.execute("SELECT id, event, time, hall FROM schedule").fetchall()
        if schedule:
            for s in schedule:
                with st.expander(f"📌 {s[1]} → 🕒 {s[2]} • Hall {s[3]}"):
                    with st.form(f"edit_form_{s[0]}"):
                        new_event = st.text_input("Event Name", value=s[1], key=f"e_{s[0]}")
                        new_time = st.text_input("Time", value=s[2], key=f"t_{s[0]}")
                        new_hall = st.text_input("Hall", value=s[3], key=f"h_{s[0]}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Update"):
                                c.execute("UPDATE schedule SET event=?, time=?, hall=? WHERE id=?",
                                          (new_event, new_time, new_hall, s[0]))
                                conn.commit()
                                st.success("✅ Schedule updated!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("🗑 Delete"):
                                c.execute("DELETE FROM schedule WHERE id=?", (s[0],))
                                conn.commit()
                                st.success("Schedule deleted!")
                                st.rerun()
        else:
            st.info("No schedule items yet.")
