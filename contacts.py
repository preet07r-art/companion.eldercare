import streamlit as st
import database
import re
import ui_components as ui

def is_valid_phone(phone_number):
    # Returns True if the phone number matches a basic valid format
    pattern = r"^\+?[\d\s\-]{10,15}$"
    return bool(re.match(pattern, phone_number))

def is_valid_email(email_address):
    # Returns True if the email address matches a basic valid format
    if not email_address:
        return True   # Email is optional, so blank is allowed
    pattern = r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    return bool(re.match(pattern, email_address))

def show_contacts():
    # Main contacts page — add form, edit tab, and contact card display
    ui.header("Emergency Contacts")
    if not ui.check_logged_in():
        return
    user_id = st.session_state.user_id

    tab_add, tab_edit = st.tabs(["Add New Contact", "Edit Existing Contact"])

    with tab_add:
        show_add_contact_form(user_id)

    with tab_edit:
        show_edit_contact_form(user_id)

    st.divider()
    show_contact_cards(user_id)

def show_add_contact_form(user_id):
    # Form to add a new emergency contact
    with st.form("add_contact_form", clear_on_submit=True):
        full_name    = st.text_input("Full Name")
        relationship = st.text_input("Relationship (e.g. Daughter, Neighbor)")
        phone        = st.text_input("Phone Number")
        email        = st.text_input("Email Address (optional)")
        notes        = st.text_area("Additional Notes")
        is_pinned    = st.checkbox("Mark as Priority Contact (Pin to Top)")
        submitted    = st.form_submit_button("Save Contact")

        if submitted:
            if not full_name or not phone:
                ui.show_error("Name and phone number are both required.")
            elif not is_valid_phone(phone):
                ui.show_error("Phone number format is invalid. Example: +91 9876543210")
            elif not is_valid_email(email):
                ui.show_error("Email format is invalid.")
            else:
                database.add_contact(user_id, full_name, relationship,
                                     phone, email, notes, is_pinned)
                ui.show_success(f"Contact for {full_name} has been added.")
                st.rerun()

def show_edit_contact_form(user_id):
    # Form to edit an existing contact's details
    all_contacts = database.get_contacts(user_id)
    if not all_contacts:
        ui.show_info("No contacts to edit yet.")
        return

    contact_labels = []
    for contact in all_contacts:
        label = f"{contact[1]} ({contact[2]})"
        contact_labels.append(label)

    selected_index = st.selectbox("Select contact to edit",
                                  range(len(contact_labels)),
                                  format_func=lambda i: contact_labels[i])

    chosen = all_contacts[selected_index]

    with st.form("edit_contact_form"):
        new_name  = st.text_input("Name",         value=chosen[1])
        new_rel   = st.text_input("Relationship", value=chosen[2])
        new_phone = st.text_input("Phone",        value=chosen[3])
        new_email = st.text_input("Email",        value=chosen[4])
        new_notes = st.text_area("Notes",         value=chosen[5])
        new_pin   = st.checkbox("Pinned",         value=bool(chosen[6]))
        submitted = st.form_submit_button("Update Contact")
        if submitted:
            if not is_valid_phone(new_phone):
                ui.show_error("Invalid phone number format.")
            elif not is_valid_email(new_email):
                ui.show_error("Invalid email format.")
            else:
                database.update_contact(user_id, chosen[0], new_name, new_rel,
                                        new_phone, new_email, new_notes, new_pin)
                ui.show_success("Contact updated successfully.")
                st.rerun()

def show_contact_cards(user_id):
    # Shows all contacts as cards in a 2-column grid
    st.subheader("Your Emergency Contacts")
    all_contacts = database.get_contacts(user_id)

    if not all_contacts:
        ui.show_info("No contacts added yet. Use the form above.")
        return

    col1, col2 = st.columns(2)
    for i in range(len(all_contacts)):
        contact = all_contacts[i]

        if i % 2 == 0:
            target_col = col1
        else:
            target_col = col2

        with target_col:
            with st.container(border=True):
                if contact[6]:  # is_pinned flag
                    st.write(f"**{contact[1]}** — Priority Contact")
                else:
                    st.write(f"**{contact[1]}**")
                st.write(f"Relationship: {contact[2]}")
                st.write(f"Phone: {contact[3]}")
                if contact[4]:
                    st.write(f"Email: {contact[4]}")
                if contact[5]:
                    st.caption(f"Note: {contact[5]}")
                if st.button("Delete", key=f"del_contact_{contact[0]}"):
                    database.delete_contact(user_id, contact[0])
                    st.rerun()
