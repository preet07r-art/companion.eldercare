import streamlit as st
import database
import hashlib
import ui_components as ui

def show_login_page():
    # Shows profile selection buttons and the create/delete user forms
    st.title("ElderCare Companion")
    st.divider()

    users = database.get_all_users()

    if users:
        left_col, center_col, right_col = st.columns([1, 2, 1])
        with center_col:
            st.write("### Select Your Profile")
            col1, col2 = st.columns(2)
            for i in range(len(users)):
                user_id   = users[i][0]
                user_name = users[i][1]
                if database.is_account_locked(user_id):
                    button_label = user_name + " (Locked)"
                else:
                    button_label = user_name
                # Alternate between column 1 and column 2
                if i % 2 == 0:
                    target_col = col1
                else:
                    target_col = col2
                button_clicked = target_col.button(button_label,
                    key=f"select_{user_id}", use_container_width=True)
                if button_clicked:
                    st.session_state.selected_user_id   = user_id
                    st.session_state.selected_user_name = user_name
                    st.session_state.show_pin_screen     = True
                    st.rerun()
    else:
        ui.show_info("No profiles yet. Create one below.")

    st.divider()

    with st.expander("Create New Profile"):
        show_create_user_form()

    if users:
        with st.expander("Manage / Delete Users"):
            show_delete_user_form(users)

def show_create_user_form():
    # Form to create a new user with name and PIN
    with st.form("create_user_form"):
        name    = st.text_input("Full Name")
        pin     = st.text_input("4-digit PIN", type="password", max_chars=4)
        confirm = st.text_input("Confirm PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Create Profile")
        if submitted:
            if not name:
                ui.show_error("Please enter a name.")
            elif not pin.isdigit() or len(pin) != 4:
                ui.show_error("PIN must be exactly 4 digits.")
            elif pin != confirm:
                ui.show_error("PINs do not match.")
            elif database.user_exists(name):
                ui.show_error(f"A user named {name} already exists.")
            else:
                new_id   = database.create_user(name)
                pin_hash = database.hash_pin(pin)
                database.set_user_pin(new_id, pin_hash)
                ui.show_success(f"Profile created for {name}!")

def show_delete_user_form(users):
    # Form to permanently delete a user and all their data
    st.warning("Deleting a user removes all their health data permanently.")
    with st.form("delete_user_form"):
        user_names   = [u[1] for u in users]
        selected_name = st.selectbox("Select user to delete", user_names)
        confirmed    = st.checkbox("I understand this cannot be undone")
        submitted    = st.form_submit_button("Delete User")
        if submitted:
            if not confirmed:
                ui.show_error("Please check the confirmation box first.")
            else:
                for user in users:
                    if user[1] == selected_name:
                        database.delete_user(user[0])
                        st.rerun()

def show_pin_screen():
    # Handles PIN login, account locking, forgot PIN, and first-time setup
    st.title("ElderCare Companion")
    user_id   = st.session_state.selected_user_id
    user_name = st.session_state.selected_user_name
    st.header(f"Welcome, {user_name}")

    stored_pin = database.get_user_pin(user_id)

    # First time — user has no PIN yet
    if stored_pin is None:
        show_first_time_pin_setup(user_id, user_name)
        return

    # Account is locked
    if database.is_account_locked(user_id):
        show_locked_account_screen(user_id)
        return

    # Normal PIN entry
    with st.form("pin_entry_form"):
        entered_pin = st.text_input("Enter your 4-digit PIN",
                                    type="password", max_chars=4)
        login_btn = st.form_submit_button("Login")
        if login_btn:
            entered_hash = database.hash_pin(entered_pin)
            if entered_hash == stored_pin:
                # Correct PIN — log in
                database.reset_pin_attempts(user_id)
                st.session_state.logged_in  = True
                st.session_state.user_id    = user_id
                st.session_state.user_name  = user_name
                st.session_state.show_pin_screen = False
                st.rerun()
            else:
                # Wrong PIN
                database.increment_pin_attempts(user_id)
                attempts = database.get_pin_attempts(user_id)
                remaining = 3 - attempts
                if remaining <= 0:
                    database.lock_user_account(user_id)
                    ui.popup_warning("Account Locked",
                        "Too many wrong attempts. This account is now locked.")
                    st.rerun()
                else:
                    ui.show_error(f"Wrong PIN. {remaining} attempt(s) remaining.")

    if st.button("Back to Profiles"):
        st.session_state.show_pin_screen = False
        st.rerun()

    with st.expander("Forgot PIN? Recover using Caretaker Password"):
        show_forgot_pin_form(user_id)

