"""
database.py — SQLite Layer for Smart Health Reminder App
"""
import sqlite3, os, json
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "health.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, age INTEGER, gender TEXT,
        condition TEXT, wake_time TEXT DEFAULT '06:30',
        sleep_time TEXT DEFAULT '22:00', language TEXT DEFAULT 'en',
        caregiver TEXT, created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        name TEXT NOT NULL, dosage TEXT, times TEXT,
        duration INTEGER, priority TEXT DEFAULT 'HIGH',
        active INTEGER DEFAULT 1, from_ocr INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        type TEXT NOT NULL, title TEXT NOT NULL, body TEXT,
        scheduled TEXT NOT NULL, priority TEXT DEFAULT 'MEDIUM',
        active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        reminder_id INTEGER, type TEXT, action TEXT,
        logged_at TEXT DEFAULT (datetime('now')),
        date TEXT DEFAULT (date('now'))
    );
    CREATE TABLE IF NOT EXISTS health_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        score REAL, date TEXT DEFAULT (date('now')), breakdown TEXT,
        UNIQUE(user_id, date)
    );
    CREATE TABLE IF NOT EXISTS caregiver_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        message TEXT, sent_at TEXT DEFAULT (datetime('now')), resolved INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        filename TEXT, raw_text TEXT, parsed TEXT,
        uploaded_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS hydration_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        glasses INTEGER DEFAULT 0, date TEXT DEFAULT (date('now'))
    );
    """)
    conn.commit(); conn.close()

def q(sql, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_conn(); c = conn.cursor(); c.execute(sql, params)
    result = None
    if fetchone: result = c.fetchone(); result = dict(result) if result else None
    elif fetchall: result = [dict(r) for r in c.fetchall()]
    if commit: conn.commit()
    if not fetchone and not fetchall: result = c.lastrowid
    conn.close(); return result

# Users
def create_user(d): return q("INSERT INTO users (name,age,gender,condition,wake_time,sleep_time,language,caregiver) VALUES (:name,:age,:gender,:condition,:wake_time,:sleep_time,:language,:caregiver)", d, commit=True)
def get_user(uid): return q("SELECT * FROM users WHERE id=?", (uid,), fetchone=True)
def update_user(uid, d):
    fields=", ".join(f"{k}=:{k}" for k in d); d["uid"]=uid
    q(f"UPDATE users SET {fields} WHERE id=:uid", d, commit=True)
def list_users(): return q("SELECT * FROM users ORDER BY id", fetchall=True)

# Medicines
def add_medicine(d): return q("INSERT INTO medicines (user_id,name,dosage,times,duration,priority,from_ocr) VALUES (:user_id,:name,:dosage,:times,:duration,:priority,:from_ocr)", d, commit=True)
def get_medicines(uid): return q("SELECT * FROM medicines WHERE user_id=? AND active=1 ORDER BY id", (uid,), fetchall=True)
def delete_medicine(mid): q("UPDATE medicines SET active=0 WHERE id=?", (mid,), commit=True)

# Reminders
def add_reminder(d): return q("INSERT INTO reminders (user_id,type,title,body,scheduled,priority) VALUES (:user_id,:type,:title,:body,:scheduled,:priority)", d, commit=True)
def get_reminders(uid): return q("SELECT * FROM reminders WHERE user_id=? AND active=1 ORDER BY scheduled", (uid,), fetchall=True)
def delete_reminder(rid): q("UPDATE reminders SET active=0 WHERE id=?", (rid,), commit=True)

# Activity
def log_activity(uid, rid, rtype, action): q("INSERT INTO activity_logs (user_id,reminder_id,type,action) VALUES (?,?,?,?)", (uid,rid,rtype,action), commit=True)
def get_today_logs(uid): return q("SELECT * FROM activity_logs WHERE user_id=? AND date=date('now') ORDER BY logged_at DESC", (uid,), fetchall=True)
def get_skipped_count(uid, rid, days=7):
    r=q("SELECT COUNT(*) as cnt FROM activity_logs WHERE user_id=? AND reminder_id=? AND action='skipped' AND logged_at>=datetime('now',?)",(uid,rid,f"-{days} days"),fetchone=True)
    return r["cnt"] if r else 0

# Health Score
def save_health_score(uid, score, breakdown): q("INSERT OR REPLACE INTO health_scores (user_id,score,date,breakdown) VALUES (?,?,date('now'),?)",(uid,score,json.dumps(breakdown)),commit=True)
def get_health_scores(uid, days=7): return q("SELECT * FROM health_scores WHERE user_id=? ORDER BY date DESC LIMIT ?",(uid,days),fetchall=True)

# Hydration
def log_hydration(uid, glasses):
    ex=q("SELECT id,glasses FROM hydration_logs WHERE user_id=? AND date=date('now')",(uid,),fetchone=True)
    if ex: q("UPDATE hydration_logs SET glasses=? WHERE id=?",(ex["glasses"]+glasses,ex["id"]),commit=True)
    else: q("INSERT INTO hydration_logs (user_id,glasses) VALUES (?,?)",(uid,glasses),commit=True)
def get_hydration_today(uid):
    r=q("SELECT glasses FROM hydration_logs WHERE user_id=? AND date=date('now')",(uid,),fetchone=True)
    return r["glasses"] if r else 0

# Caregiver
def create_caregiver_alert(uid, msg): return q("INSERT INTO caregiver_alerts (user_id,message) VALUES (?,?)",(uid,msg),commit=True)
def get_caregiver_alerts(uid): return q("SELECT * FROM caregiver_alerts WHERE user_id=? ORDER BY sent_at DESC LIMIT 20",(uid,),fetchall=True)

# Prescriptions
def save_prescription(uid, filename, raw_text, parsed): return q("INSERT INTO prescriptions (user_id,filename,raw_text,parsed) VALUES (?,?,?,?)",(uid,filename,raw_text,parsed),commit=True)
