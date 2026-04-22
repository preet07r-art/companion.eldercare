import streamlit as st
import database
import numpy as np
import charts
import ui_components as ui
from datetime import datetime, timedelta

def safe_float(value, default=0.0):
    # Converts a value to float, handling 'None' strings and empty values safely
    if value is None or str(value).lower() == 'none' or str(value).strip() == "":
        return float(default)
    try:
        return float(value)
    except:
        return float(default)

def show_bmi(user_id):
    # Calculates BMI using NumPy and shows the colorful gauge
    prof = database.get_user_by_id(user_id)
    h = safe_float(prof.get('height'), 0)
    w = safe_float(prof.get('weight'), 0)
    
    if not (h and w):
        ui.show_info("Update height & weight in User Profile to see BMI."); return
    bmi = round(w / np.square(h / 100), 2)
    c1, c2 = st.columns([1, 2])
    c1.metric("Your BMI", bmi)
    if bmi < 18.5:   c2.warning("Underweight — consult your doctor."); color = "blue"
    elif bmi <= 24.9: c2.success("Normal weight — keep it up!");        color = "green"
    elif bmi <= 29.9: c2.warning("Overweight — consider lifestyle changes."); color = "orange"
    else:             c2.error("Obese — please consult your doctor.");   color = "red"
    
    charts.draw_bmi_gauge(bmi, color)

def show_goals_form(user_id):
    # Lets users define healthy target ranges for each vital
    with st.expander("Set My Vitals Goals"):
        g = database.get_vitals_goals(user_id) or {}
        c1, c2, c3, c4 = st.columns(4)
        sys_min = c1.number_input("Min Systolic",  value=int(safe_float(g.get('bp_systolic_min'), 90)))
        sys_max = c2.number_input("Max Systolic",  value=int(safe_float(g.get('bp_systolic_max'), 120)))
        dia_min = c3.number_input("Min Diastolic", value=int(safe_float(g.get('bp_diastolic_min'), 60)))
        dia_max = c4.number_input("Max Diastolic", value=int(safe_float(g.get('bp_diastolic_max'), 80)))
        s1, s2, h1, h2 = st.columns(4)
        sg_min = s1.number_input("Min Sugar",  value=int(safe_float(g.get('blood_sugar_min'), 70)))
        sg_max = s2.number_input("Max Sugar",  value=int(safe_float(g.get('blood_sugar_max'), 140)))
        hr_min = h1.number_input("Min HR",     value=int(safe_float(g.get('heart_rate_min'), 60)))
        hr_max = h2.number_input("Max HR",     value=int(safe_float(g.get('heart_rate_max'), 100)))
        w1, w2, _, _ = st.columns(4)
        wt_min = w1.number_input("Min Weight", value=safe_float(g.get('weight_min'), 50.0))
        wt_max = w2.number_input("Max Weight", value=safe_float(g.get('weight_max'), 90.0))
        if st.button("Save Goals"):
            database.save_vitals_goals(user_id, {
                'bp_systolic_min': sys_min, 'bp_systolic_max': sys_max,
                'bp_diastolic_min': dia_min, 'bp_diastolic_max': dia_max,
                'blood_sugar_min': sg_min, 'blood_sugar_max': sg_max,
                'heart_rate_min': hr_min, 'heart_rate_max': hr_max,
                'weight_min': wt_min, 'weight_max': wt_max})
            ui.show_success("Goals saved!")

