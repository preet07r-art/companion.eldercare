import streamlit as st
import database
from login import show_login_page, show_pin_screen
import ui_components as ui
import profile, medications, vitals, appointments, journal, reports, contacts
import subprocess
import sys
from datetime import datetime

# Set up the browser page settings
st.set_page_config(page_title="ElderCare Companion", layout="wide")

# Start the database — create tables if they do not exist
database.migrate_database()

# Set default values in session state if not already set
if "logged_in"           not in st.session_state: st.session_state.logged_in           = False
if "user_id"             not in st.session_state: st.session_state.user_id             = None
if "user_name"           not in st.session_state: st.session_state.user_name           = None
if "selected_user_id"    not in st.session_state: st.session_state.selected_user_id    = None
if "selected_user_name"  not in st.session_state: st.session_state.selected_user_name  = None
if "show_pin_screen"     not in st.session_state: st.session_state.show_pin_screen     = False
if "current_page"        not in st.session_state: st.session_state.current_page        = "Home Dashboard"
if "caretaker_verified"  not in st.session_state: st.session_state.caretaker_verified  = False

def show_sidebar():
    # Shows the navigation sidebar and returns the selected page name
    st.sidebar.title("ElderCare")
    st.sidebar.markdown(f"**User:** {st.session_state.user_name}")

    if st.sidebar.button("Switch User / Logout"):
        st.session_state.logged_in          = False
        st.session_state.user_id            = None
        st.session_state.user_name          = None
        st.session_state.selected_user_id   = None
        st.session_state.selected_user_name = None
        st.session_state.show_pin_screen    = False
        st.rerun()

    st.sidebar.divider()

    page_options = [
        "Home Dashboard",
        "User Profile",
        "Medication Manager",
        "Vital Signs Logger",
        "Appointment Tracker",
        "Symptom Journal",
        "Health Reports",
        "Emergency Contacts",
    ]

    selected_page = st.sidebar.radio("Go to", page_options,
        index=page_options.index(st.session_state.current_page))

    st.session_state.current_page = selected_page
    return selected_page

def show_dashboard():
    # Shows the home dashboard with greeting, summary cards, and Turtle/Tkinter buttons
    user_id = st.session_state.user_id
    user    = database.get_user_by_id(user_id)

    # Greeting based on time of day
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
    elif hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    st.header(f"{greeting}, {user.get('name', 'User')}!")
    st.subheader(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
    st.write("")

    # Summary cards row
    card1, card2, card3 = st.columns(3)

    # Card 1: Pending medication doses today
    with card1:
        active_meds = database.get_active_medications(user_id)
        today_str   = datetime.now().strftime("%Y-%m-%d")
        logs        = database.get_medication_logs(user_id, today_str)
        total_slots = 0
        taken_count = 0
        for med in active_meds:
            freq  = med[3]
            slots = medications.FREQUENCY_SLOTS.get(freq, [])
            for slot in slots:
                total_slots = total_slots + 1
                if logs.get((med[0], slot)) == "Taken":
                    taken_count = taken_count + 1
        pending = total_slots - taken_count
        st.metric("Pending Doses", pending, f"{total_slots} total today", delta_color="inverse")

    # Card 2: Latest blood pressure and heart rate
    with card2:
        all_vitals = database.get_vitals(user_id)
        if all_vitals:
            latest = all_vitals[0]
            bp_reading = f"{latest[3]}/{latest[4]}"
            heart_rate = f"{latest[6]} bpm"
            st.metric("Latest BP", bp_reading, heart_rate)
        else:
            st.metric("Vitals", "No Data", "Log a reading")

    # Card 3: Next upcoming appointment
    with card3:
        all_appts = database.get_appointments(user_id)
        today_str = datetime.now().strftime("%Y-%m-%d")
        upcoming = []
        for a in all_appts:
            if a[3] and isinstance(a[3], str) and a[3] >= today_str:
                upcoming.append(a)
        
        if upcoming:
            next_appt = upcoming[0]
            appt_date = datetime.strptime(next_appt[3], "%Y-%m-%d")
            days_away = (appt_date - datetime.now()).days + 1
            st.metric("Next Appointment", f"Dr. {next_appt[1]}", f"In {days_away} day(s)")
        else:
            st.metric("Appointments", "None Scheduled", "All clear")

    st.divider()

    # Visual motivation buttons
    st.write("### Daily Visual Motivation")
    btn1, btn2, btn3 = st.columns(3)

    if btn1.button("Weekly Progress (Turtle Pie Chart)"):
        try:
            subprocess.Popen([sys.executable, "progress_visual.py", "weekly", str(user_id)])
        except Exception:
            st.error("Desktop graphics (Turtle) are not available on this server.")

    if btn2.button("Monthly Calendar (Turtle Grid)"):
        try:
            subprocess.Popen([sys.executable, "progress_visual.py", "monthly", str(user_id)])
        except Exception:
            st.error("Desktop graphics (Turtle) are not available on this server.")

    if btn3.button("Today's Reminder (Tkinter Popup)"):
        try:
            subprocess.Popen([sys.executable, "reminder.py", str(user_id)])
        except Exception:
            st.error("Desktop popups (Tkinter) are not available on this server.")

    st.divider()

    # User profile summary
    st.write("### Profile Summary")
    col1, col2, col3 = st.columns(3)
    col1.write(f"**Age:** {user.get('age', '—')} | **Gender:** {user.get('gender', '—')}")
    col2.write(f"**Blood Group:** {user.get('blood_group', '—')} | **Caretaker:** {user.get('caretaker_name', '—')}")
    col3.write(f"**Conditions:** {user.get('known_conditions', '—')}")

def route_to_page(page_name):
    # Calls the correct page function based on the selected page name
    if page_name == "Home Dashboard":
        show_dashboard()
    elif page_name == "User Profile":
        profile.show_profile()
    elif page_name == "Medication Manager":
        medications.show_medications()
    elif page_name == "Vital Signs Logger":
        vitals.show_vitals()
    elif page_name == "Appointment Tracker":
        appointments.show_appointments()
    elif page_name == "Symptom Journal":
        journal.show_journal()
    elif page_name == "Health Reports":
        reports.show_reports()
    elif page_name == "Emergency Contacts":
        contacts.show_contacts()

# --- App Entry Point ---
# Decide which screen to show based on login state

if not st.session_state.logged_in:
    if st.session_state.show_pin_screen:
        show_pin_screen()
    else:
        show_login_page()
else:
    selected_page = show_sidebar()
    route_to_page(selected_page)
