"""
ai_engine.py — Rule-Based AI + Adaptive Learning Engine
Smart Health Reminder Application
"""
import json
from datetime import datetime, timedelta
from database import (get_user, get_medicines, get_today_logs, get_skipped_count,
                       add_reminder, get_reminders, delete_reminder, save_health_score,
                       log_activity, get_hydration_today, create_caregiver_alert)


# ─── HEALTH CONDITION RULES ─────────────────────────────────────────────────
CONDITION_RULES = {
    "diabetes": {
        "exercise": ["30-min brisk walking", "Light yoga", "Post-meal 10-min walk"],
        "diet": ["Avoid sugar & refined carbs", "Eat every 3-4 hrs", "High-fiber foods"],
        "alerts": ["Monitor blood sugar before meals", "Carry glucose tablets"],
        "priority": "HIGH"
    },
    "blood pressure": {
        "exercise": ["30-min walking", "Breathing exercises", "Swimming"],
        "diet": ["Low-sodium diet", "DASH diet foods", "Reduce caffeine"],
        "alerts": ["Measure BP morning & evening", "Avoid stress"],
        "priority": "HIGH"
    },
    "heart disease": {
        "exercise": ["Low-intensity walking", "Gentle stretching", "Supervised cardio"],
        "diet": ["Heart-healthy omega-3 foods", "Low-fat diet", "No trans fats"],
        "alerts": ["Keep nitroglycerin handy", "Avoid heavy lifting"],
        "priority": "HIGH"
    },
    "asthma": {
        "exercise": ["Swimming", "Light indoor yoga", "Avoid cold-air running"],
        "diet": ["Anti-inflammatory foods", "Avoid food allergens", "Stay hydrated"],
        "alerts": ["Carry inhaler always", "Avoid smoke & dust"],
        "priority": "HIGH"
    },
    "thyroid": {
        "exercise": ["Cardio 30 mins daily", "Strength training 3x/week"],
        "diet": ["Iodine-rich foods", "Avoid soy excess", "Selenium-rich foods"],
        "alerts": ["Take medicine on empty stomach", "Regular TSH tests"],
        "priority": "HIGH"
    },
    "obesity": {
        "exercise": ["45-min cardio daily", "Strength training", "Swimming"],
        "diet": ["Calorie deficit diet", "High protein meals", "No late-night eating"],
        "alerts": ["Track daily calorie intake", "Weigh in weekly"],
        "priority": "MEDIUM"
    },
    "anxiety": {
        "exercise": ["Yoga & meditation", "Nature walks", "Deep breathing"],
        "diet": ["Reduce caffeine", "Magnesium-rich foods", "Balanced meals"],
        "alerts": ["Practice mindfulness daily", "Maintain sleep schedule"],
        "priority": "MEDIUM"
    },
    "general": {
        "exercise": ["30-min moderate exercise", "Stretching"],
        "diet": ["Balanced nutrition", "Plenty of vegetables"],
        "alerts": ["Stay hydrated", "Regular health checkups"],
        "priority": "LOW"
    }
}

AGE_RULES = {
    "young": {"exercise_intensity": "HIGH", "hydration_glasses": 10, "sleep_hours": 8},
    "adult": {"exercise_intensity": "MEDIUM", "hydration_glasses": 8, "sleep_hours": 7},
    "senior": {"exercise_intensity": "LOW", "hydration_glasses": 7, "sleep_hours": 8}
}

