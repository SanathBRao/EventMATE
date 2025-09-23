import streamlit as st
import sqlite3
import os
import hashlib

DB_FILE = "eventmate.db"

# ----------------------------
# Password Hashing
# ----------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

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

    # Attendees
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            username TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    """)

    # Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('user','admin'))
        )
    """)

    # Feedback
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            comments TEXT,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    """)

    # Insert default admin if missing
    c.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("admin", hash_password("admin123"), "admin"))

    conn.commit()
    conn.close()

# ----------------------------
# Reset Database
# ----------------------------
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

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Login", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT password, role FROM users WHERE username=?", (username,))
            account = c.fetchone()
            conn.close()

            if account and check_password(password, account[0]):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = account[1]
                st.success(f"✅ Logged in as {account[1].capitalize()}")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    with col2:
        if st.button("Go to Signup", use_container_width=True):
            st.session_state["page"] = "signup"
            st.rerun()

# ----------------------------
# Signup Page
# ----------------------------
def signup_page():
    st.title("📝 Signup")

    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")

    if st.button("Create Account", use_container_width=True):
        if not new_username or not new_password:
            st.error("⚠️ Please fill all fields.")
        elif len(new_password) < 6:
            st.error("⚠️ Password must be at least 6 characters long.")
        elif not any(c.isdigit() for c in new_password):
            st.error("⚠️ Password must contain at least one number.")
        elif not any(c.isalpha() for c in new_password):
            st.error("⚠️ Password must contain at least one letter.")
        else:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')",
                          (new_username, hash_password(new_password)))
                conn.commit()
                st.success("✅ Account created! Please login now.")
                st.session_state["page"] = "login"
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("⚠️ Username already exists. Try another.")
            conn.close()

    if st.button("⬅️ Back to Login", use_container_width=True):
        st.session_state["page"] = "login"
        st.rerun()

# ----------------------------
# Home Page
# ----------------------------
def home_page():
    st.title("🏠 EventMate")
    st.subheader("📢 Announcements")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    announcements = c.execute("SELECT message FROM announcements ORDER BY id DESC").fetchall()
    conn.close()

    if announcements:
        for ann in announcements:
            st.info(ann[0])
    else:
        st.write("No announcements yet.")

    st.subheader("📅 Upcoming Events")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
                    st.rerun()
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
            elif not phone.isdigit() or len(phone) != 10:
                st.error("⚠️ Phone number must be exactly 10 digits (numbers only).")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO attendees (name, email, phone, username, event_id) VALUES (?, ?, ?, ?, ?)",
                          (name, email, phone, st.session_state['username'], event_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Registered successfully for {event[0]}!")

# ----------------------------
# User Dashboard
# ----------------------------
def user_dashboard():
    st.title("🎉 My Registrations")

    username = st.session_state.get("username")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    regs = c.execute("""
        SELECT e.id, e.name, e.date, e.location, a.name, a.email, a.phone
        FROM attendees a
        JOIN events e ON a.event_id = e.id
        WHERE a.username=?
    """, (username,)).fetchall()
    conn.close()

    if regs:
        for r in regs:
            st.write(f"### {r[1]} ({r[2]} @ {r[3]})")
            st.write(f"- You registered as: {r[4]} | {r[5]} | {r[6]}")

            # Show others
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            others = c.execute("SELECT name, email, phone FROM attendees WHERE event_id=?", (r[0],)).fetchall()
            conn.close()
            st.write("👥 Other Registered People:")
            st.table(others)

            # Feedback section
            st.write("⭐ Leave Feedback for this Event")
            rating = st.slider(f"Rate {r[1]} (1 = Poor, 5 = Excellent)", 1, 5, 3, key=f"rate{r[0]}")
            comments = st.text_area("Your comments (optional)", key=f"comm{r[0]}")
            if st.button("Submit Feedback", key=f"fbbtn{r[0]}"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO feedback (username, event_id, rating, comments) VALUES (?, ?, ?, ?)",
                          (st.session_state['username'], r[0], rating, comments))
                conn.commit()
                conn.close()
                st.success("✅ Feedback submitted successfully!")
                st.rerun()
    else:
        st.info("You have not registered for any events yet.")

# ----------------------------
# Admin Dashboard
# ----------------------------
def admin_dashboard():
    st.title("🛠️ Admin Dashboard")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Reset DB
    if st.button("⚠️ Reset Database (Danger)"):
        reset_db()
        st.success("✅ Database has been reset!")
        st.rerun()

    # Announcements
    st.subheader("📢 Manage Announcements")
    with st.form("add_announcement"):
        message = st.text_input("New Announcement")
        submit = st.form_submit_button("Add")
        if submit and message:
            c.execute("INSERT INTO announcements (message) VALUES (?)", (message,))
            conn.commit()
            st.success("✅ Announcement added!")
            st.rerun()

    announcements = c.execute("SELECT id, message FROM announcements ORDER BY id DESC").fetchall()
    for ann in announcements:
        if st.button(f"❌ Delete: {ann[1][:30]}...", key=f"delann{ann[0]}"):
            c.execute("DELETE FROM announcements WHERE id=?", (ann[0],))
            conn.commit()
            st.success("✅ Announcement deleted!")
            st.rerun()

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
            st.rerun()

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
# Post-Event Analysis
# ----------------------------
def post_event_analysis():
    st.title("📊 Post-Event Analysis")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    events = c.execute("SELECT id, name FROM events").fetchall()

    if not events:
        st.info("No events available for analysis.")
        return

    for e in events:
        st.subheader(f"📌 {e[1]}")

        # Total registrations
        total_regs = c.execute("SELECT COUNT(*) FROM attendees WHERE event_id=?", (e[0],)).fetchone()[0]

        # Feedback stats
        avg_rating = c.execute("SELECT AVG(rating) FROM feedback WHERE event_id=?", (e[0],)).fetchone()[0]
        feedbacks = c.execute("SELECT username, rating, comments FROM feedback WHERE event_id=?", (e[0],)).fetchall()

        st.write(f"👥 Total Registrations: {total_regs}")
        st.write(f"⭐ Average Rating: {avg_rating:.1f}" if avg_rating else "⭐ No feedback yet")

        if feedbacks:
            st.markdown("📝 **Feedback received:**")
            for fb in feedbacks:
                st.markdown(f"- **{fb[0]}** rated {fb[1]} ⭐ — {fb[2] if fb[2] else 'No comment'}")
        else:
            st.info("No feedback submitted.")

    conn.close()

# ----------------------------
# Main App
# ----------------------------
def main():
    st.sidebar.title("📌 Navigation")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    if not st.session_state["logged_in"]:
        if st.session_state["page"] == "login":
            login_page()
        elif st.session_state["page"] == "signup":
            signup_page()
    else:
        st.sidebar.success(f"Logged in as {st.session_state['username']} ({st.session_state['role']})")

        menu = ["Home"]
        if st.session_state["role"] == "user":
            menu.extend(["Register", "My Registrations"])
        if st.session_state["role"] == "admin":
            menu.append("Admin")
            menu.append("Post-Event Analysis")

        choice = st.sidebar.radio("Go to", menu)

        if choice == "Home":
            home_page()
        elif choice == "Register" and st.session_state["role"] == "user":
            registration_page()
        elif choice == "My Registrations" and st.session_state["role"] == "user":
            user_dashboard()
        elif choice == "Admin" and st.session_state["role"] == "admin":
            admin_dashboard()
        elif choice == "Post-Event Analysis" and st.session_state["role"] == "admin":
            post_event_analysis()

        if st.sidebar.button("🚪 Logout"):
            st.session_state.clear()
            st.success("Logged out successfully.")
            st.rerun()

# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    init_db()
    main()
