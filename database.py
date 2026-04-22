import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta

DB_NAME = "eldercare.db"

def get_connection():
    # Returns a connection to the SQLite database
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def create_tables():
    # Creates all database tables if they do not exist yet
    conn = get_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
        date_of_birth TEXT, age INTEGER, gender TEXT, blood_group TEXT,
        height REAL, weight REAL, known_conditions TEXT, allergies TEXT,
        past_surgeries TEXT, disabilities TEXT, smoking_habit TEXT,
        alcohol_habit TEXT, activity_level TEXT, caretaker_name TEXT,
        caretaker_relationship TEXT, caretaker_phone TEXT, caretaker_email TEXT,
        caretaker_password TEXT, emergency_contact_name TEXT,
        emergency_contact_phone TEXT, nearest_hospital TEXT, ambulance_number TEXT,
        pin TEXT, pin_attempts INTEGER DEFAULT 0, is_locked INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS medications
        (id INTEGER PRIMARY KEY, name TEXT, dosage TEXT, frequency TEXT,
        start_date TEXT, end_date TEXT, image BLOB, user_id INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS medication_logs
        (id INTEGER PRIMARY KEY, medication_id INTEGER, date TEXT,
        status TEXT, slot TEXT DEFAULT 'Default', user_id INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS vitals
        (id INTEGER PRIMARY KEY, date TEXT, time TEXT, bp_systolic INTEGER,
        bp_diastolic INTEGER, blood_sugar REAL, heart_rate INTEGER, weight REAL,
        user_id INTEGER, blood_sugar_before_meal REAL, blood_sugar_after_meal REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS vitals_goals
        (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE,
        bp_systolic_min INTEGER, bp_systolic_max INTEGER,
        bp_diastolic_min INTEGER, bp_diastolic_max INTEGER,
        blood_sugar_min INTEGER, blood_sugar_max INTEGER,
        heart_rate_min INTEGER, heart_rate_max INTEGER,
        weight_min REAL, weight_max REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS appointments
        (id INTEGER PRIMARY KEY, doctor_name TEXT, specialization TEXT,
        date TEXT, time TEXT, location TEXT, notes TEXT, user_id INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS journal
        (id INTEGER PRIMARY KEY, date TEXT, time TEXT, entry TEXT, user_id INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts
        (id INTEGER PRIMARY KEY, name TEXT, relationship TEXT, phone TEXT,
        email TEXT, notes TEXT, is_pinned INTEGER, user_id INTEGER)""")
    conn.commit()
    conn.close()

def migrate_database():
    # Creates tables and adds any missing columns for older databases
    create_tables()
    conn = get_connection()
    c = conn.cursor()
    # List of columns to add if they are missing
    new_columns = [
        ("vitals", "blood_sugar_before_meal", "REAL"),
        ("vitals", "blood_sugar_after_meal", "REAL"),
        ("users", "pin", "TEXT"),
        ("users", "pin_attempts", "INTEGER DEFAULT 0"),
        ("users", "is_locked", "INTEGER DEFAULT 0"),
        ("users", "height", "REAL"),
        ("users", "weight", "REAL"),
    ]
    for table, column, col_type in new_columns:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception:
            pass  # Column already exists
    conn.commit()
    conn.close()

# --- USER FUNCTIONS ---

def get_all_users():
    # Returns list of all users as (id, name)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM users")
    users = c.fetchall()
    conn.close()
    return users

def create_user(name):
    # Creates a new user and returns their new ID
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def get_user_by_id(user_id):
    # Returns a user's data as a dictionary
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    column_names = ["id","name","date_of_birth","age","gender","blood_group",
        "height","weight","known_conditions","allergies","past_surgeries",
        "disabilities","smoking_habit","alcohol_habit","activity_level",
        "caretaker_name","caretaker_relationship","caretaker_phone","caretaker_email",
        "caretaker_password","emergency_contact_name","emergency_contact_phone",
        "nearest_hospital","ambulance_number","pin","pin_attempts","is_locked"]
    return dict(zip(column_names, row))

def update_user_profile(user_id, **fields):
    # Updates any profile fields passed as keyword arguments
    if not fields:
        return
    set_clause = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values())
    values.append(user_id)
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_user(user_id):
    # Deletes a user and all their data from every table
    tables = ["medications","medication_logs","vitals",
              "vitals_goals","appointments","journal","contacts"]
    conn = get_connection()
    c = conn.cursor()
    for table in tables:
        c.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def user_exists(name):
    # Returns True if a user with this name already exists
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE name = ?", (name,))
    result = c.fetchone()
    conn.close()
    return result is not None

# --- SECURITY FUNCTIONS ---

def hash_pin(pin):
    # Converts a PIN into a secure hash so it is never stored as plain text
    return hashlib.sha256(pin.encode()).hexdigest()

def get_user_pin(user_id):
    # Returns the stored PIN hash for this user
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT pin FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_user_pin(user_id, pin_hash):
    # Saves a new PIN hash and resets failed attempts
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET pin = ?, pin_attempts = 0, is_locked = 0 WHERE id = ?",
              (pin_hash, user_id))
    conn.commit()
    conn.close()

def update_user_pin(user_id, pin_hash):
    # Updates the user's PIN hash
    set_user_pin(user_id, pin_hash)

def get_pin_attempts(user_id):
    # Returns the number of failed login attempts for this user
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT pin_attempts FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def increment_pin_attempts(user_id):
    # Adds 1 to the failed attempt counter
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET pin_attempts = pin_attempts + 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def reset_pin_attempts(user_id):
    # Resets failed attempt counter to 0 after a successful login
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET pin_attempts = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def lock_user_account(user_id):
    # Locks the account so no more login attempts are allowed
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET is_locked = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def unlock_user_account(user_id):
    # Unlocks the account and clears failed attempt counter
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET is_locked = 0, pin_attempts = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_account_locked(user_id):
    # Returns True if this account is currently locked
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT is_locked FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return bool(row[0]) if row else False

# --- MEDICATION FUNCTIONS ---

def get_medications(user_id):
    # Returns all medications for this user
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medications WHERE user_id = ?", (user_id,))
    meds = c.fetchall()
    conn.close()
    return meds

def get_active_medications(user_id):
    # Returns only medications active today (within start and end date)
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medications WHERE user_id = ? AND start_date <= ? AND end_date >= ?",
              (user_id, today, today))
    meds = c.fetchall()
    conn.close()
    return meds

def add_medication(user_id, name, dosage, frequency, start_date, end_date, image=None):
    # Saves a new medication to the database
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO medications
        (name, dosage, frequency, start_date, end_date, image, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, dosage, frequency, start_date, end_date, image, user_id))
    conn.commit()
    conn.close()

def delete_medication(user_id, med_id):
    # Deletes a medication and all its dose logs
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM medications WHERE id = ? AND user_id = ?", (med_id, user_id))
    c.execute("DELETE FROM medication_logs WHERE medication_id = ? AND user_id = ?", (med_id, user_id))
    conn.commit()
    conn.close()

def get_expiring_soon(user_id, days=5):
    # Returns medications that expire within the next N days
    today = datetime.now().strftime("%Y-%m-%d")
    soon  = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medications WHERE user_id = ? AND end_date >= ? AND end_date <= ?",
              (user_id, today, soon))
    meds = c.fetchall()
    conn.close()
    return meds

# --- MEDICATION LOG FUNCTIONS ---

def get_medication_logs(user_id, date_str):
    # Returns a dictionary: {(medication_id, slot): status} for this date
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT medication_id, slot, status FROM medication_logs WHERE user_id = ? AND date = ?",
              (user_id, date_str))
    rows = c.fetchall()
    conn.close()
    logs = {}
    for row in rows:
        med_id = row[0]
        slot   = row[1]
        status = row[2]
        logs[(med_id, slot)] = status
    return logs

def log_medication(user_id, med_id, date_str, status, slot):
    # Saves or updates a medication dose status for a specific slot and date
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT id FROM medication_logs
                 WHERE user_id = ? AND medication_id = ? AND date = ? AND slot = ?""",
              (user_id, med_id, date_str, slot))
    existing = c.fetchone()
    if existing:
        c.execute("UPDATE medication_logs SET status = ? WHERE id = ?", (status, existing[0]))
    else:
        c.execute("""INSERT INTO medication_logs (medication_id, date, status, slot, user_id)
                     VALUES (?, ?, ?, ?, ?)""", (med_id, date_str, status, slot, user_id))
    conn.commit()
    conn.close()

# --- VITALS FUNCTIONS ---

def add_vitals(user_id, systolic, diastolic, sugar_before, sugar_after, heart_rate, weight):
    # Saves a new vitals reading with current date and time
    today = datetime.now().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M")
    conn  = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO vitals
        (date, time, bp_systolic, bp_diastolic, blood_sugar, heart_rate, weight,
         user_id, blood_sugar_before_meal, blood_sugar_after_meal)
        VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)""",
        (today, now, systolic, diastolic, heart_rate, weight, user_id, sugar_before, sugar_after))
    conn.commit()
    conn.close()

def get_vitals(user_id):
    # Returns all vitals for this user, newest first
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM vitals WHERE user_id = ? ORDER BY date DESC, time DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_vitals_df(user_id):
    # Returns vitals as a Pandas DataFrame with correct column names
    conn = get_connection()
    query = "SELECT * FROM vitals WHERE user_id = ? ORDER BY date DESC, time DESC"
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    if df.empty:
        return df
    df.columns = ["ID","Date","Time","Systolic","Diastolic","LegacySugar",
                  "Heart Rate","Weight","UserID","BeforeMeal","AfterMeal"]
    df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    return df

# --- VITALS GOALS FUNCTIONS ---

def get_vitals_goals(user_id):
    # Returns the saved health goal ranges for this user as a dictionary
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM vitals_goals WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return {}
    keys = ["id","user_id","bp_systolic_min","bp_systolic_max",
            "bp_diastolic_min","bp_diastolic_max","blood_sugar_min","blood_sugar_max",
            "heart_rate_min","heart_rate_max","weight_min","weight_max"]
    return dict(zip(keys, row))

def save_vitals_goals(user_id, goals):
    # Saves or updates the health goal ranges for this user
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM vitals_goals WHERE user_id = ?", (user_id,))
    existing = c.fetchone()
    if existing:
        c.execute("""UPDATE vitals_goals SET
            bp_systolic_min=?, bp_systolic_max=?, bp_diastolic_min=?, bp_diastolic_max=?,
            blood_sugar_min=?, blood_sugar_max=?, heart_rate_min=?, heart_rate_max=?,
            weight_min=?, weight_max=? WHERE user_id=?""",
            (goals['bp_systolic_min'], goals['bp_systolic_max'],
             goals['bp_diastolic_min'], goals['bp_diastolic_max'],
             goals['blood_sugar_min'], goals['blood_sugar_max'],
             goals['heart_rate_min'], goals['heart_rate_max'],
             goals['weight_min'], goals['weight_max'], user_id))
    else:
        c.execute("""INSERT INTO vitals_goals
            (user_id, bp_systolic_min, bp_systolic_max, bp_diastolic_min, bp_diastolic_max,
             blood_sugar_min, blood_sugar_max, heart_rate_min, heart_rate_max, weight_min, weight_max)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, goals['bp_systolic_min'], goals['bp_systolic_max'],
             goals['bp_diastolic_min'], goals['bp_diastolic_max'],
             goals['blood_sugar_min'], goals['blood_sugar_max'],
             goals['heart_rate_min'], goals['heart_rate_max'],
             goals['weight_min'], goals['weight_max']))
    conn.commit()
    conn.close()

# --- APPOINTMENT FUNCTIONS ---

def get_appointments(user_id):
    # Returns all appointments sorted by date
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM appointments WHERE user_id = ? ORDER BY date ASC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_appointment(user_id, doctor, specialization, date, time, location, notes):
    # Saves a new appointment to the database
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO appointments
        (doctor_name, specialization, date, time, location, notes, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (doctor, specialization, date, time, location, notes, user_id))
    conn.commit()
    conn.close()

def delete_appointment(user_id, appt_id):
    # Deletes an appointment by ID
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM appointments WHERE id = ? AND user_id = ?", (appt_id, user_id))
    conn.commit()
    conn.close()

# --- JOURNAL FUNCTIONS ---

def get_journal_entries(user_id):
    # Returns all journal entries, newest first
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY date DESC, time DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_journal_entry(user_id, entry_text):
    # Saves a new journal entry with today's date and time
    today = datetime.now().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M")
    conn  = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO journal (date, time, entry, user_id) VALUES (?, ?, ?, ?)",
              (today, now, entry_text, user_id))
    conn.commit()
    conn.close()

def delete_journal_entry(user_id, entry_id):
    # Deletes a journal entry by ID
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM journal WHERE id = ? AND user_id = ?", (entry_id, user_id))
    conn.commit()
    conn.close()

# --- CONTACT FUNCTIONS ---

def get_contacts(user_id):
    # Returns all contacts — pinned ones appear first
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM contacts WHERE user_id = ? ORDER BY is_pinned DESC, name ASC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_contact(user_id, name, relationship, phone, email, notes, is_pinned):
    # Saves a new emergency contact
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO contacts (name, relationship, phone, email, notes, is_pinned, user_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (name, relationship, phone, email, notes, int(is_pinned), user_id))
    conn.commit()
    conn.close()

def update_contact(user_id, contact_id, name, relationship, phone, email, notes, is_pinned):
    # Updates an existing contact's details
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE contacts SET name=?, relationship=?, phone=?, email=?,
                 notes=?, is_pinned=? WHERE id=? AND user_id=?""",
              (name, relationship, phone, email, notes, int(is_pinned), contact_id, user_id))
    conn.commit()
    conn.close()

def delete_contact(user_id, contact_id):
    # Deletes a contact by ID
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM contacts WHERE id = ? AND user_id = ?", (contact_id, user_id))
    conn.commit()
    conn.close()