MULTILANG = {
    "en": {
        "medicine": "Time to take your {name} ({dosage}). Please take it now!",
        "water": "Stay hydrated! Drink a glass of water now. 💧",
        "exercise": "Time for your exercise: {activity}. Keep moving! 🏃",
        "meal": "Meal time reminder: {meal}. Eat healthy! 🥗",
        "sleep": "It's time to sleep. Good night! Rest well. 🌙",
        "wake": "Good morning! Start your healthy day. ☀️"
    },
    "kn": {
        "medicine": "ನಿಮ್ಮ {name} ({dosage}) ತೆಗೆದುಕೊಳ್ಳುವ ಸಮಯ ಆಗಿದೆ. ದಯಮಾಡಿ ಈಗ ತೆಗೆದುಕೊಳ್ಳಿ!",
        "water": "ನೀರು ಕುಡಿಯಿರಿ! ಒಂದು ಗ್ಲಾಸ್ ನೀರು ಕುಡಿಯಿರಿ. 💧",
        "exercise": "ವ್ಯಾಯಾಮ ಸಮಯ: {activity}. ಚಲಿಸುತ್ತಾ ಇರಿ! 🏃",
        "meal": "ಊಟದ ಸಮಯ: {meal}. ಆರೋಗ್ಯಕರ ಊಟ ಮಾಡಿ! 🥗",
        "sleep": "ಮಲಗುವ ಸಮಯ ಆಯಿತು. ಶುಭ ರಾತ್ರಿ! 🌙",
        "wake": "ಶುಭೋದಯ! ಆರೋಗ್ಯಕರ ದಿನ ಪ್ರಾರಂಭಿಸಿ. ☀️"
    },
    "te": {
        "medicine": "మీ {name} ({dosage}) తీసుకోవాల్సిన సమయం. దయచేసి ఇప్పుడు తీసుకోండి!",
        "water": "నీరు తాగండి! ఒక గ్లాసు నీరు తాగండి. 💧",
        "exercise": "వ్యాయామ సమయం: {activity}. కదులుతూ ఉండండి! 🏃",
        "meal": "భోజన సమయం: {meal}. ఆరోగ్యకరంగా తినండి! 🥗",
        "sleep": "నిద్రపోయే సమయమైంది. శుభ రాత్రి! 🌙",
        "wake": "శుభోదయం! ఆరోగ్యకరమైన రోజు ప్రారంభించండి. ☀️"
    },
    "hi": {
        "medicine": "आपकी {name} ({dosage}) लेने का समय हो गया। अभी लें!",
        "water": "पानी पियें! एक गिलास पानी पियें। 💧",
        "exercise": "व्यायाम का समय: {activity}. चलते रहें! 🏃",
        "meal": "भोजन का समय: {meal}. स्वस्थ खाएं! 🥗",
        "sleep": "सोने का समय हो गया। शुभ रात्रि! 🌙",
        "wake": "सुप्रभात! स्वस्थ दिन की शुरुआत करें। ☀️"
    }
}


def get_age_group(age):
    if age < 30: return "young"
    if age < 60: return "adult"
    return "senior"


def get_condition_key(condition: str) -> str:
    if not condition: return "general"
    condition = condition.lower()
    for key in CONDITION_RULES:
        if key in condition:
            return key
    return "general"


def get_voice_message(lang: str, msg_type: str, **kwargs) -> str:
    lang = lang if lang in MULTILANG else "en"
    template = MULTILANG[lang].get(msg_type, MULTILANG["en"].get(msg_type, ""))
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


