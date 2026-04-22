import streamlit as st
import database
import numpy as np
import pandas as pd
import charts
import ui_components as ui
from datetime import datetime, timedelta
from collections import Counter
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Import the frequency-to-slots mapping from medications
from medications import FREQUENCY_SLOTS, get_slots

def count_compliance(user_id, date_list):
    # Counts total doses taken and expected over a list of dates
    all_meds  = database.get_medications(user_id)
    total_taken    = 0
    total_expected = 0
    for med in all_meds:
        med_id    = med[0]
        frequency = med[3]
        start_dt  = med[4]
        end_dt    = med[5]
        if frequency == "As Needed":
            continue
        slots = get_slots(frequency)
        for day_str in date_list:
            if start_dt <= day_str <= end_dt:
                day_logs = database.get_medication_logs(user_id, day_str)
                for slot in slots:
                    total_expected = total_expected + 1
                    if day_logs.get((med_id, slot)) == "Taken":
                        total_taken = total_taken + 1
    return total_taken, total_expected

def build_date_list(start_date, num_days):
    # Returns a list of date strings from start_date for num_days days
    date_list = []
    for i in range(num_days):
        day = start_date + timedelta(days=i)
        date_list.append(day.strftime("%Y-%m-%d"))
    return date_list

def show_reports():
    # Main reports page — period selector, PDF button, and weekly/monthly sections
    ui.header("Health Reports")
    if not ui.check_logged_in():
        return
    user_id = st.session_state.user_id
    today   = datetime.now()

    period = st.radio("Select Report Period",
                      ["Weekly (Last 7 Days)", "Monthly (Last 30 Days)"],
                      horizontal=True)

    if "Weekly" in period:
        num_days = 7
        label    = "Weekly"
    else:
        num_days = 30
        label    = "Monthly"

    start_date = today - timedelta(days=num_days)
    st.write(f"Report: **{start_date.strftime('%b %d, %Y')}** to **{today.strftime('%b %d, %Y')}**")
    st.divider()

    # PDF download button
    if st.button("Generate PDF Report (ReportLab)", type="primary"):
        pdf_path = create_pdf_report(user_id, start_date, today, label)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name=f"eldercare_{label}_report.pdf",
                mime="application/pdf"
            )

    st.divider()

    if "Weekly" in period:
        show_weekly_report(user_id, today)
    else:
        show_monthly_report(user_id, today)

def show_weekly_report(user_id, today):
    # Shows health score, adherence heatmap, week comparison, and violin plot
    date_list  = build_date_list(today - timedelta(days=7), 7)
    taken, expected = count_compliance(user_id, date_list)

    if expected > 0:
        score = taken / expected * 100
    else:
        score = 0

    st.metric("Weekly Health Score", f"{score:.1f} / 100")

    # --- Seaborn Heatmap (Medication Adherence) ---
    st.write("### Medication Adherence Heatmap")
    show_heatmap(user_id, date_list)

    # --- Week vs Last Week Comparison (NumPy stats) ---
    st.write("### Week vs Last Week — Vitals Comparison")
    show_week_comparison(user_id, today)

    # --- Seaborn Violin Plot (Vitals Distribution) ---
    st.write("### Vitals Distribution (Last 14 Days)")
    vitals_df = database.get_vitals_df(user_id)
    if not vitals_df.empty:
        cutoff = today - timedelta(days=14)
        df_14  = vitals_df[vitals_df["Timestamp"] >= cutoff]
        if not df_14.empty:
            charts.draw_violin_plot(df_14, ["Systolic", "Diastolic", "Heart Rate"],
                                    "Vitals Distribution")
    # --- CSV Export ---
    show_csv_export(user_id, date_list)

