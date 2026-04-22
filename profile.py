import streamlit as st
import database
import hashlib
import re
import ui_components as ui
from datetime import datetime, date

def safe_float(value, default=0.0):
    # Converts a value to float, handling 'None' strings and empty values safely
    if value is None or str(value).lower() == 'none' or str(value).strip() == "":
        return float(default)
    try:
        return float(value)
    except:
        return float(default)

def show_profile():
    # Main profile page — loads data and shows all 4 sections
    ui.header("User Profile")
    if not ui.check_logged_in():
        return
    user_id = st.session_state.user_id
    user    = database.get_user_by_id(user_id)
    if user is None:
        ui.show_error("Profile not found.")
        return
    st.write(f"### {user['name']}")
    st.info("Your name cannot be changed after account creation.")

    dob, age, gender                       = show_personal_section(user)
    bg, height, weight, conditions, allergies, surgeries, disabilities, smoking, alcohol, activity = show_medical_section(user)
    ct_name, ct_rel, ct_phone, ct_email, ct_pw = show_caretaker_section(user)
    e_name, e_phone, hospital, ambulance   = show_emergency_section(user)

    show_change_pin_section(user_id)

    st.divider()
    if st.button("Save All Profile Changes", type="primary"):
        save_profile(user_id, user, dob, age, gender, bg, height, weight,
                     conditions, allergies, surgeries, disabilities, smoking, alcohol, activity,
                     ct_name, ct_rel, ct_phone, ct_email, ct_pw,
                     e_name, e_phone, hospital, ambulance)

def show_personal_section(user):
    # Shows personal details — date of birth, calculated age, gender
    with st.expander("Personal Information", expanded=True):
        col1, col2 = st.columns(2)
        if user.get("date_of_birth") and isinstance(user["date_of_birth"], str):
            default_dob = datetime.strptime(user["date_of_birth"], "%Y-%m-%d").date()
        else:
            default_dob = date(1950, 1, 1)
        dob    = col1.date_input("Date of Birth", value=default_dob, min_value=date(1900,1,1))
        today  = date.today()
        age    = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        col1.write(f"**Calculated Age:** {age} years")
        options = ["Male", "Female", "Other"]
        current = user.get("gender", "Male")
        index   = options.index(current) if current in options else 0
        gender  = col2.selectbox("Gender", options, index=index)
    return dob, age, gender

def show_medical_section(user):
    # Shows medical details — blood group, height, weight, conditions, habits
    with st.expander("Medical Information"):
        bg_options = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
        c1, c2, c3 = st.columns(3)
        current_bg = user.get("blood_group", "A+")
        bg_index   = bg_options.index(current_bg) if current_bg in bg_options else 0
        blood_group = c1.selectbox("Blood Group", bg_options, index=bg_index)
        height = c2.number_input("Height (cm)", 0.0, 300.0, safe_float(user.get("height"), 170))
        weight = c3.number_input("Weight (kg)", 0.0, 500.0, safe_float(user.get("weight"), 70))
        conditions   = st.text_area("Known Conditions", value=user.get("known_conditions") or "")
        allergies    = st.text_area("Allergies",        value=user.get("allergies") or "")
        surgeries    = st.text_area("Past Surgeries",   value=user.get("past_surgeries") or "")
        disabilities = st.text_area("Disabilities",     value=user.get("disabilities") or "")
        yn_opts = ["No","Yes","Quit"]
        a1, a2, a3 = st.columns(3)
        s_idx = yn_opts.index(user.get("smoking_habit","No")) if user.get("smoking_habit") in yn_opts else 0
        a_idx = yn_opts.index(user.get("alcohol_habit","No")) if user.get("alcohol_habit") in yn_opts else 0
        smoking  = a1.selectbox("Smoking",  yn_opts, index=s_idx)
        alcohol  = a2.selectbox("Alcohol",  yn_opts, index=a_idx)
        act_opts = ["Sedentary","Light","Moderate"]
        ac_idx = act_opts.index(user.get("activity_level","Sedentary")) if user.get("activity_level") in act_opts else 0
        activity = a3.selectbox("Activity Level", act_opts, index=ac_idx)
    return blood_group, height, weight, conditions, allergies, surgeries, disabilities, smoking, alcohol, activity

