import streamlit as st
import database
import pandas as pd
import ui_components as ui
from datetime import datetime, timedelta

def show_appointments():
    # Main appointments page — add form, upcoming list, past history
    ui.header("Appointment Tracker")
    if not ui.check_logged_in():
        return
    user_id = st.session_state.user_id

    show_add_form(user_id)
    st.divider()
    show_appointments_list(user_id)

def show_add_form(user_id):
    # Form to schedule a new doctor appointment
    with st.expander("Schedule New Appointment"):
        with st.form("add_appt_form"):
            col1, col2 = st.columns(2)
            doctor_name    = col1.text_input("Doctor's Name")
            specialization = col1.text_input("Specialization (e.g. Cardiology)")
            appt_date      = col1.date_input("Date")
            appt_time      = col2.time_input("Time")
            location       = col2.text_input("Clinic / Hospital Location")
            notes          = st.text_area("Notes")
            submitted = st.form_submit_button("Save Appointment")
            if submitted and doctor_name:
                database.add_appointment(
                    user_id, doctor_name, specialization,
                    appt_date.strftime("%Y-%m-%d"),
                    appt_time.strftime("%H:%M"),
                    location, notes
                )
                ui.show_success(f"Appointment with Dr. {doctor_name} saved.")
                st.rerun()

def show_appointments_list(user_id):
    # Loads all appointments and shows upcoming and past in separate sections
    all_rows = database.get_appointments(user_id)
    if not all_rows:
        ui.show_info("No appointments yet. Use the form above to add one.")
        return

    # Use Pandas to organize appointments
    df = pd.DataFrame(all_rows,
                      columns=["ID","Doctor","Specialization","Date","Time","Location","Notes","UserID"])

    today_str  = datetime.now().strftime("%Y-%m-%d")
    soon_str   = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    # Split into upcoming and past
    upcoming_df = df[df["Date"] >= today_str]
    past_df     = df[df["Date"] <  today_str]

    # Show upcoming appointments
    st.subheader("Upcoming Appointments")
    if not upcoming_df.empty:
        # Highlight appointments in the next 2 days
        for index, row in upcoming_df.iterrows():
            if row["Date"] <= soon_str:
                ui.show_warning(f"Reminder: Dr. {row['Doctor']} on {row['Date']} at {row['Time']}")

        display_df = upcoming_df.drop(columns=["ID", "UserID"])
        st.dataframe(display_df, use_container_width=True)

        # Option to cancel an upcoming appointment
        with st.expander("Cancel an Appointment"):
            appt_options = []
            appt_ids     = []
            for index, row in upcoming_df.iterrows():
                appt_options.append(f"Dr. {row['Doctor']} on {row['Date']}")
                appt_ids.append(row["ID"])
            selected_index = st.selectbox("Select appointment to cancel",
                                          range(len(appt_options)),
                                          format_func=lambda i: appt_options[i])
            if st.button("Cancel Selected Appointment"):
                database.delete_appointment(user_id, int(appt_ids[selected_index]))
                st.rerun()
    else:
        ui.show_info("No upcoming appointments.")

    # Show past appointments
    st.divider()
    st.subheader("Past Appointments")
    if not past_df.empty:
        display_past = past_df.drop(columns=["ID", "UserID"])
        st.dataframe(display_past, use_container_width=True)
        if st.button("Clear All Past Records"):
            for appt_id in past_df["ID"]:
                database.delete_appointment(user_id, int(appt_id))
            st.rerun()
    else:
        st.write("No past appointment records.")