def show_monthly_report(user_id, today):
    # Shows health score, best/worst days, keyword, adherence heatmap
    date_list  = build_date_list(today - timedelta(days=30), 30)
    taken, expected = count_compliance(user_id, date_list)

    if expected > 0:
        score = taken / expected * 100
    else:
        score = 0

    st.metric("Monthly Health Score", f"{score:.1f} / 100")

    # --- Best and Worst Days using Pandas ---
    all_meds = database.get_medications(user_id)
    daily_taken  = {}
    daily_missed = {}

    for day_str in date_list:
        day_logs = database.get_medication_logs(user_id, day_str)
        taken_on_day  = 0
        missed_on_day = 0
        for med in all_meds:
            if med[3] == "As Needed":
                continue
            if med[4] <= day_str <= med[5]:
                for slot in get_slots(med[3]):
                    if day_logs.get((med[0], slot)) == "Taken":
                        taken_on_day  = taken_on_day  + 1
                    else:
                        missed_on_day = missed_on_day + 1
        daily_taken[day_str]  = taken_on_day
        daily_missed[day_str] = missed_on_day

    if daily_taken:
        taken_series  = pd.Series(daily_taken)
        missed_series = pd.Series(daily_missed)
        best_day  = taken_series.idxmax()
        worst_day = missed_series.idxmax()
        col1, col2 = st.columns(2)
        col1.write(f"**Best Day:** {best_day}")
        col2.write(f"**Worst Day:** {worst_day}")

    # --- Most Common Symptom Keyword from Journal ---
    entries = database.get_journal_entries(user_id)
    all_words = []
    for entry in entries:
        entry_date = entry[1]
        entry_text = entry[3]
        if (today - timedelta(days=30)).strftime("%Y-%m-%d") <= entry_date <= today.strftime("%Y-%m-%d"):
            words = entry_text.split()
            for word in words:
                clean_word = word.lower().strip(".,!?")
                if len(clean_word) > 3:
                    all_words.append(clean_word)
    if all_words:
        word_counts = Counter(all_words)
        top_word = word_counts.most_common(1)[0][0]
        st.write(f"**Most Common Symptom Keyword:** {top_word.capitalize()}")

    # --- Seaborn Heatmap ---
    st.write("### Monthly Medication Adherence Heatmap")
    show_heatmap(user_id, date_list)

    # --- CSV Export ---
    show_csv_export(user_id, date_list)

def show_heatmap(user_id, date_list):
    # Builds a 2D grid of compliance data and draws a Seaborn heatmap
    all_meds  = database.get_medications(user_id)
    row_labels = []
    row_data   = []

    for med in all_meds:
        med_id    = med[0]
        med_name  = med[1]
        frequency = med[3]
        start_dt  = med[4]
        end_dt    = med[5]
        if frequency == "As Needed":
            continue
        slots = get_slots(frequency)
        for slot in slots:
            if len(slots) > 1:
                row_key = f"{med_name} ({slot})"
            else:
                row_key = med_name
            row_values = []
            for day_str in date_list:
                if start_dt <= day_str <= end_dt:
                    day_logs = database.get_medication_logs(user_id, day_str)
                    if day_logs.get((med_id, slot)) == "Taken":
                        row_values.append(1)
                    else:
                        row_values.append(0)
                else:
                    row_values.append(float("nan"))
            row_labels.append(row_key)
            row_data.append(row_values)

    if row_data:
        column_labels = [d[-5:] for d in date_list]
        df_heatmap = pd.DataFrame(row_data,
                                  index=row_labels,
                                  columns=column_labels)
        show_numbers = len(date_list) <= 7
        charts.draw_heatmap(df_heatmap, "Medication Adherence", show_numbers)
    else:
        ui.show_info("No compliance data to display.")

