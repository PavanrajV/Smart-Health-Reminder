# 💊 Smart Health Reminder Application
### AI-Powered · Multilingual · Adaptive · Full-Stack

---

## 🚀 QUICK START

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Install Tesseract OCR for real prescription scanning
# Ubuntu/Debian:   sudo apt-get install tesseract-ocr
# macOS:           brew install tesseract
# Windows:         https://github.com/UB-Mannheim/tesseract/wiki

# 3. Run the application
python app.py

# 4. Open browser
http://localhost:5000
```

---

## 🗂️ PROJECT STRUCTURE

```
smart_health/
├── app.py              ← Flask backend (all API routes)
├── database.py         ← SQLite database layer
├── ai_engine.py        ← Rule-based AI + Adaptive Learning
├── requirements.txt    ← Python dependencies
├── health.db           ← SQLite DB (auto-created)
├── templates/
│   └── index.html      ← Single-Page App frontend
└── static/
    ├── css/style.css   ← Custom stylesheet
    └── js/app.js       ← Frontend JavaScript + Web Speech API
```

---

## 🧠 FEATURES

### Core Features
| Feature | Status |
|---------|--------|
| User Health Profile | ✅ Complete |
| AI Schedule Generator | ✅ Complete |
| Medicine Manager | ✅ Complete |
| Smart Reminders (voice + popup) | ✅ Complete |
| Hydration Tracker | ✅ Complete |
| Exercise Planner | ✅ Complete |
| OCR Prescription Scanner | ✅ Complete |
| Multi-language Voice (EN/KN/TE/HI) | ✅ Complete |
| Health Score Calculator | ✅ Complete |
| 7-Day Score Chart | ✅ Complete |
| Caregiver Alert System | ✅ Complete |
| Adaptive Learning Engine | ✅ Complete |
| Browser Notifications | ✅ Complete |
| SQLite Offline DB | ✅ Complete |
| APScheduler Background Jobs | ✅ Complete |

---

## 🔌 API ENDPOINTS

| Method | Route | Description |
|--------|-------|-------------|
| POST | /api/users | Create user profile |
| GET | /api/users | List all users |
| PUT | /api/users/{id} | Update user |
| GET | /api/reminders | Get today's reminders |
| POST | /api/reminders/generate | Regenerate schedule |
| POST | /api/reminders/{id}/action | Mark done/snooze/skip |
| GET | /api/medicines | List medicines |
| POST | /api/medicines | Add medicine |
| DELETE | /api/medicines/{id} | Remove medicine |
| GET | /api/hydration | Get hydration status |
| POST | /api/hydration | Log water intake |
| GET | /api/health-score | Calculate health score |
| GET | /api/adaptive | AI suggestions |
| POST | /api/adaptive/apply | Apply AI suggestion |
| POST | /api/ocr | Scan prescription image |
| POST | /api/tts | Text-to-speech |
| GET | /api/caregiver-alerts | Get caregiver alerts |
| GET | /api/dashboard | Full dashboard data |
| GET | /api/status | System status |

---

## 🤖 AI ENGINE

### Rule-Based Health Classification
- 10 health conditions with personalized rules
- Age-group based recommendations (Young/Adult/Senior)
- Exercise intensity adaptation
- Dietary guidance per condition

### Adaptive Learning Algorithm
```
IF reminder skipped ≥ 3 times in 7 days:
    → Suggest +30min time shift
    → Notify user of optimization
    
IF task completed ≥ 5 days consistently:
    → Mark as habit formed
    → Reduce alert intensity
```

### Health Score Formula
```
Score = (Compliance × 0.4) + (Hydration × 0.2) + (Medicine × 0.4)

Score ≥ 80 → Excellent 🌟
Score ≥ 60 → Good 👍  
Score ≥ 40 → Needs Improvement ⚠️
Score < 40 → Risk Alert 🚨 (caregiver notified)
```

---

## 🌐 MULTI-LANGUAGE VOICE

Supports Web Speech API voices:
- 🇺🇸 English (en-US)
- 🇮🇳 Kannada (kn-IN)
- 🇮🇳 Telugu (te-IN)  
- 🇮🇳 Hindi (hi-IN)

Example Kannada voice:
```
"ನಿಮ್ಮ Metformin 500mg ತೆಗೆದುಕೊಳ್ಳುವ ಸಮಯ ಆಗಿದೆ"
```

---

## 🛠️ TECH STACK

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| UI Framework | Custom CSS (no Bootstrap dependency) |
| Voice | Web Speech API (SpeechSynthesis) |
| Backend | Python 3.10+ / Flask 3.0 |
| Database | SQLite (offline-capable) |
| OCR | Tesseract + pytesseract |
| TTS | gTTS (fallback: Web Speech API) |
| Scheduler | APScheduler 3.x |
| AI | Rule-based Python engine |

---

## 📝 VIVA ANSWERS

**Q: What AI is used?**
A: Rule-based AI with adaptive learning. We analyze skip patterns (7-day window) and dynamically reschedule reminders. Health score uses weighted multi-factor calculation.

**Q: How does OCR work?**
A: Image → pytesseract (Tesseract engine) → text extraction → regex-based medicine parser → auto-create reminders.

**Q: How is multi-language handled?**
A: MULTILANG dictionary with template strings per language + Web Speech API with language-specific voice selection.

**Q: Why SQLite?**
A: Offline capability, zero-config, perfect for single-user health app. Easy upgrade to PostgreSQL if needed.

**Q: What is adaptive learning?**
A: We track skip frequency per reminder. If skipped ≥3 times in 7 days, AI suggests shifting the time by 30 minutes and notifies user.

---

## 🏆 HACKATHON HIGHLIGHTS

1. **Full offline support** via SQLite
2. **Real OCR** via Tesseract for prescription scanning
3. **Multilingual voice** (4 Indian languages)
4. **Adaptive AI** that learns from user behavior  
5. **Caregiver safety net** for elderly patients
6. **Health Score** computed in real-time
7. **APScheduler** for background compliance monitoring
8. **Browser notifications** + voice announcements
