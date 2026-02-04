from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import pyttsx3

engine = pyttsx3.init()

def speak_reminder(message):
    engine.say(message)
    engine.runAndWait()

from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize DB
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            age INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            name TEXT,
            dosage TEXT,
            time TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Home
@app.route('/')
def index():
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, age) VALUES (?, ?, ?)",
                      (username, password, age))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists!"
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/dashboard')
        else:
            return "Invalid credentials!"
    return render_template('login.html')

# Dashboard
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    if request.method == 'POST':
        r_type = request.form['type']
        name = request.form['name']
        dosage = request.form['dosage']
        time = request.form['time']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO reminders (user_id, type, name, dosage, time) VALUES (?, ?, ?, ?, ?)",
                  (user_id, r_type, name, dosage, time))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reminders WHERE user_id=?", (user_id,))
    reminders = c.fetchall()
    conn.close()
    return render_template('dashboard.html', reminders=reminders)

# Mark as done
@app.route('/done/<int:reminder_id>')
def mark_done(reminder_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE reminders SET status='done' WHERE id=?", (reminder_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Daily Summary
@app.route('/summary')
def summary():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT type, name, dosage, time, status FROM reminders WHERE user_id=?", (user_id,))
    reminders = c.fetchall()
    conn.close()
    return render_template('summary.html', reminders=reminders)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

from flask import jsonify

# API to send all reminders as JSON
@app.route('/get_reminders')
def get_reminders():
    if 'user_id' not in session:
        return jsonify([])
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, type, name, dosage, time, status FROM reminders WHERE user_id=?", (user_id,))
    reminders = c.fetchall()
    conn.close()
    reminders_list = []
    for r in reminders:
        reminders_list.append({
            'id': r[0],
            'type': r[1],
            'name': r[2],
            'dosage': r[3],
            'time': r[4],
            'status': r[5]
        })
    return jsonify(reminders_list)

# Speak reminder for a specific reminder ID
@app.route('/speak/<int:reminder_id>')
def speak(reminder_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT type, name, dosage FROM reminders WHERE id=?", (reminder_id,))
    r = c.fetchone()
    conn.close()
    if r:
        message = f"It's time for your {r[0]}: {r[1]}, {r[2]}"
        speak_reminder(message)
    return '', 200


if __name__ == '__main__':
    app.run(debug=True)