def show_week_comparison(user_id, today):
    # Compares this week's and last week's vitals using NumPy averages
    vitals_df = database.get_vitals_df(user_id)
    if vitals_df.empty:
        ui.show_info("No vitals data yet."); return

    this_week_start = today - timedelta(days=7)
    last_week_start = today - timedelta(days=14)

    this_week_df = vitals_df[vitals_df["Timestamp"] >= this_week_start]
    last_week_df = vitals_df[(vitals_df["Timestamp"] >= last_week_start) &
                              (vitals_df["Timestamp"] < this_week_start)]

    metric_names      = []
    this_week_values  = []
    last_week_values  = []

    for col in ["Systolic", "Diastolic", "Heart Rate"]:
        tw_data = this_week_df[col].dropna().values
        lw_data = last_week_df[col].dropna().values
        if len(tw_data) > 0 and len(lw_data) > 0:
            # Use NumPy to calculate averages
            tw_avg = np.mean(tw_data)
            lw_avg = np.mean(lw_data)
            metric_names.append(col)
            this_week_values.append(round(tw_avg, 1))
            last_week_values.append(round(lw_avg, 1))
            # Show as metric card with delta
            delta = round(tw_avg - lw_avg, 1)
            st.metric(col, f"{tw_avg:.1f}", f"{delta:+.1f} vs last week")

    if metric_names:
        charts.draw_comparison_bars(metric_names, this_week_values, last_week_values,
                                    "This Week vs Last Week")

def show_csv_export(user_id, date_list):
    # Exports vitals data as a CSV file for download
    st.write("### Export Data")
    vitals_df = database.get_vitals_df(user_id)
    if not vitals_df.empty:
        csv_data = vitals_df.to_csv(index=False)
        st.download_button(
            label="Download Vitals as CSV",
            data=csv_data,
            file_name="eldercare_vitals.csv",
            mime="text/csv"
        )

def create_pdf_report(user_id, start_date, end_date, label):
    # Generates a PDF report using ReportLab and returns the file path
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc       = SimpleDocTemplate(temp_file.name)
    styles    = getSampleStyleSheet()
    elements  = []

    user = database.get_user_by_id(user_id)

    # Title
    elements.append(Paragraph("ElderCare Companion Health Report", styles["Title"]))
    elements.append(Paragraph(
        f"{label} Report — {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}",
        styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Patient information table
    elements.append(Paragraph("Patient Information", styles["Heading2"]))
    patient_data = [
        ["Name",         user.get("name", "")],
        ["Age",          str(user.get("age", ""))],
        ["Gender",       user.get("gender", "")],
        ["Blood Group",  user.get("blood_group", "")],
        ["Conditions",   user.get("known_conditions", "")],
        ["Allergies",    user.get("allergies", "")],
    ]
    patient_table = Table(patient_data)
    patient_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID",       (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 12))

    # Medication compliance summary
    elements.append(Paragraph("Medication Compliance", styles["Heading2"]))
    num_days  = (end_date - start_date).days + 1
    date_list = build_date_list(start_date, num_days)
    taken, expected = count_compliance(user_id, date_list)
    if expected > 0:
        compliance_pct = f"{taken / expected * 100:.1f}%"
    else:
        compliance_pct = "No data"
    elements.append(Paragraph(f"Overall Compliance: {compliance_pct}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Vitals summary
    elements.append(Paragraph("Vitals Summary", styles["Heading2"]))
    vitals_df = database.get_vitals_df(user_id)
    if not vitals_df.empty:
        vitals_table_data = [["Vital", "Average", "Min", "Max"]]
        for col in ["Systolic", "Diastolic", "Heart Rate", "Weight", "BeforeMeal", "AfterMeal"]:
            data = vitals_df[col].dropna().values
            if len(data) > 0:
                avg_val = np.mean(data)
                min_val = np.min(data)
                max_val = np.max(data)
                vitals_table_data.append([
                    col,
                    f"{avg_val:.1f}",
                    f"{min_val:.1f}",
                    f"{max_val:.1f}"
                ])
        vitals_table = Table(vitals_table_data)
        vitals_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID",       (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(vitals_table)

    doc.build(elements)
    return temp_file.name
