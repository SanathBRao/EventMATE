import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime

DB_FILE = "eventmate.db"

# ----------------------------
# Password Hashing
# ----------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# ----------------------------
# Custom CSS for Styling
# ----------------------------
def set_custom_theme():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #E3F2FD, #E8F6F3);
            font-family: 'Segoe UI', sans-serif;
        }
        section[data-testid="stSidebar"] {
            background-color: #2E4053 !important;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] label {
            color: white !important;
        }
        div.stButton > button {
            background-color: #3498DB;
            color: white;
            border-radius: 10px;
            border: none;
            padding: 0.6em;
            font-weight: bold;
        }
        div.stButton > button:hover {
            background-color: #2ECC71;
            color: white;
        }
        h1, h2, h3 { color: #154360 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# ----------------------------
# Database Setup
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    timestamp TEXT
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    location TEXT NOT NULL
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS attendees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    username TEXT NOT NULL,
                    event_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT CHECK(role IN ('user','admin'))
                )""")

    # Default admin
    c.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("admin", hash_password("admin123"), "admin"))

    conn.commit()
    conn.close()

# ----------------------------
# Reset DB
# ----------------------------
def reset_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()

# ----------------------------
# Announcements
# ----------------------------
def show_announcements():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    announcements = c.execute("SELECT message, timestamp FROM announcements ORDER BY id DESC").fetchall()
    conn.close()

    if announcements:
        st.subheader("📢 Latest Announcements")
        for msg, ts in announcements:
            st.markdown(
                f"""
                <div style="background:#FDEDEC; padding:15px; border-radius:10px; 
                            margin-bottom:10px; box-shadow:0px 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="color:#C0392B;">📌 {msg}</h4>
                    <p style="font-size:12px;color:gray;">🕒 {ts}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No announcements yet.")

# ----------------------------
# Payment Page
# ----------------------------
def payment_page(event_id, event_name):
    st.markdown(f"<h2 style='color:#2E86C1;'>💳 Payment for {event_name}</h2>", unsafe_allow_html=True)
    st.write("Please complete the payment to confirm your registration.")

    col1, col2 = st.columns(2)
    with col1:
        card_number = st.text_input("Card Number")
        expiry = st.text_input("Expiry (MM/YY)")
        cvv = st.text_input("CVV", type="password")
    with col2:
        upi = st.text_input("Or Pay via UPI ID")

    if st.button("✅ Pay Now", use_container_width=True):
        if (card_number and expiry and cvv) or upi:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE attendees SET status='paid' WHERE event_id=? AND username=?",
                      (event_id, st.session_state["username"]))
            conn.commit()
            conn.close()
            st.success("🎉 Payment Successful! You are now fully registered.")
        else:
            st.error("⚠️ Please enter card details or UPI ID.")

