import streamlit as st
import sqlite3
import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import google.generativeai as genai

# ===============================
# 🎯 CONFIG
# ===============================
st.set_page_config(page_title="Smart Event Organizer", layout="wide")

# 🔑 Configure API key
API_KEY = os.getenv("AIzaSyBhvjm6m7A2ZrJ7ogDl7GW8xt6dcY53M4c")
if not API_KEY:
    st.error("⚠️ GOOGLE_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=API_KEY)

# LangChain LLM
llm_text = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# ===============================
# 🗄️ DATABASE SETUP
# ===============================
conn = sqlite3.connect("eventmate.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                event TEXT,
                timestamp TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                timestamp TEXT)""")

conn.commit()

# ===============================
# 📌 SIDEBAR MENU
# ===============================
st.sidebar.title("📋 Navigation")
menu = st.sidebar.radio(
    "Go to",
    ["🏠 Home", "📝 Register", "📅 Schedule", "💬 Chatbot", "🛠 Admin Dashboard"]
)

# ===============================
# 🏠 HOME
# ===============================
if menu == "🏠 Home":
    st.title("🎉 Smart Event Organizer")
    st.subheader("One-stop solution for registrations, scheduling, and assistance")

    st.markdown("""
    Welcome to the **Smart Event Organizer** 🚀  
    Features:
    - Register for events easily  
    - View upcoming schedules  
    - Ask our AI Chatbot for instant help  
    - Check announcements from organizers
    """)

    st.subheader("📢 Announcements")
    announcements = c.execute("SELECT message, timestamp FROM announcements ORDER BY id DESC").fetchall()
    if announcements:
        for a in announcements:
            st.info(f"📌 {a[0]}  _(Posted: {a[1]})_")
    else:
        st.write("No announcements yet.")

# ===============================
# 📝 REGISTRATION
# ===============================
elif menu == "📝 Register":
    st.title("📝 Event Registration")

    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        event = st.selectbox("Select Event", ["Hackathon", "Workshop", "Seminar", "Cultural Fest"])
        submit = st.form_submit_button("Register")

    if submit:
        if name and email and event:
            c.execute("INSERT INTO attendees (name, email, event, timestamp) VALUES (?,?,?,?)",
                      (name, email, event, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success(f"✅ {name}, you are registered for {event}!")
        else:
            st.error("⚠️ Please fill all fields.")

    st.subheader("📌 Registered Attendees")
    attendees = c.execute("SELECT name, email, event, timestamp FROM attendees").fetchall()
    for a in attendees:
        st.write(f"👤 {a[0]} | ✉️ {a[1]} | 🎯 {a[2]} | ⏰ {a[3]}")

# ===============================
# 📅 SCHEDULE
# ===============================
elif menu == "📅 Schedule":
    st.title("📅 Event Schedule")
    schedule = {
        "Hackathon": "9:00 AM - 6:00 PM",
        "Workshop": "10:00 AM - 1:00 PM",
        "Seminar": "2:00 PM - 4:00 PM",
        "Cultural Fest": "6:30 PM - 9:30 PM"
    }
    for event, timing in schedule.items():
        st.write(f"📌 **{event}** → 🕒 {timing}")

# ===============================
# 💬 CHATBOT
# ===============================
elif menu == "💬 Chatbot":
    st.title("🤖 Event Assistant Chatbot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.llm_history = []

    # Chat input
    user_input = st.chat_input("Ask me anything about the event...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.llm_history.append(HumanMessage(content=user_input))

        with st.spinner("🤔 Thinking..."):
            try:
                response = llm_text.invoke(st.session_state.llm_history)
                st.session_state.chat_history.append({"role": "assistant", "content": response.content})
                st.session_state.llm_history.append(AIMessage(content=response.content))
            except Exception as e:
                st.session_state.chat_history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})

    # Display Chat
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

# ===============================
# 🛠 ADMIN DASHBOARD
# ===============================
elif menu == "🛠 Admin Dashboard":
    st.title("🛠 Admin Dashboard")

    # Simple login system
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if password == "admin123":  # demo password
                st.session_state.admin_logged_in = True
                st.success("✅ Logged in as Admin")
            else:
                st.error("❌ Wrong password")
    else:
        tab1, tab2 = st.tabs(["👥 Manage Attendees", "📢 Manage Announcements"])

        # ======================
        # 👥 Manage Attendees
        # ======================
        with tab1:
            st.subheader("👥 Registered Attendees")
            event_filter = st.selectbox("Filter by Event", ["All", "Hackathon", "Workshop", "Seminar", "Cultural Fest"])
            
            if event_filter == "All":
                attendees = c.execute("SELECT id, name, email, event, timestamp FROM attendees").fetchall()
            else:
                attendees = c.execute("SELECT id, name, email, event, timestamp FROM attendees WHERE event=?",
                                      (event_filter,)).fetchall()

            if attendees:
                for a in attendees:
                    col1, col2, col3 = st.columns([4, 2, 1])
                    with col1:
                        st.write(f"👤 {a[1]} | ✉️ {a[2]} | 🎯 {a[3]} | ⏰ {a[4]}")
                    with col3:
                        if st.button("🗑 Delete", key=f"del_{a[0]}"):
                            c.execute("DELETE FROM attendees WHERE id=?", (a[0],))
                            conn.commit()
                            st.success(f"Deleted {a[1]}")
                            st.rerun()
            else:
                st.info("No attendees found.")

        # ======================
        # 📢 Manage Announcements
        # ======================
        with tab2:
            st.subheader("📢 Post Announcement")
            new_announcement = st.text_area("Write an announcement...")
            if st.button("Post"):
                if new_announcement.strip():
                    c.execute("INSERT INTO announcements (message, timestamp) VALUES (?, ?)",
                              (new_announcement, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success("✅ Announcement posted!")
                    st.rerun()
                else:
                    st.error("⚠️ Please enter a message.")

            st.subheader("📜 Existing Announcements")
            announcements = c.execute("SELECT id, message, timestamp FROM announcements ORDER BY id DESC").fetchall()
            for a in announcements:
                col1, col2 = st.columns([6,1])
                with col1:
                    st.info(f"{a[1]} _(Posted: {a[2]})_")
                with col2:
                    if st.button("🗑", key=f"del_ann_{a[0]}"):
                        c.execute("DELETE FROM announcements WHERE id=?", (a[0],))
                        conn.commit()
                        st.success("Announcement deleted!")
                        st.rerun()
