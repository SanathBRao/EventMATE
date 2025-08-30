# app.py
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
from datetime import datetime

# ---- CONFIG ----
st.set_page_config(page_title="Smart Event Organizer", layout="wide")

# ---- SESSION STATE ----
if "events" not in st.session_state:
    st.session_state.events = []
if "attendees" not in st.session_state:
    st.session_state.attendees = {}

# ---- HEADER ----
st.markdown(
    """
    <style>
        .main-title { font-size:36px; font-weight:bold; color:#2E86C1; }
        .event-card { padding:15px; border-radius:12px; background:#F4F6F7; margin-bottom:15px; box-shadow:0px 2px 6px rgba(0,0,0,0.1); }
        .attendee-badge { background:#2ECC71; padding:6px 10px; border-radius:8px; color:white; margin:3px; display:inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🎉 Smart Event Organizer</p>', unsafe_allow_html=True)
st.caption("A modern event planning and attendee management tool")

# ---- SIDEBAR: ADD EVENT ----
st.sidebar.header("➕ Add New Event")
with st.sidebar.form("add_event_form"):
    event_name = st.text_input("Event Name *")
    event_time = st.text_input("Time (e.g. 10:00 AM - 11:00 AM)")
    event_hall = st.text_input("Hall / Venue *")
    event_desc = st.text_area("Description")
    submitted = st.form_submit_button("Create Event")
    if submitted:
        if event_name and event_hall:
            event_id = len(st.session_state.events) + 1
            st.session_state.events.append({
                "ID": event_id,
                "Name": event_name,
                "Time": event_time,
                "Hall": event_hall,
                "Description": event_desc,
                "Created": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.session_state.attendees[event_id] = []
            st.sidebar.success(f"✅ Event '{event_name}' created!")
        else:
            st.sidebar.error("⚠️ Please fill required fields")

# ---- MAIN AREA ----
tab1, tab2, tab3 = st.tabs(["📅 Events", "👥 Attendees", "📊 Analytics"])

# --- TAB 1: EVENTS ---
with tab1:
    st.subheader("Scheduled Events")
    if st.session_state.events:
        search = st.text_input("🔍 Search Events", "")
        for event in st.session_state.events:
            if search.lower() in event["Name"].lower():
                with st.container():
                    st.markdown(
                        f"""
                        <div class="event-card">
                            <h4>{event['Name']}</h4>
                            <b>Time:</b> {event['Time']} &nbsp; | &nbsp; 
                            <b>Hall:</b> {event['Hall']} <br>
                            <i>{event['Description']}</i><br>
                            <small>Created on: {event['Created']}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No events yet. Add one from the sidebar!")

# --- TAB 2: ATTENDEES ---
with tab2:
    st.subheader("Event Attendees")
    if st.session_state.events:
        event_choices = {e["Name"]: e["ID"] for e in st.session_state.events}
        selected_event_name = st.selectbox("Select Event", list(event_choices.keys()))
        event_id = event_choices[selected_event_name]

        st.markdown(f"### 👥 {selected_event_name}")
        name = st.text_input("Attendee Name")
        email = st.text_input("Attendee Email")
        if st.button("Register Attendee"):
            if name and email:
                st.session_state.attendees[event_id].append({"Name": name, "Email": email})
                st.success(f"✅ {name} registered!")
            else:
                st.error("⚠️ Enter both name and email")

        if st.session_state.attendees[event_id]:
            st.markdown("#### Registered Attendees")
            for att in st.session_state.attendees[event_id]:
                st.markdown(f"<span class='attendee-badge'>{att['Name']}</span>", unsafe_allow_html=True)
            
            df = pd.DataFrame(st.session_state.attendees[event_id])
            st.download_button("⬇️ Download Attendees CSV", df.to_csv(index=False), file_name="attendees.csv", mime="text/csv")
        else:
            st.info("No attendees yet.")
    else:
        st.warning("Please create an event first!")

# --- TAB 3: ANALYTICS ---
with tab3:
    st.subheader("Event Analytics")
    total_events = len(st.session_state.events)
    total_attendees = sum(len(v) for v in st.session_state.attendees.values())
    col1, col2 = st.columns(2)
    col1.metric("📅 Total Events", total_events)
    col2.metric("👥 Total Attendees", total_attendees)

    if st.session_state.events:
        # Events summary
        df_events = pd.DataFrame(st.session_state.events)
        st.dataframe(df_events, use_container_width=True)
        st.download_button("⬇️ Download Events CSV", df_events.to_csv(index=False), file_name="events.csv", mime="text/csv")
