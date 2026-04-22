import sqlite3
import sys
import tkinter as tk
from datetime import datetime

# This script shows a desktop popup window listing today's medications.
# Run it from the command line like: python reminder.py 1
# The number at the end is the user's ID.

DB_NAME = "eldercare.db"

def get_todays_medications(user_id):
    # Loads all active medications for today from the database
    today = datetime.now().strftime("%Y-%m-%d")
    conn  = sqlite3.connect(DB_NAME)
    c     = conn.cursor()
    c.execute("""SELECT name, dosage, frequency FROM medications
                 WHERE user_id = ? AND start_date <= ? AND end_date >= ?""",
              (user_id, today, today))
    medications = c.fetchall()
    conn.close()
    return medications

def build_popup_window(medications):
    # Creates and shows the Tkinter reminder popup window
    window = tk.Tk()
    window.title("ElderCare Medication Reminder")
    window.geometry("380x320")
    window.configure(bg="#f0f4f8")
    window.attributes("-topmost", True)

    # Title label
    title_label = tk.Label(window, text="Today's Medications",
                           font=("Arial", 16, "bold"), bg="#f0f4f8", fg="#2c3e50")
    title_label.pack(pady=(15, 5))

    # Date label
    date_text = datetime.now().strftime("%A, %B %d %Y")
    date_label = tk.Label(window, text=date_text,
                          font=("Arial", 10), bg="#f0f4f8", fg="#7f8c8d")
    date_label.pack(pady=(0, 10))

    # List of medications
    list_frame = tk.Frame(window, bg="#ffffff", relief="solid", bd=1)
    list_frame.pack(padx=15, fill="both", expand=True)

    if medications:
        for medicine_name, dosage, frequency in medications:
            med_label = tk.Label(list_frame,
                                 text=f"  {medicine_name}  —  {dosage}",
                                 font=("Arial", 11), bg="#ffffff", anchor="w")
            med_label.pack(fill="x", pady=4)

            freq_label = tk.Label(list_frame,
                                  text=f"     Schedule: {frequency}",
                                  font=("Arial", 9), fg="#7f8c8d", bg="#ffffff", anchor="w")
            freq_label.pack(fill="x")
    else:
        no_med_label = tk.Label(list_frame, text="No medications scheduled today.",
                                font=("Arial", 11), bg="#ffffff")
        no_med_label.pack(pady=20)

    # OK button to close the window
    ok_button = tk.Button(window, text="OK — I will take them",
                          font=("Arial", 11, "bold"),
                          bg="#27ae60", fg="white", relief="flat",
                          padx=20, pady=8, command=window.destroy)
    ok_button.pack(pady=15)

    window.mainloop()

if __name__ == "__main__":
    # Get user ID from command line or use default
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        user_id = 1

    medications = get_todays_medications(user_id)
    build_popup_window(medications)
