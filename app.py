"""
app.py — Flask Backend for Smart Health Reminder Application
"""
import os, json, base64, re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

import database as db
import ai_engine as ai

# ── OCR ──────────────────────────────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ── TTS ──────────────────────────────────────────────────────────────────────
try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# ── SCHEDULER ────────────────────────────────────────────────────────────────
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    scheduler = None

app = Flask(__name__)
app.secret_key = "nexushealth_secret_2024"
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def ok(data=None, **kwargs):
    payload = {"success": True}
    if data is not None: payload["data"] = data
    payload.update(kwargs)
    return jsonify(payload)

def err(msg, code=400):
    return jsonify({"success": False, "error": msg}), code

def current_user_id():
    return session.get("user_id", 1)


# ─── SCHEDULED JOBS ──────────────────────────────────────────────────────────
def check_reminder_compliance():
    users = db.list_users()
    for u in users:
        ai.check_caregiver_alert(u["id"])

def compute_daily_scores():
    users = db.list_users()
    for u in users:
        ai.calculate_health_score(u["id"])


# ─── MAIN PAGE ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html",
        ocr_available=OCR_AVAILABLE,
        tts_available=TTS_AVAILABLE,
        scheduler_available=SCHEDULER_AVAILABLE)


# ─── USER ENDPOINTS ──────────────────────────────────────────────────────────
@app.route("/api/users", methods=["GET"])
def get_users():
    return ok(db.list_users())

@app.route("/api/users", methods=["POST"])
def create_user():
    d = request.json or {}
    required = ["name"]
    for f in required:
        if not d.get(f): return err(f"'{f}' is required")
    data = {
        "name": d["name"].strip(),
        "age": int(d.get("age", 25)),
        "gender": d.get("gender", ""),
        "condition": d.get("condition", "general"),
        "wake_time": d.get("wake_time", "06:30"),
        "sleep_time": d.get("sleep_time", "22:00"),
        "language": d.get("language", "en"),
        "caregiver": d.get("caregiver", "")
    }
    uid = db.create_user(data)
    session["user_id"] = uid
    # Generate initial schedule
    ai.generate_schedule(uid)
    return ok(db.get_user(uid)), 201

@app.route("/api/users/<int:uid>", methods=["GET"])
def get_user(uid):
    u = db.get_user(uid)
    if not u: return err("User not found", 404)
    return ok(u)

@app.route("/api/users/<int:uid>", methods=["PUT"])
def update_user(uid):
    d = request.json or {}
    db.update_user(uid, d)
    return ok(db.get_user(uid))

@app.route("/api/session/<int:uid>", methods=["POST"])
def set_session(uid):
    session["user_id"] = uid
    return ok({"user_id": uid})


# ─── MEDICINES ───────────────────────────────────────────────────────────────
@app.route("/api/medicines", methods=["GET"])
def get_medicines():
    uid = current_user_id()
    return ok(db.get_medicines(uid))

@app.route("/api/medicines", methods=["POST"])
def add_medicine():
    uid = current_user_id()
    d = request.json or {}
    if not d.get("name"): return err("Medicine name required")
    times = d.get("times", ["08:00"])
    if isinstance(times, str): times = [times]
    data = {
        "user_id": uid,
        "name": d["name"].strip(),
        "dosage": d.get("dosage", "1 tablet"),
        "times": json.dumps(times),
        "duration": int(d.get("duration", 7)),
        "priority": d.get("priority", "HIGH"),
        "from_ocr": 0
    }
    mid = db.add_medicine(data)
    # Regenerate schedule
    ai.generate_schedule(uid)
    return ok({"id": mid, **data}), 201

@app.route("/api/medicines/<int:mid>", methods=["DELETE"])
def delete_medicine(mid):
    db.delete_medicine(mid)
    ai.generate_schedule(current_user_id())
    return ok({"deleted": mid})


# ─── REMINDERS ───────────────────────────────────────────────────────────────
@app.route("/api/reminders", methods=["GET"])
def get_reminders():
    uid = current_user_id()
    reminders = db.get_reminders(uid)
    now_time = datetime.now().strftime("%H:%M")
    for r in reminders:
        r["is_due"] = r["scheduled"] <= now_time
    return ok(reminders)

@app.route("/api/reminders/generate", methods=["POST"])
def generate_reminders():
    uid = current_user_id()
    schedule = ai.generate_schedule(uid)
    return ok(schedule)

