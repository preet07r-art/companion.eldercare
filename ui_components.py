import streamlit as st

# This file contains simple reusable functions for UI and desktop popups.

def show_success(message):
    # Shows a green success message in the browser
    st.success(message)

def show_error(message):
    # Shows a red error message in the browser
    st.error(message)

def show_warning(message):
    # Shows an orange warning message in the browser
    st.warning(message)

def show_info(message):
    # Shows a blue info message in the browser
    st.info(message)

def header(title):
    # Shows a page header
    st.header(title)

def check_logged_in():
    # Returns False and shows error if no user is logged in
    if not st.session_state.get("logged_in"):
        st.error("Please log in to view this page.")
        return False
    return True

def popup_warning(title, message):
    # Opens a native desktop warning popup using Tkinter
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showwarning(title, message, master=root)
        root.destroy()
    except Exception:
        # Fallback for cloud deployment (no display)
        st.warning(f"**{title}**: {message}")

def popup_info(title, message):
    # Opens a native desktop info popup using Tkinter
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo(title, message, master=root)
        root.destroy()
    except Exception:
        # Fallback for cloud deployment (no display)
        st.info(f"**{title}**: {message}")
