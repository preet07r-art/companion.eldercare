import turtle
import sqlite3
import sys
from datetime import datetime, timedelta

# This script draws a weekly health progress graphic using Python Turtle.
# Run it like: python progress_visual.py weekly 1
# The number at the end is the user ID.

DB_NAME = "eldercare.db"

FREQUENCY_SLOTS = {
    "Once Daily - Morning":   ["Morning"],
    "Once Daily - Afternoon": ["Afternoon"],
    "Once Daily - Night":     ["Night"],
    "Twice Daily - Morning + Afternoon": ["Morning", "Afternoon"],
    "Twice Daily - Morning + Night":     ["Morning", "Night"],
    "Twice Daily - Afternoon + Night":   ["Afternoon", "Night"],
    "3 Times Daily - Morning + Afternoon + Night": ["Morning", "Afternoon", "Night"],
    "As Needed": [],
}

def load_data(user_id):
    # Loads medications and dose logs from the database
    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()
    c.execute("SELECT id, frequency, start_date, end_date FROM medications WHERE user_id = ?", (user_id,))
    medications = c.fetchall()
    c.execute("SELECT medication_id, date, slot, status FROM medication_logs WHERE user_id = ?", (user_id,))
    log_rows = c.fetchall()
    conn.close()
    logs = {}
    for med_id, date, slot, status in log_rows:
        logs[(med_id, date, slot)] = status
    return medications, logs

def get_day_compliance(medications, logs, date_str):
    # Counts how many doses were taken vs how many were expected on this date
    taken    = 0
    expected = 0
    for med_id, frequency, start_date, end_date in medications:
        if start_date <= date_str <= end_date:
            slots = FREQUENCY_SLOTS.get(frequency, [])
            for slot in slots:
                expected = expected + 1
                if logs.get((med_id, date_str, slot)) == "Taken":
                    taken = taken + 1
    return taken, expected

def draw_weekly_chart(user_id):
    # Draws a 7-segment circle — one segment per day, green if doses taken
    medications, logs = load_data(user_id)

    screen = turtle.Screen()
    screen.setup(520, 520)
    screen.title("Weekly Health Progress")
    screen.bgcolor("#f9f9f9")

    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()

    today = datetime.now()
    total_taken    = 0
    total_expected = 0

    for i in range(7):
        day_offset = 6 - i
        day = today - timedelta(days=day_offset)
        date_str = day.strftime("%Y-%m-%d")
        taken, expected = get_day_compliance(medications, logs, date_str)

        total_taken    = total_taken    + taken
        total_expected = total_expected + expected

        # Choose color based on compliance
        if expected == 0:
            fill_color = "#bdc3c7"   # grey — no medicines
        elif taken == expected:
            fill_color = "#2ecc71"   # green — all taken
        elif taken > 0:
            fill_color = "#f1c40f"   # yellow — partial
        else:
            fill_color = "#e74c3c"   # red — all missed

        # Draw one pie slice for this day
        t.penup()
        t.goto(0, 0)
        t.setheading(360 / 7 * i)
        t.forward(150)
        t.fillcolor(fill_color)
        t.begin_fill()
        t.goto(0, 0)
        t.setheading(360 / 7 * i)
        t.forward(150)
        t.left(90)
        t.circle(150, 360 / 7)
        t.goto(0, 0)
        t.end_fill()

    # Calculate overall score
    if total_expected > 0:
        score = int(total_taken / total_expected * 100)
    else:
        score = 0

    # Draw white circle in the middle for the score
    t.penup()
    t.goto(0, -90)
    t.fillcolor("white")
    t.begin_fill()
    t.circle(90)
    t.end_fill()

    # Write score in center
    t.goto(0, -15)
    t.color("#2c3e50")
    t.write(f"{score}%", align="center", font=("Arial", 28, "bold"))
    t.goto(0, -35)
    t.write("Weekly Score", align="center", font=("Arial", 11, "normal"))

    # Write motivational message below
    if score >= 90:
        message = "Excellent! You are doing great!"
    elif score >= 70:
        message = "Good job! Keep up the effort."
    else:
        message = "Keep going — consistency is key!"

    t.goto(0, -230)
    t.write(message, align="center", font=("Arial", 12, "italic"))

    t.goto(0, -260)
    t.color("gray")
    t.write("Click anywhere to close", align="center", font=("Arial", 9, "normal"))

    screen.exitonclick()

def draw_monthly_grid(user_id):
    # Draws a 30-day calendar grid — one box per day, colored by compliance
    medications, logs = load_data(user_id)

    screen = turtle.Screen()
    screen.setup(700, 560)
    screen.title("Monthly Adherence Calendar")
    screen.bgcolor("#ffffff")

    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()

    today     = datetime.now()
    columns   = 6
    cell_w    = 100
    cell_h    = 78
    start_x   = -(columns * cell_w) / 2
    start_y   = (5 * cell_h) / 2 - 10

    for i in range(30):
        day_offset = 29 - i
        day      = today - timedelta(days=day_offset)
        date_str = day.strftime("%Y-%m-%d")

        taken, expected = get_day_compliance(medications, logs, date_str)

        # Choose fill color for this cell
        if expected == 0:
            fill_color = "#ecf0f1"   # light grey
        elif taken == expected:
            fill_color = "#27ae60"   # dark green
        elif taken > 0:
            fill_color = "#2ecc71"   # light green
        else:
            fill_color = "#e74c3c"   # red

        col = i % columns
        row = i // columns
        x = start_x + (col * cell_w)
        y = start_y - (row * cell_h)

        # Draw the cell rectangle
        t.penup()
        t.goto(x, y)
        t.pendown()
        t.fillcolor(fill_color)
        t.begin_fill()
        for _ in range(4):
            t.forward(cell_w - 4)
            t.right(90)
        t.end_fill()

        # Write the date inside the cell
        t.penup()
        t.goto(x + 5, y - 18)
        t.color("#2c3e50")
        t.write(date_str[-5:], font=("Arial", 8, "normal"))

        # Write taken/expected count
        if expected > 0:
            t.goto(x + cell_w / 2, y - 50)
            t.write(f"{taken}/{expected}", align="center", font=("Arial", 9, "bold"))

    # Title at top
    t.penup()
    t.goto(0, start_y + 38)
    t.color("#2c3e50")
    t.write("Monthly Adherence Calendar", align="center", font=("Arial", 18, "bold"))

    t.goto(0, -280)
    t.color("gray")
    t.write("Click anywhere to close", align="center", font=("Arial", 9, "normal"))

    screen.exitonclick()

if __name__ == "__main__":
    mode    = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    if mode == "weekly":
        draw_weekly_chart(user_id)
    elif mode == "monthly":
        draw_monthly_grid(user_id)
