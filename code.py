import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

# Load API key
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
llm_text = None
if API_KEY:
    llm_text = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
else:
    st.warning("⚠️ GOOGLE_API_KEY missing. Add it in .env file.")

# Database connection
def get_announcements():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT message FROM announcements ORDER BY created_at DESC LIMIT 5")
    data = c.fetchall()
    conn.close()
    return [d[0] for d in data]

def get_schedule():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT title, time, hall FROM schedule ORDER BY time ASC LIMIT 5")
    data = c.fetchall()
    conn.close()
    return data

# Streamlit UI
st.title("🤖 EventMate Chatbot")
st.write("Ask about event schedule, announcements, or just chat!")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "llm_history" not in st.session_state:
    st.session_state.llm_history = []

prompt = st.chat_input("Ask me something...")

if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.session_state.llm_history.append(HumanMessage(content=prompt))

    # Special queries for DB
    if "announcement" in prompt.lower():
        anns = get_announcements()
        response = "📢 Latest Announcements:\n" + "\n".join([f"- {a}" for a in anns]) if anns else "No announcements yet."
    elif "schedule" in prompt.lower() or "when" in prompt.lower():
        sched = get_schedule()
        if sched:
            response = "📅 Upcoming Schedule:\n" + "\n".join([f"- {s[0]} at {s[1]} in {s[2]}" for s in sched])
        else:
            response = "No events scheduled yet."
    elif llm_text:
        try:
            response_obj = llm_text.invoke(st.session_state.llm_history)
            response = response_obj.content
        except Exception as e:
            response = f"❌ Chat error: {e}"
    else:
        response = "⚠️ Chatbot is disabled (missing API key)."

    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.session_state.llm_history.append(AIMessage(content=response))

# Show chat
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])