def show_first_time_pin_setup(user_id, user_name):
    # Shown when a user has no PIN — lets them set one for the first time
    ui.show_warning("Please set a 4-digit PIN for your account.")
    with st.form("setup_pin_form"):
        new_pin     = st.text_input("New PIN",         type="password", max_chars=4)
        confirm_pin = st.text_input("Confirm New PIN", type="password", max_chars=4)
        submitted   = st.form_submit_button("Set PIN and Login")
        if submitted:
            if not new_pin.isdigit() or len(new_pin) != 4:
                ui.show_error("PIN must be exactly 4 digits.")
            elif new_pin != confirm_pin:
                ui.show_error("PINs do not match.")
            else:
                database.set_user_pin(user_id, database.hash_pin(new_pin))
                st.session_state.logged_in  = True
                st.session_state.user_id    = user_id
                st.session_state.user_name  = user_name
                st.session_state.show_pin_screen = False
                st.rerun()
    if st.button("Back"):
        st.session_state.show_pin_screen = False
        st.rerun()

def show_locked_account_screen(user_id):
    # Shown when an account is locked — lets caretaker unlock it
    ui.show_error("This account is locked due to too many wrong PIN attempts.")
    ui.popup_warning("Account Locked", "Use the caretaker password to unlock.")
    with st.expander("Unlock Account with Caretaker Password"):
        caretaker_pw = st.text_input("Caretaker Password", type="password")
        if st.button("Unlock Account"):
            user_data = database.get_user_by_id(user_id)
            stored_pw = user_data.get("caretaker_password", "")
            entered_hash = hashlib.sha256(caretaker_pw.encode()).hexdigest()
            if entered_hash == stored_pw:
                database.unlock_user_account(user_id)
                ui.popup_info("Unlocked", "Account has been unlocked successfully!")
                st.rerun()
            else:
                ui.show_error("Wrong caretaker password.")
    if st.button("Back to Profiles"):
        st.session_state.show_pin_screen = False
        st.rerun()

def show_forgot_pin_form(user_id):
    # Lets user reset their PIN after verifying with caretaker password
    caretaker_pw = st.text_input("Caretaker Password", type="password", key="forgot_pw")
    if st.button("Verify Caretaker Password"):
        user_data    = database.get_user_by_id(user_id)
        stored_pw    = user_data.get("caretaker_password", "")
        entered_hash = hashlib.sha256(caretaker_pw.encode()).hexdigest()
        if entered_hash == stored_pw:
            st.session_state.caretaker_verified = True
        else:
            ui.show_error("Wrong caretaker password.")

    if st.session_state.get("caretaker_verified"):
        with st.form("reset_pin_form"):
            new_pin  = st.text_input("New PIN",     type="password", max_chars=4)
            conf_pin = st.text_input("Confirm PIN", type="password", max_chars=4)
            if st.form_submit_button("Reset PIN"):
                if new_pin.isdigit() and len(new_pin) == 4 and new_pin == conf_pin:
                    database.update_user_pin(user_id, database.hash_pin(new_pin))
                    st.session_state.caretaker_verified = False
                    ui.popup_info("Success", "PIN has been reset. You can now log in.")
                    st.rerun()
                else:
                    ui.show_error("PIN must be 4 digits and both must match.")
