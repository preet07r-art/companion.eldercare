# 👨‍🏫 ElderCare Companion: Total Line-by-Line Code Manual

This manual explains **every single line** of your project. It is organized file-by-file. Read this while you have the code open in your editor!

---

## 1. `main.py` (The Receptionist)
This is the entry point. It controls the "Flow" of the entire app.

```python
import streamlit as st
```
*   **Line 1:** Imports the Streamlit library. This is the main engine that turns your Python code into a website.

```python
import database
```
*   **Line 2:** Imports your `database.py`. We need this to talk to the SQLite storage.

```python
import profile, medications, vitals, appointments, journal, reports, contacts
```
*   **Line 3:** Imports all your other page files. Think of these as "Rooms" in the guest house.

```python
import ui_components as ui
```
*   **Line 4:** Imports your helper tools (like headers and alerts) and names them `ui` for easy typing.

```python
st.set_page_config(page_title="ElderCare Companion", layout="wide")
```
*   **Line 5:** Sets the browser tab title and makes the layout "Wide" so it uses the whole screen.

```python
database.migrate_database()
```
*   **Line 6:** Calls the migration function. This ensures the database file and all Excel-like tables are ready before the app starts.

```python
if "logged_in" not in st.session_state: st.session_state.logged_in = False
```
*   **Line 7:** Checks if the app's "Memory" (Session State) has a `logged_in` key. If not, it sets it to `False` (logged out).

```python
def show_sidebar():
    st.sidebar.title("ElderCare")
    selected_page = st.sidebar.radio("Go to", page_options, ...)
    return selected_page
```
*   **Line 1:** Starts a function to draw the sidebar.
*   **Line 2:** Puts the title "ElderCare" on the left.
*   **Line 3:** Creates the list of pages. It returns the name of the page the user clicked on.

```python
def show_dashboard():
    hour = datetime.now().hour
    if hour < 12: greeting = "Good Morning"
```
*   **Line 1:** Starts the Dashboard function.
*   **Line 2:** Looks at the computer's current time.
*   **Line 3:** If the hour is less than 12 (Midnight to 11:59 AM), pick "Good Morning".

```python
subprocess.Popen([sys.executable, "progress_visual.py", "weekly", str(user_id)])
```
*   **Line 1:** Launches the **Turtle** script as a separate process. `sys.executable` finds your Python, and it passes the User ID so the Turtle knows whose data to draw.

---

## 2. `database.py` (The Filing Cabinet)
This is where we talk to SQLite.

```python
import sqlite3
```
*   **Line 1:** Imports the library for the local database file.

```python
DB_NAME = "eldercare.db"
```
*   **Line 2:** Sets the name of your database file. It will appear in your folder.

```python
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)
```
*   **Line 1:** A helper function. It "unlocks" the database file so we can read/write data.

```python
c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ...)""")
```
*   **Line 1:** Tells SQLite to create a "Table" (like an Excel sheet) called `users`.
*   **id**: Each user gets a unique number automatically (1, 2, 3...).
*   **name**: Stores the user's name as text.

```python
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()
```
*   **Line 1:** Encrypts the user's PIN. You give it "1234", it gives back a scrambled code. This is for security!

```python
def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    ...
```
*   **Line 1:** Starts the function to find a specific user's details.
*   **Line 2-3**: Connects to the database and gets a "Cursor" (a pointer to read data).
*   **Line 4:** Asks: "Find the row in the `users` table where the ID matches this number."
*   **Line 5:** Grabs that single row of data.

---

## 3. `medications.py` (The Pill Manager)
This handles medication checklists.

```python
FREQUENCY_SLOTS = { "Once Daily": ["Morning"], "Twice Daily": ["Morning", "Night"] }
```
*   **Line 1:** A "Dictionary" or "Map." It maps a frequency name to a list of times (slots) to take medicine.

```python
active_meds = [m for m in all_meds if m[4] <= today_str <= m[5]]
```
*   **Line 1:** A "Filter." It looks at every medicine and only keeps the ones where today's date is between the Start Date (`m[4]`) and End Date (`m[5]`).

```python
for med in active_meds:
    with st.container(border=True):
        st.write(f"**{med[1]}** — {med[2]}")
```
*   **Line 1:** Loops through every active medicine.
*   **Line 2:** Draws a clean box around this medicine.
*   **Line 3:** Writes the Name (`med[1]`) and Dosage (`med[2]`) in bold.

```python
checkbox = st.checkbox(slot, value=is_taken, key=f"chk_{med_id}_{slot}")
```
*   **Line 1:** Draws a checkmark box for a specific time (like "Morning").
*   **value=is_taken**: If the database says you already took it, the box will already be checked.
*   **key**: A unique ID for Streamlit to track this specific checkbox.

---

## 4. `vitals.py` (The Health Tracker)
Math and analysis for vitals.

```python
def safe_float(value, default=0.0):
    if value is None or str(value).lower() == 'none' or str(value).strip() == "":
        return float(default)
    return float(value)
```
*   **Line 1:** Starts a safety net function.
*   **Line 2-3**: If data is missing or says "none," it returns `0.0`.
*   **Line 4:** Otherwise, it converts the text to a real decimal number (float).

```python
bmi = round(w / np.square(h / 100), 2)
```
*   **Line 1:** **NumPy BMI Math!**
    *   `h / 100`: Turns cm into meters.
    *   `np.square(...)`: Multiplies height by itself.
    *   `w / ...`: Divides weight by that squared height.
    *   `round(..., 2)`: Keeps only 2 decimal places.

---

## 5. `progress_visual.py` (The Turtle Artist)
Drawing with Python.

```python
screen = turtle.Screen()
screen.setup(520, 520)
```
*   **Line 1:** Creates a new window for drawing.
*   **Line 2:** Makes the window 520 by 520 pixels.

```python
t = turtle.Turtle()
t.speed(0) # Fastest speed
```
*   **Line 1:** Creates the "Turtle" (your pen).
*   **Line 2:** Sets the drawing speed to the fastest setting so the chart appears instantly.

```python
t.fillcolor(fill_color)
t.begin_fill()
t.circle(150, 360 / 7)
t.end_fill()
```
*   **Line 1:** Picks the color (Green if taken, Red if missed).
*   **Line 2:** Tells the turtle: "I'm about to draw a shape, please fill it."
*   **Line 3:** Draws 1/7th of a circle with a radius of 150.
*   **Line 4:** Says: "Shape finished, fill it with color now!"

---

## 📂 Other Core Pieces
*   **`reports.py`**: Uses **ReportLab** to create a PDF. It builds a "Story" of your health by adding sections (Paragraphs, Tables) into a list and then "Building" that list into a file.
*   **`reminder.py`**: Uses **Tkinter**. `tk.Tk()` opens a window, and `messagebox.showinfo()` shows the popup alert you see on your desktop.
*   **`charts.py`**: Uses **Matplotlib**. `plt.subplots()` creates the canvas, and `ax.plot()` draws the lines for your heart rate or blood sugar.

---

### 👨‍🎓 How to explain this in your Viva:
If the teacher asks: **"How does the medicine checklist work?"**
You say:
*"In `medications.py`, we loop through the active medicines from the database. For each one, we create an `st.checkbox`. If the user clicks it, it immediately calls a function in `database.py` to save a 'Taken' record for that specific user and time."*