# ─── SCHEDULE GENERATOR ─────────────────────────────────────────────────────
def generate_schedule(user_id: int) -> list:
    """Generate a personalized daily schedule for the user."""
    user = get_user(user_id)
    if not user: return []
    
    medicines = get_medicines(user_id)
    lang = user.get("language", "en")
    age = user.get("age", 30) or 30
    condition = user.get("condition", "general") or "general"
    wake = user.get("wake_time", "06:30") or "06:30"
    sleep_t = user.get("sleep_time", "22:00") or "22:00"
    condition_key = get_condition_key(condition)
    rules = CONDITION_RULES.get(condition_key, CONDITION_RULES["general"])
    age_group = get_age_group(age)
    hydration = AGE_RULES[age_group]["hydration_glasses"]

    # Delete old reminders
    existing = get_reminders(user_id)
    for r in existing:
        delete_reminder(r["id"])

    schedule = []

    # Wake-up reminder
    schedule.append({
        "user_id": user_id, "type": "wake",
        "title": "Good Morning! 🌅",
        "body": get_voice_message(lang, "wake"),
        "scheduled": wake, "priority": "HIGH"
    })

    # Parse wake time
    wh, wm = map(int, wake.split(":"))
    base = datetime.now().replace(hour=wh, minute=wm, second=0, microsecond=0)

    # Morning medicine (+15 min after wake)
    for med in medicines:
        times = json.loads(med.get("times", '["08:00"]') or '["08:00"]')
        for t in times:
            msg = get_voice_message(lang, "medicine", name=med["name"], dosage=med.get("dosage","1 tablet"))
            schedule.append({
                "user_id": user_id, "type": "medicine",
                "title": f"💊 Medicine: {med['name']}",
                "body": msg, "scheduled": t, "priority": "HIGH"
            })

    # Breakfast (+1hr after wake)
    bf_time = (base + timedelta(hours=1)).strftime("%H:%M")
    schedule.append({
        "user_id": user_id, "type": "meal",
        "title": "🥗 Breakfast Time",
        "body": get_voice_message(lang, "meal", meal="Breakfast - " + (rules["diet"][0] if rules["diet"] else "Healthy breakfast")),
        "scheduled": bf_time, "priority": "HIGH"
    })

    # Hydration reminders (every 2 hrs from 8am to 8pm)
    hydration_times = ["08:00","10:00","12:00","14:00","16:00","18:00","20:00"]
    for ht in hydration_times[:min(hydration, 7)]:
        schedule.append({
            "user_id": user_id, "type": "water",
            "title": "💧 Hydration Check",
            "body": get_voice_message(lang, "water"),
            "scheduled": ht, "priority": "LOW"
        })

    # Exercise
    ex_time = (base + timedelta(hours=2)).strftime("%H:%M")
    ex_activity = rules["exercise"][0] if rules["exercise"] else "30-min walk"
    schedule.append({
        "user_id": user_id, "type": "exercise",
        "title": f"🏃 Exercise Time",
        "body": get_voice_message(lang, "exercise", activity=ex_activity),
        "scheduled": ex_time, "priority": "MEDIUM"
    })

    # Lunch
    schedule.append({
        "user_id": user_id, "type": "meal",
        "title": "🍱 Lunch Time",
        "body": get_voice_message(lang, "meal", meal="Lunch - " + (rules["diet"][1] if len(rules["diet"])>1 else "Balanced lunch")),
        "scheduled": "13:00", "priority": "MEDIUM"
    })

    # Evening exercise
    schedule.append({
        "user_id": user_id, "type": "exercise",
        "title": "🧘 Evening Activity",
        "body": get_voice_message(lang, "exercise", activity=rules["exercise"][-1] if rules["exercise"] else "Evening walk"),
        "scheduled": "17:00", "priority": "MEDIUM"
    })

    # Dinner
    schedule.append({
        "user_id": user_id, "type": "meal",
        "title": "🍽️ Dinner Time",
        "body": get_voice_message(lang, "meal", meal="Dinner - Light & healthy meal"),
        "scheduled": "19:30", "priority": "MEDIUM"
    })

    # Health alerts from condition
    for i, alert in enumerate(rules["alerts"][:2]):
        schedule.append({
            "user_id": user_id, "type": "health_tip",
            "title": f"💡 Health Tip",
            "body": alert, "scheduled": f"{9+i*4:02d}:00", "priority": "LOW"
        })

    # Sleep reminder
    sh, sm = map(int, sleep_t.split(":"))
    prep_sleep = datetime.now().replace(hour=sh, minute=sm).replace(minute=max(0, sm-30))
    schedule.append({
        "user_id": user_id, "type": "sleep",
        "title": "🌙 Sleep Reminder",
        "body": get_voice_message(lang, "sleep"),
        "scheduled": prep_sleep.strftime("%H:%M"), "priority": "MEDIUM"
    })

    # Remove duplicates by scheduled time
    seen = set()
    unique = []
    for item in sorted(schedule, key=lambda x: x["scheduled"]):
        key = (item["scheduled"], item["type"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # Save to DB
    for item in unique:
        add_reminder(item)

    return unique


# ─── HEALTH SCORE CALCULATOR ─────────────────────────────────────────────────
def calculate_health_score(user_id: int) -> dict:
    logs = get_today_logs(user_id)
    reminders = get_reminders(user_id)
    hydration = get_hydration_today(user_id)
    
    total = len(reminders)
    if total == 0:
        return {"score": 0, "grade": "N/A", "breakdown": {}}

    completed = sum(1 for l in logs if l["action"] == "completed")
    skipped   = sum(1 for l in logs if l["action"] == "skipped")
    snoozed   = sum(1 for l in logs if l["action"] == "snoozed")

    # Component scores (out of 100)
    compliance = (completed / max(total, 1)) * 100
    hydration_score = min((hydration / 8) * 100, 100)
    
    med_logs = [l for l in logs if l["type"] == "medicine"]
    med_completed = sum(1 for l in med_logs if l["action"] == "completed")
    med_total = sum(1 for r in reminders if r["type"] == "medicine")
    med_score = (med_completed / max(med_total, 1)) * 100 if med_total > 0 else 100

    # Weighted final score
    score = (compliance * 0.4 + hydration_score * 0.2 + med_score * 0.4)
    score = round(min(score, 100), 1)

    grade = "Excellent 🌟" if score >= 80 else \
            "Good 👍" if score >= 60 else \
            "Needs Improvement ⚠️" if score >= 40 else "Risk Alert 🚨"

    breakdown = {
        "compliance_pct": round(compliance, 1),
        "hydration_glasses": hydration,
        "hydration_score": round(hydration_score, 1),
        "medicine_score": round(med_score, 1),
        "completed": completed, "skipped": skipped, "snoozed": snoozed,
        "total_reminders": total
    }
    save_health_score(user_id, score, breakdown)
    return {"score": score, "grade": grade, "breakdown": breakdown}


# ─── ADAPTIVE LEARNING ───────────────────────────────────────────────────────
def run_adaptive_learning(user_id: int) -> list:
    """Check skipped reminders and suggest time adjustments."""
    reminders = get_reminders(user_id)
    suggestions = []
    
    for r in reminders:
        skipped = get_skipped_count(user_id, r["id"], days=7)
        if skipped >= 3:
            # Suggest shifting time by +30min
            try:
                h, m = map(int, r["scheduled"].split(":"))
                new_m = m + 30
                new_h = h + new_m // 60
                new_m = new_m % 60
                new_time = f"{new_h:02d}:{new_m:02d}"
                suggestions.append({
                    "reminder_id": r["id"],
                    "title": r["title"],
                    "current_time": r["scheduled"],
                    "suggested_time": new_time,
                    "reason": f"Skipped {skipped} times in last 7 days",
                    "action": "reschedule"
                })
            except:
                pass
    return suggestions


# ─── CAREGIVER MONITOR ───────────────────────────────────────────────────────
def check_caregiver_alert(user_id: int) -> bool:
    """Check if caregiver should be notified."""
    logs = get_today_logs(user_id)
    med_logs = [l for l in logs if l["type"] == "medicine"]
    missed = sum(1 for l in med_logs if l["action"] == "skipped")
    
    user = get_user(user_id)
    if missed >= 3 and user and user.get("caregiver"):
        msg = (f"HEALTH ALERT: {user['name']} has missed {missed} critical medicine "
               f"reminders today ({datetime.now().strftime('%d %b %Y')}). "
               f"Please check on them immediately.")
        create_caregiver_alert(user_id, msg)
        return True
    return False


# ─── PRESCRIPTION OCR ────────────────────────────────────────────────────────
def parse_prescription_text(text: str) -> list:
    """Parse medicine details from OCR text using pattern matching."""
    import re
    medicines = []
    lines = text.split("\n")
    
    # Common medicine patterns
    dosage_pattern = re.compile(
        r'(\d+\s*mg|\d+\s*ml|\d+\s*tablet|\d+\s*cap)', re.IGNORECASE
    )
    time_keywords = {
        "morning": "08:00", "afternoon": "13:00",
        "evening": "18:00", "night": "21:00",
        "twice": "2x", "thrice": "3x",
        "breakfast": "08:00", "lunch": "13:00",
        "dinner": "19:30", "bedtime": "21:30"
    }
    
    known_medicines = [
        "Metformin","Glucophage","Aspirin","Paracetamol","Atorvastatin",
        "Lisinopril","Amlodipine","Omeprazole","Metoprolol","Losartan",
        "Ramipril","Cetirizine","Pantoprazole","Vitamin","Calcium","Iron",
        "Amoxicillin","Ciprofloxacin","Azithromycin","Doxycycline",
        "Levothyroxine","Insulin","Glipizide","Januvia","Warfarin"
    ]
    
    current_med = None
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check for medicine name
        for med in known_medicines:
            if med.lower() in line.lower():
                if current_med:
                    medicines.append(current_med)
                dosage_match = dosage_pattern.search(line)
                current_med = {
                    "name": med,
                    "dosage": dosage_match.group(0) if dosage_match else "1 tablet",
                    "times": ["08:00"],
                    "duration": 7
                }
                # Check timing
                for kw, t in time_keywords.items():
                    if kw in line.lower():
                        if t not in ["2x","3x"]:
                            current_med["times"] = [t]
                        elif t == "2x":
                            current_med["times"] = ["08:00","20:00"]
                        elif t == "3x":
                            current_med["times"] = ["08:00","14:00","20:00"]
                break
        
        # Duration check
        dur_match = re.search(r'(\d+)\s*(day|week|month)', line, re.IGNORECASE)
        if dur_match and current_med:
            dur = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            if unit == "week": dur *= 7
            if unit == "month": dur *= 30
            current_med["duration"] = dur
    
    if current_med:
        medicines.append(current_med)
    
    # If nothing found, try generic extraction
    if not medicines:
        for line in lines:
            words = line.split()
            for i, w in enumerate(words):
                if w[0].isupper() and len(w) > 4 and i < len(words)-1:
                    dosage_match = dosage_pattern.search(line)
                    medicines.append({
                        "name": w,
                        "dosage": dosage_match.group(0) if dosage_match else "1 tablet",
                        "times": ["08:00"],
                        "duration": 7
                    })
                    if len(medicines) >= 5: break
            if len(medicines) >= 5: break
    
    return medicines[:10]  # max 10 medicines