@app.route("/api/reminders/<int:rid>/action", methods=["POST"])
def reminder_action(rid):
    uid = current_user_id()
    action = (request.json or {}).get("action", "completed")
    reminders = db.get_reminders(uid)
    r = next((x for x in reminders if x["id"] == rid), None)
    if not r: return err("Reminder not found", 404)
    db.log_activity(uid, rid, r["type"], action)
    # Check caregiver
    alert_sent = ai.check_caregiver_alert(uid)
    return ok({"action": action, "caregiver_alerted": alert_sent})


# ─── HYDRATION ───────────────────────────────────────────────────────────────
@app.route("/api/hydration", methods=["GET"])
def get_hydration():
    uid = current_user_id()
    glasses = db.get_hydration_today(uid)
    target = 8
    u = db.get_user(uid)
    if u and u.get("age"):
        group = ai.get_age_group(u["age"])
        target = ai.AGE_RULES[group]["hydration_glasses"]
    return ok({"glasses": glasses, "target": target, "pct": min(round(glasses/target*100), 100)})

@app.route("/api/hydration", methods=["POST"])
def log_hydration():
    uid = current_user_id()
    glasses = int((request.json or {}).get("glasses", 1))
    db.log_hydration(uid, glasses)
    db.log_activity(uid, 0, "water", "completed")
    return ok({"logged": glasses})


# ─── HEALTH SCORE ─────────────────────────────────────────────────────────────
@app.route("/api/health-score", methods=["GET"])
def health_score():
    uid = current_user_id()
    result = ai.calculate_health_score(uid)
    history = db.get_health_scores(uid, 7)
    result["history"] = history
    return ok(result)


# ─── ADAPTIVE LEARNING ───────────────────────────────────────────────────────
@app.route("/api/adaptive", methods=["GET"])
def adaptive_suggestions():
    uid = current_user_id()
    suggestions = ai.run_adaptive_learning(uid)
    return ok(suggestions)

@app.route("/api/adaptive/apply", methods=["POST"])
def apply_suggestion():
    uid = current_user_id()
    d = request.json or {}
    rid = d.get("reminder_id")
    new_time = d.get("suggested_time")
    if rid and new_time:
        db.q("UPDATE reminders SET scheduled=? WHERE id=?", (new_time, rid), commit=True)
    return ok({"applied": True})


# ─── CAREGIVER ALERTS ────────────────────────────────────────────────────────
@app.route("/api/caregiver-alerts", methods=["GET"])
def caregiver_alerts():
    uid = current_user_id()
    alerts = db.get_caregiver_alerts(uid)
    return ok(alerts)


# ─── OCR PRESCRIPTION SCAN ───────────────────────────────────────────────────
@app.route("/api/ocr", methods=["POST"])
def ocr_prescription():
    uid = current_user_id()
    
    # Accept base64 image or file upload
    if request.content_type and "application/json" in request.content_type:
        d = request.json or {}
        img_data = d.get("image_base64", "")
        if img_data.startswith("data:"):
            img_data = img_data.split(",")[1]
        try:
            img_bytes = base64.b64decode(img_data)
        except Exception:
            return err("Invalid base64 image")
        filename = "prescription.jpg"
    elif "file" in request.files:
        f = request.files["file"]
        filename = f.filename
        img_bytes = f.read()
    else:
        return err("No image provided")
    
    # Attempt OCR
    raw_text = ""
    if OCR_AVAILABLE:
        try:
            img = Image.open(io.BytesIO(img_bytes))
            raw_text = pytesseract.image_to_string(img)
        except Exception as e:
            raw_text = f"OCR Error: {str(e)}"
    else:
        # Demo mode: simulate OCR output
        raw_text = """
        Dr. Rajesh Kumar MD
        Patient: John Doe  Date: 2024-01-15
        
        Rx:
        Metformin 500mg - Twice daily (morning, evening) x 30 days
        Aspirin 75mg - Once daily (morning) x 30 days  
        Atorvastatin 10mg - Once at night x 90 days
        Vitamin D3 1000 IU - Once daily (morning) x 60 days
        
        Follow up after 4 weeks.
        """

    # Parse medicines from OCR text
    parsed_meds = ai.parse_prescription_text(raw_text)
    
    # Save prescription
    db.save_prescription(uid, filename, raw_text, json.dumps(parsed_meds))
    
    # Auto-create medicine reminders from parsed
    added = []
    for med in parsed_meds:
        data = {
            "user_id": uid,
            "name": med["name"],
            "dosage": med["dosage"],
            "times": json.dumps(med["times"]),
            "duration": med.get("duration", 7),
            "priority": "HIGH",
            "from_ocr": 1
        }
        mid = db.add_medicine(data)
        added.append({"id": mid, **med})
    
    if added:
        ai.generate_schedule(uid)
    
    return ok({
        "raw_text": raw_text,
        "medicines_found": len(parsed_meds),
        "medicines": parsed_meds,
        "added_to_profile": len(added),
        "ocr_used": OCR_AVAILABLE
    })


