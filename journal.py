import streamlit as st
import database
import pandas as pd
import ui_components as ui

def show_journal():
    # Main journal page — form to add entry, table to view history, option to delete
    ui.header("Symptom Journal")
    if not ui.check_logged_in():
        return
    user_id = st.session_state.user_id

    show_add_entry_form(user_id)
    st.divider()
    show_journal_history(user_id)

def show_add_entry_form(user_id):
    # Form to write and save a new journal entry
    with st.form("journal_form", clear_on_submit=True):
        entry_text = st.text_area("How are you feeling today?", height=150,
                                  help="Describe any symptoms, moods, or side effects.")
        submitted  = st.form_submit_button("Log Entry")
        if submitted:
            if entry_text.strip():
                database.add_journal_entry(user_id, entry_text)
                ui.show_success("Your entry has been saved.")
            else:
                ui.show_warning("Please write something before saving.")

def show_journal_history(user_id):
    # Loads all journal entries and shows them as a Pandas table
    st.subheader("Journal History")
    entries = database.get_journal_entries(user_id)

    if not entries:
        ui.show_info("Your journal is empty. Log your first entry above.")
        return

    # Use Pandas to display the data as a clean table
    df = pd.DataFrame(entries, columns=["ID", "Date", "Time", "Note", "UserID"])
    display_df = df.drop(columns=["ID", "UserID"])
    st.dataframe(display_df, use_container_width=True)

    # Option to delete an entry
    with st.expander("Delete an Entry"):
        entry_options = []
        entry_ids     = []
        for entry in entries:
            label = f"{entry[1]} at {entry[2]}: {entry[3][:40]}..."
            entry_options.append(label)
            entry_ids.append(entry[0])

        selected_index = st.selectbox("Select entry to delete",
                                      range(len(entry_options)),
                                      format_func=lambda i: entry_options[i])
        if st.button("Delete Selected Entry"):
            database.delete_journal_entry(user_id, entry_ids[selected_index])
            ui.show_success("Entry removed.")
            st.rerun()