# ----------------------------
# Registration
# ----------------------------
def registration_page(event_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    event = c.execute("SELECT name FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()

    st.markdown(f"<h2 style='color:#CA6F1E;'>📝 Register for {event[0]}</h2>", unsafe_allow_html=True)

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
                st.error("⚠️ Phone number must be exactly 10 digits.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""INSERT INTO attendees (name, email, phone, username, event_id) 
                             VALUES (?, ?, ?, ?, ?)""",
                          (name, email, phone, st.session_state['username'], event_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Registered for {event[0]}! Please complete payment.")
                payment_page(event_id, event[0])

# ----------------------------
# User Dashboard
# ----------------------------
def user_dashboard():
    st.markdown("<h2 style='color:#1ABC9C;'>🎉 My Registrations</h2>", unsafe_allow_html=True)
    show_announcements()
    st.divider()

    username = st.session_state.get("username")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    regs = c.execute("""SELECT e.id, e.name, e.date, e.location, a.status
                        FROM attendees a
                        JOIN events e ON a.event_id = e.id
                        WHERE a.username=?""", (username,)).fetchall()
    conn.close()

    if regs:
        for r in regs:
            with st.expander(f"🎯 {r[1]} on {r[2]} at {r[3]} [{r[4]}]"):
                col1, col2 = st.columns([4,1])
                with col1:
                    st.write(f"✅ Status: {r[4]}")
                with col2:
                    if st.button("❌ Cancel", key=f"cancel{r[0]}"):
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("DELETE FROM attendees WHERE event_id=? AND username=?", (r[0], username))
                        conn.commit()
                        conn.close()
                        st.success(f"❌ Cancelled registration for {r[1]}")
                        st.rerun()
    else:
        st.info("No registrations yet.")

# ----------------------------
# Admin Dashboard
# ----------------------------
def admin_dashboard():
    st.markdown("<h2 style='color:#C0392B;'>🛠️ Admin Dashboard</h2>", unsafe_allow_html=True)
    show_announcements()
    st.divider()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if st.button("⚠️ Reset Database (Danger)", use_container_width=True):
        reset_db()
        st.success("✅ Database reset!")
        st.rerun()

    st.subheader("📢 Manage Announcements")
    with st.form("add_announcement"):
        message = st.text_input("New Announcement")
        submit = st.form_submit_button("Add")
        if submit and message:
            c.execute("INSERT INTO announcements (message, timestamp) VALUES (?, ?)",
                      (message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("✅ Announcement added!")
            st.rerun()

    st.subheader("📅 Manage Events")
    with st.form("add_event"):
        name = st.text_input("Event Name")
        date = st.date_input("Event Date")
        location = st.text_input("Event Location")
        submit = st.form_submit_button("Add Event")
        if submit and name and location:
            c.execute("INSERT INTO events (name, date, location) VALUES (?, ?, ?)",
                      (name, str(date), location))
            conn.commit()
            st.success("✅ Event added!")
            st.rerun()

    st.subheader("👥 View Attendees")
    events = c.execute("SELECT id, name FROM events ORDER BY date").fetchall()
    event_names = ["All Events"] + [e[1] for e in events]
    event_choice = st.selectbox("Filter by Event", event_names)

    if event_choice == "All Events":
        attendees = c.execute("""SELECT a.name, a.email, a.phone, e.name, e.date, a.status
                                 FROM attendees a
                                 JOIN events e ON a.event_id = e.id""").fetchall()
    else:
        event_id = [e[0] for e in events if e[1] == event_choice][0]
        attendees = c.execute("""SELECT a.name, a.email, a.phone, e.name, e.date, a.status
                                 FROM attendees a
                                 JOIN events e ON a.event_id = e.id
                                 WHERE e.id=?""", (event_id,)).fetchall()

    if attendees:
        for a in attendees:
            st.markdown(f"""
                <div style='background:#EAF2F8; padding:10px; border-radius:8px; margin-bottom:8px;'>
                    👤 <b>{a[0]}</b> | ✉️ {a[1]} | 📞 {a[2]} | 🎯 {a[3]} ({a[4]}) | 💳 Status: {a[5]}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No attendees found for this event.")

    conn.close()

# ----------------------------
# Login / Signup
# ----------------------------
def login_page():
    st.markdown("<h2 style='color:#2E86C1;'>🔑 Login</h2>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
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

    if st.button("Go to Signup"):
        st.session_state["page"] = "signup"
        st.rerun()

def signup_page():
    st.markdown("<h2 style='color:#28B463;'>📝 Signup</h2>", unsafe_allow_html=True)
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")

    if st.button("Create Account"):
        if not new_username or not new_password:
            st.error("⚠️ Fill all fields.")
        else:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')",
                          (new_username, hash_password(new_password)))
                conn.commit()
                st.success("✅ Account created! Please login.")
                st.session_state["page"] = "login"
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("⚠️ Username already exists.")
            conn.close()

# ----------------------------
# Main App
# ----------------------------
def main():
    set_custom_theme()
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
        st.sidebar.success(f"👤 {st.session_state['username']} ({st.session_state['role']})")

        if st.session_state["role"] == "user":
            menu = ["Home", "My Registrations"]
        else:
            menu = ["Home", "Admin"]

        choice = st.sidebar.radio("Go to", menu)

        if choice == "Home":
            show_announcements()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            events = c.execute("SELECT id, name, date, location FROM events").fetchall()
            conn.close()
            st.subheader("📅 Available Events")
            for e in events:
                if st.button(f"Register for {e[1]}", key=f"reg{e[0]}"):
                    registration_page(e[0])

        elif choice == "My Registrations":
            user_dashboard()
        elif choice == "Admin":
            admin_dashboard()

        if st.sidebar.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    init_db()
    main()