# ─── TTS ENDPOINT ────────────────────────────────────────────────────────────
@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    d = request.json or {}
    text = d.get("text", "")
    lang = d.get("lang", "en")
    
    if not text: return err("No text provided")
    
    lang_map = {"en": "en", "kn": "kn", "te": "te", "hi": "hi"}
    gtts_lang = lang_map.get(lang, "en")
    
    if TTS_AVAILABLE:
        try:
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            audio_b64 = base64.b64encode(audio_io.read()).decode()
            return ok({"audio_base64": audio_b64, "format": "mp3"})
        except Exception as e:
            return ok({"error": str(e), "fallback": "web_speech_api"})
    else:
        return ok({"fallback": "web_speech_api", "text": text, "lang": lang})


# ─── DASHBOARD SUMMARY ───────────────────────────────────────────────────────
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    uid = current_user_id()
    user = db.get_user(uid)
    if not user: return ok({})
    
    score_data = ai.calculate_health_score(uid)
    reminders = db.get_reminders(uid)
    logs = db.get_today_logs(uid)
    hydration = db.get_hydration_today(uid)
    
    now = datetime.now().strftime("%H:%M")
    upcoming = [r for r in reminders if r["scheduled"] >= now][:3]
    
    completed_today = sum(1 for l in logs if l["action"] == "completed")
    
    condition_key = ai.get_condition_key(user.get("condition","general"))
    tips = ai.CONDITION_RULES.get(condition_key, ai.CONDITION_RULES["general"])
    
    return ok({
        "user": user,
        "health_score": score_data["score"],
        "grade": score_data.get("grade", ""),
        "breakdown": score_data.get("breakdown", {}),
        "upcoming_reminders": upcoming,
        "total_reminders": len(reminders),
        "completed_today": completed_today,
        "hydration": {"glasses": hydration, "target": 8},
        "health_tips": tips.get("diet", []),
        "exercise_tips": tips.get("exercise", []),
        "condition_alerts": tips.get("alerts", []),
        "adaptive_suggestions": ai.run_adaptive_learning(uid)
    })


# ─── ACTIVITY LOGS ────────────────────────────────────────────────────────────
@app.route("/api/logs", methods=["GET"])
def get_logs():
    uid = current_user_id()
    return ok(db.get_today_logs(uid))


# ─── SYSTEM STATUS ───────────────────────────────────────────────────────────
@app.route("/api/status", methods=["GET"])
def status():
    return ok({
        "ocr": OCR_AVAILABLE,
        "tts": TTS_AVAILABLE,
        "scheduler": SCHEDULER_AVAILABLE,
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    })


# ─── STARTUP ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db.init_db()
    
    if SCHEDULER_AVAILABLE:
        scheduler.add_job(check_reminder_compliance, "interval", hours=1)
        scheduler.add_job(compute_daily_scores, "cron", hour=23, minute=55)
        scheduler.start()
        print("[Scheduler] Running ✓")
    
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║      SMART HEALTH REMINDER APP  —  v2.0          ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print(f"  ║  OCR:       {'✓ Tesseract' if OCR_AVAILABLE else '✗ Install pytesseract + Pillow':<35}║")
    print(f"  ║  TTS:       {'✓ gTTS' if TTS_AVAILABLE else '✗ Install gTTS (Web Speech fallback)':<35}║")
    print(f"  ║  Scheduler: {'✓ APScheduler' if SCHEDULER_AVAILABLE else '✗ Install apscheduler':<35}║")
    print("  ╠══════════════════════════════════════════════════╣")
    print("  ║  → Open  http://localhost:5000                   ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()
    
    app.run(host="0.0.0.0", port=5000, debug=False)
