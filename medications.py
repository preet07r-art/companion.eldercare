import streamlit as st
import database
import pandas as pd
import numpy as np
import charts
import ui_components as ui
from datetime import datetime, date, timedelta

# This maps each frequency option to the dose slot names it tracks
FREQUENCY_SLOTS = {
    "Once Daily - Morning":   ["Morning"],
    "Once Daily - Afternoon": ["Afternoon"],
    "Once Daily - Night":     ["Night"],
    "Twice Daily - Morning + Afternoon": ["Morning", "Afternoon"],
    "Twice Daily - Morning + Night":     ["Morning", "Night"],
    "Twice Daily - Afternoon + Night":   ["Afternoon", "Night"],
    "3 Times Daily - Morning + Afternoon + Night": ["Morning", "Afternoon", "Night"],
    "As Needed": [],
}

def get_slots(frequency):
    # Returns the list of dose slots for a given frequency
    return FREQUENCY_SLOTS.get(frequency, ["Default"])

def show_medications():
    # Main medications page — shows checklist, charts, and a form to add/delete
    ui.header("Medication Manager")
    if not ui.check_logged_in():
        return
    user_id   = st.session_state.user_id
    today_str = datetime.now().strftime("%Y-%m-%d")

    show_refill_warnings(user_id)
    show_daily_checklist(user_id, today_str)
    st.divider()
    show_weekly_chart(user_id, today_str)
    st.divider()
    show_monthly_table(user_id, today_str)
    st.divider()
    show_manage_section(user_id)

def show_refill_warnings(user_id):
    # Shows a warning for each medication that expires within 5 days
    expiring_meds = database.get_expiring_soon(user_id, days=5)
    for med in expiring_meds:
        if med[5] and isinstance(med[5], str):
            end_date      = datetime.strptime(med[5], "%Y-%m-%d").date()
        else:
            continue # Skip invalid/missing dates
        days_left     = (end_date - date.today()).days
        if days_left >= 0:
            ui.show_warning(f"Refill needed — {medicine_name} ends in {days_left} day(s).")
        else:
            ui.show_error(f"{medicine_name} has expired. Please see your doctor.")

def show_daily_checklist(user_id, today_str):
    # Shows today's medication checklist — one checkbox per dose slot per medicine
    st.subheader("Today's Medication Checklist")
    all_meds   = database.get_medications(user_id)
    todays_logs = database.get_medication_logs(user_id, today_str)

    # Filter to only active medications for today
    active_meds = []
    for med in all_meds:
        if med[4] <= today_str <= med[5]:
            active_meds.append(med)

    if not active_meds:
        ui.show_info("No active medications for today.")
        return

    for med in active_meds:
        med_id   = med[0]
        med_name = med[1]
        dosage   = med[2]
        freq     = med[3]
        image    = med[6]
        slots    = get_slots(freq)

        with st.container(border=True):
            img_col, txt_col = st.columns([1, 4])
            with img_col:
                if image:
                    st.image(image, width=60)
                else:
                    st.write("💊")
            with txt_col:
                st.write(f"**{med_name}** — {dosage}")
                st.caption(f"Schedule: {freq}")

            if not slots:
                st.caption("Take as needed — no fixed slots to track.")
                continue

            slot_columns = st.columns(len(slots))
            for i in range(len(slots)):
                slot = slots[i]
                with slot_columns[i]:
                    log_key    = (med_id, slot)
                    is_taken   = todays_logs.get(log_key) == "Taken"
                    checkbox   = st.checkbox(slot, value=is_taken,
                                             key=f"chk_{med_id}_{slot}")
                    if checkbox and not is_taken:
                        database.log_medication(user_id, med_id, today_str, "Taken", slot)
                        st.rerun()
                    elif not checkbox and is_taken:
                        database.log_medication(user_id, med_id, today_str, "Missed", slot)
                        st.rerun()

