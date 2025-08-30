from flask import Flask, render_template_string, request, redirect
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Database init
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS announcements (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 message TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS schedule (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT,
                 time TEXT,
                 hall TEXT)""")
    conn.commit()
    conn.close()

init_db()

# Templates
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Admin Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    h1 { color: #444; }
    form { margin-bottom: 20px; }
    input, textarea { padding: 8px; margin: 5px; width: 300px; }
    button { padding: 10px; }
  </style>
</head>
<body>
  <h1>📊 Admin Dashboard</h1>

  <h2>Add Announcement</h2>
  <form method="POST" action="/add_announcement">
    <textarea name="message" placeholder="Type announcement..." required></textarea><br>
    <button type="submit">Add</button>
  </form>

  <h2>Add Schedule</h2>
  <form method="POST" action="/add_schedule">
    <input name="title" placeholder="Event Title" required><br>
    <input name="time" placeholder="Time (e.g. 10:00 AM)" required><br>
    <input name="hall" placeholder="Hall/Location" required><br>
    <button type="submit">Add</button>
  </form>

  <h2>📢 Announcements</h2>
  <ul>
    {% for a in announcements %}
      <li>{{a[1]}} ({{a[2]}})</li>
    {% endfor %}
  </ul>

  <h2>📅 Schedule</h2>
  <ul>
    {% for s in schedule %}
      <li>{{s[1]}} at {{s[2]}} in {{s[3]}}</li>
    {% endfor %}
  </ul>
</body>
</html>
"""

@app.route("/")
def dashboard():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM announcements ORDER BY created_at DESC")
    announcements = c.fetchall()
    c.execute("SELECT * FROM schedule ORDER BY time ASC")
    schedule = c.fetchall()
    conn.close()
    return render_template_string(TEMPLATE, announcements=announcements, schedule=schedule)

@app.route("/add_announcement", methods=["POST"])
def add_announcement():
    msg = request.form["message"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO announcements (message) VALUES (?)", (msg,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/add_schedule", methods=["POST"])
def add_schedule():
    title, time, hall = request.form["title"], request.form["time"], request.form["hall"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO schedule (title, time, hall) VALUES (?, ?, ?)", (title, time, hall))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