def show_caretaker_section(user):
    # Shows caretaker contact details and login password
    with st.expander("Caretaker Information"):
        name  = st.text_input("Caretaker Name",  value=user.get("caretaker_name") or "")
        rel_options = ["Son","Daughter","Spouse","Nurse","Other","Not Applicable"]
        current_rel = user.get("caretaker_relationship", "Not Applicable")
        rel_index   = rel_options.index(current_rel) if current_rel in rel_options else 5
        rel    = st.selectbox("Relationship", rel_options, index=rel_index)
        phone  = st.text_input("Phone Number", value=user.get("caretaker_phone") or "")
        email  = st.text_input("Email Address", value=user.get("caretaker_email") or "")
        pw     = st.text_input("Caretaker Password", type="password",
                               help="Leave blank to keep existing password")
    return name, rel, phone, email, pw

def show_emergency_section(user):
    # Shows emergency contact, nearest hospital, and ambulance number
    with st.expander("Emergency Information"):
        c1, c2 = st.columns(2)
        e_name   = c1.text_input("Emergency Contact Name",  value=user.get("emergency_contact_name") or "")
        e_phone  = c2.text_input("Emergency Contact Phone", value=user.get("emergency_contact_phone") or "")
        hospital  = c1.text_input("Nearest Hospital",  value=user.get("nearest_hospital") or "")
        ambulance = c2.text_input("Ambulance Number",  value=user.get("ambulance_number") or "")
    return e_name, e_phone, hospital, ambulance

def show_change_pin_section(user_id):
    # Lets the user change their login PIN
    with st.expander("Security — Change PIN"):
        current = st.text_input("Current PIN", type="password", max_chars=4)
        new_pin = st.text_input("New PIN",     type="password", max_chars=4)
        confirm = st.text_input("Confirm New", type="password", max_chars=4)
        if st.button("Change PIN"):
            stored_hash = database.get_user_pin(user_id)
            if database.hash_pin(current) != stored_hash:
                ui.show_error("Current PIN is incorrect.")
            elif not new_pin.isdigit() or len(new_pin) != 4:
                ui.show_error("New PIN must be exactly 4 digits.")
            elif new_pin != confirm:
                ui.show_error("New PINs do not match.")
            else:
                database.update_user_pin(user_id, database.hash_pin(new_pin))
                ui.show_success("PIN changed successfully!")

def save_profile(user_id, user, dob, age, gender, blood_group, height, weight,
                 conditions, allergies, surgeries, disabilities, smoking, alcohol, activity,
                 ct_name, ct_rel, ct_phone, ct_email, ct_pw,
                 e_name, e_phone, hospital, ambulance):
    # Validates phone/email using re library, then saves all profile changes
    phone_pattern = r"^\+?[\d\s\-]{7,15}$"
    email_pattern = r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    if ct_phone and not re.match(phone_pattern, ct_phone):
        ui.show_error("Caretaker phone number format is invalid."); return
    if ct_email and not re.match(email_pattern, ct_email):
        ui.show_error("Caretaker email format is invalid."); return
    if e_phone and not re.match(phone_pattern, e_phone):
        ui.show_error("Emergency phone number format is invalid."); return
    if ct_pw:
        pw_hash = hashlib.sha256(ct_pw.encode()).hexdigest()
    else:
        pw_hash = user.get("caretaker_password")
    database.update_user_profile(user_id,
        date_of_birth=dob.strftime("%Y-%m-%d"), age=age, gender=gender,
        blood_group=blood_group, height=height, weight=weight,
        known_conditions=conditions, allergies=allergies, past_surgeries=surgeries,
        disabilities=disabilities, smoking_habit=smoking, alcohol_habit=alcohol,
        activity_level=activity, caretaker_name=ct_name, caretaker_relationship=ct_rel,
        caretaker_phone=ct_phone, caretaker_email=ct_email, caretaker_password=pw_hash,
        emergency_contact_name=e_name, emergency_contact_phone=e_phone,
        nearest_hospital=hospital, ambulance_number=ambulance)
    ui.show_success("Profile saved successfully!")