def show_weekly_chart(user_id, today_str):
    # Builds 7-day compliance data and draws a bar chart using Matplotlib
    st.subheader("Weekly Progress Chart")
    today   = datetime.now()
    labels  = []
    taken_values  = []
    missed_values = []

    for i in range(6, -1, -1):
        day       = today - timedelta(days=i)
        date_str  = day.strftime("%Y-%m-%d")
        day_logs  = database.get_medication_logs(user_id, date_str)
        all_meds  = database.get_medications(user_id)
        taken  = 0
        missed = 0
        for med in all_meds:
            freq = med[3]
            if freq == "As Needed":
                continue
            if med[4] <= date_str <= med[5]:
                for slot in get_slots(freq):
                    status = day_logs.get((med[0], slot))
                    if status == "Taken":
                        taken = taken + 1
                    else:
                        missed = missed + 1
        labels.append(date_str[-5:])
        taken_values.append(taken)
        missed_values.append(missed)

    charts.draw_bar_chart(labels, taken_values, missed_values, "Dose Compliance — Last 7 Days")

def show_monthly_table(user_id, today_str):
    # Builds monthly compliance data and shows it as a Pandas table
    st.subheader("Monthly Compliance Report")
    today      = datetime.now()
    first_day  = date(today.year, today.month, 1)
    month_days = []
    current_day = first_day
    while current_day <= today.date():
        month_days.append(current_day.strftime("%Y-%m-%d"))
        current_day = current_day + timedelta(days=1)

    all_meds     = database.get_medications(user_id)
    compliance   = {}

    for day_str in month_days:
        day_logs = database.get_medication_logs(user_id, day_str)
        for med in all_meds:
            freq = med[3]
            if freq == "As Needed":
                continue
            if med[4] <= day_str <= med[5]:
                for slot in get_slots(freq):
                    # Key for this row: medicine name + slot name
                    row_key = f"{med[1]} ({slot})"
                    if row_key not in compliance:
                        compliance[row_key] = {"Taken": 0, "Missed": 0, "Total": 0}
                    compliance[row_key]["Total"] = compliance[row_key]["Total"] + 1
                    if day_logs.get((med[0], slot)) == "Taken":
                        compliance[row_key]["Taken"] = compliance[row_key]["Taken"] + 1
                    else:
                        compliance[row_key]["Missed"] = compliance[row_key]["Missed"] + 1

    if compliance:
        # Use Pandas to display data as a table
        df = pd.DataFrame.from_dict(compliance, orient="index")
        # Use NumPy to calculate compliance percentage
        df["Compliance %"] = np.round(df["Taken"] / df["Total"] * 100, 1)
        st.dataframe(df[["Taken", "Missed", "Total", "Compliance %"]], use_container_width=True)
    else:
        ui.show_info("No compliance data for this month yet.")

def show_manage_section(user_id):
    # Shows form to add a new medication and a form to delete one
    all_meds = database.get_medications(user_id)

    with st.expander("Add New Medication"):
        with st.form("add_med_form"):
            med_name  = st.text_input("Medicine Name")
            dosage    = st.text_input("Dosage (e.g. 500mg, 1 tablet)")
            frequency = st.selectbox("Frequency", list(FREQUENCY_SLOTS.keys()))
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Start Date", date.today())
            end_date   = col2.date_input("End Date", date.today() + timedelta(days=30))
            photo      = st.file_uploader("Medicine Photo (optional)", type=["jpg","png","jpeg"])
            slots      = get_slots(frequency)
            if slots:
                st.caption(f"This will track {len(slots)} slot(s): {', '.join(slots)}")
            else:
                st.caption("As Needed — no dose tracking.")
            submitted = st.form_submit_button("Save Medication")
            if submitted and med_name:
                image_data = photo.read() if photo else None
                database.add_medication(
                    user_id, med_name, dosage, frequency,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    image_data
                )
                ui.show_success(f"{med_name} has been added.")
                st.rerun()

    if all_meds:
        with st.form("delete_med_form"):
            options = []
            for med in all_meds:
                label = f"{med[1]} ({med[2]})"
                options.append(label)
            selected_label = st.selectbox("Select medication to delete", options)
            if st.form_submit_button("Delete"):
                for med in all_meds:
                    label = f"{med[1]} ({med[2]})"
                    if label == selected_label:
                        database.delete_medication(user_id, med[0])
                        ui.show_success("Medication deleted.")
                        st.rerun()