def show_log_form(user_id, goals):
    # Form to log a new vitals reading and check against goals
    with st.expander("Log New Reading"):
        with st.form("vitals_form"):
            c1, c2 = st.columns(2)
            sys_bp = c1.number_input("Systolic BP",   50, 250, 120)
            dia_bp = c2.number_input("Diastolic BP",  30, 150, 80)
            hr     = c1.number_input("Heart Rate",    30, 200, 72)
            wt     = c2.number_input("Weight (kg)",   20.0, 300.0, 70.0, format="%.1f")
            sg_b   = c1.number_input("Blood Sugar Before Meal", value=None, min_value=40, max_value=500)
            sg_a   = c2.number_input("Blood Sugar After Meal",  value=None, min_value=40, max_value=500)
            if st.form_submit_button("Save Entry"):
                database.add_vitals(user_id, sys_bp, dia_bp, sg_b, sg_a, hr, wt)
                ui.show_success("Readings saved!")
                if goals:
                    for name, val, mn_k, mx_k in [
                        ("Systolic BP", sys_bp, 'bp_systolic_min', 'bp_systolic_max'),
                        ("Diastolic BP", dia_bp, 'bp_diastolic_min', 'bp_diastolic_max'),
                        ("Heart Rate", hr, 'heart_rate_min', 'heart_rate_max'),
                        ("Weight", wt, 'weight_min', 'weight_max')]:
                        if not (goals.get(mn_k,0) <= val <= goals.get(mx_k,999)):
                            ui.popup_alert("Vitals Alert", f"{name} ({val}) is outside your goal range.", "warning")
                st.rerun()

def show_charts(df, goals):
    # Blood sugar chart, heart rate chart, goal gauges, stats — all using charts.py
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent = df[df["Timestamp"] >= seven_days_ago].sort_values("Timestamp")

    if goals and not df.empty:
        charts.draw_goal_gauges(df.iloc[0].to_dict(), goals)

    st.subheader("Blood Sugar (7 Days)")
    bs = recent.dropna(subset=["BeforeMeal","AfterMeal"], how="all")
    charts.draw_line_chart(bs["Timestamp"], bs["BeforeMeal"], "Blood Sugar Before Meal", "mg/dL", "blue")
    charts.draw_line_chart(bs["Timestamp"], bs["AfterMeal"],  "Blood Sugar After Meal",  "mg/dL", "red")

    st.subheader("Heart Rate (7 Days)")
    hr_df = recent.dropna(subset=["Heart Rate"])
    import matplotlib.pyplot as plt
    if not hr_df.empty:
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.plot(hr_df["Timestamp"], hr_df["Heart Rate"], color="#e67e22", marker='o', markersize=4)
        if goals:
            ax.axhline(goals.get("heart_rate_min", 60), color='green', linestyle='--', alpha=0.4, label="Min Goal")
            ax.axhline(goals.get("heart_rate_max", 100), color='red',   linestyle='--', alpha=0.4, label="Max Goal")
        ax.legend(fontsize=8); ax.set_ylabel("BPM", fontsize=8)
        plt.xticks(rotation=45, fontsize=8); plt.tight_layout(); st.pyplot(fig); plt.close(fig)

    st.subheader("Monthly Statistics (NumPy)")
    month = datetime.now().strftime("%Y-%m")
    df_month = df[df["Date"].str.startswith(month)]
    for col in ["Systolic","Diastolic","Heart Rate","Weight"]:
        data = df_month[col].dropna().values
        if len(data):
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{col} Avg", f"{np.mean(data):.1f}")
            c2.metric(f"{col} Min", f"{np.min(data):.1f}")
            c3.metric(f"{col} Max", f"{np.max(data):.1f}")

def show_vitals():
    # Main vitals page — BMI, goals, log form, charts, history table
    ui.header("Vital Signs Logger")
    if not ui.check_logged_in(): return
    user_id = st.session_state.user_id

    show_bmi(user_id)
    st.divider()
    show_goals_form(user_id)
    goals = database.get_vitals_goals(user_id) or {}
    show_log_form(user_id, goals)
    st.divider()

    df = database.get_vitals_df(user_id)
    if not df.empty:
        show_charts(df, goals)
        st.divider()
        st.subheader("Full History")
        st.dataframe(df.drop(columns=["ID","UserID","Timestamp"]), use_container_width=True)
    else:
        ui.show_info("No vitals logged yet. Use the form above.")
