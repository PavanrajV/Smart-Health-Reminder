/**
 * Smart Health Reminder App — Frontend JS
 * Features: API integration, Web Speech API, Notifications, Adaptive UI
 */

const API = "";   // same origin
let currentUserId = null;
let reminderCheckInterval = null;
let speechSynth = window.speechSynthesis;
let currentVoiceLang = "en";

// ─── SPEECH SYNTHESIS ────────────────────────────────────────────────────────
const LANG_MAP = { en: "en-US", kn: "kn-IN", te: "te-IN", hi: "hi-IN" };

function speak(text, lang) {
  if (!speechSynth) return;
  speechSynth.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = LANG_MAP[lang || currentVoiceLang] || "en-US";
  u.rate = 0.92; u.pitch = 1; u.volume = 1;
  const voices = speechSynth.getVoices();
  const preferred = voices.find(v => v.lang.startsWith(u.lang.split("-")[0]));
  if (preferred) u.voice = preferred;
  u.onstart = () => document.querySelectorAll(".voice-indicator").forEach(el => el.classList.add("active"));
  u.onend = () => document.querySelectorAll(".voice-indicator").forEach(el => el.classList.remove("active"));
  speechSynth.speak(u);
}

function stopSpeech() {
  speechSynth?.cancel();
  document.querySelectorAll(".voice-indicator").forEach(el => el.classList.remove("active"));
}

// Preload voices
speechSynth?.addEventListener("voiceschanged", () => {});

// ─── TOAST NOTIFICATIONS ─────────────────────────────────────────────────────
function toast(title, msg, type = "info", duration = 5000, speakMsg = false) {
  const icons = { info: "💊", success: "✅", danger: "🚨", warning: "⚠️" };
  const cont = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${icons[type] || "🔔"}</span>
    <div style="flex:1">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-msg">${msg}</div>` : ""}
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;
  cont.appendChild(el);
  if (speakMsg) speak(title + ". " + msg);
  if (duration > 0) setTimeout(() => el.remove(), duration);

  // Browser notification
  if (Notification.permission === "granted") {
    new Notification("Health Reminder — " + title, { body: msg, icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💊</text></svg>" });
  }
}

function requestNotifPermission() {
  if ("Notification" in window) Notification.requestPermission();
}

// ─── API HELPERS ─────────────────────────────────────────────────────────────
async function api(path, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  return res.json();
}

// ─── NAVIGATION ──────────────────────────────────────────────────────────────
function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById("page-" + id)?.classList.add("active");
  document.querySelector(`[data-page="${id}"]`)?.classList.add("active");

  const titles = {
    dashboard: "Dashboard", reminders: "Today's Reminders",
    medicines: "Medicine Manager", hydration: "Hydration Tracker",
    exercise: "Exercise & Activity", ocr: "Prescription Scanner",
    reports: "Health Reports", settings: "Settings", caregiver: "Caregiver Alerts"
  };
  document.getElementById("page-title").textContent = titles[id] || "Health App";

  // Load page data
  switch (id) {
    case "dashboard":  loadDashboard();  break;
    case "reminders":  loadReminders();  break;
    case "medicines":  loadMedicines();  break;
    case "hydration":  loadHydration();  break;
    case "reports":    loadReports();    break;
    case "caregiver":  loadCaregiverAlerts(); break;
    case "exercise":   loadExercise();   break;
  }
}

// ─── CLOCK ───────────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById("live-clock").textContent = now.toLocaleTimeString("en-IN");
}
setInterval(updateClock, 1000);
updateClock();

// ─── DASHBOARD ───────────────────────────────────────────────────────────────
async function loadDashboard() {
  if (!currentUserId) return;
  const r = await api("/api/dashboard");
  if (!r.success) return;
  const d = r.data;

  // Score ring
  const score = d.health_score || 0;
  document.getElementById("score-num").textContent = Math.round(score);
  document.getElementById("score-grade").textContent = d.grade || "";
  animateScoreRing(score);

  const tag = document.getElementById("score-tag");
  tag.textContent = d.grade || "";
  tag.className = "score-label-tag";
  if (score >= 80) { tag.style.background = "#dcfce7"; tag.style.color = "#15803d"; }
  else if (score >= 60) { tag.style.background = "#dbeafe"; tag.style.color = "#1d4ed8"; }
  else if (score >= 40) { tag.style.background = "#fef3c7"; tag.style.color = "#92400e"; }
  else { tag.style.background = "#fee2e2"; tag.style.color = "#b91c1c"; }

  // Stats
  document.getElementById("stat-total").textContent   = d.total_reminders || 0;
  document.getElementById("stat-done").textContent    = d.completed_today || 0;
  document.getElementById("stat-pending").textContent = (d.total_reminders || 0) - (d.completed_today || 0);
  document.getElementById("stat-water").textContent   = d.hydration?.glasses || 0;

  // Progress bar
  const pct = d.total_reminders > 0 ? Math.round((d.completed_today / d.total_reminders) * 100) : 0;
  document.getElementById("dash-progress").style.width = pct + "%";
  document.getElementById("dash-progress-pct").textContent = pct + "%";

  // Upcoming reminders
  const upEl = document.getElementById("upcoming-reminders");
  upEl.innerHTML = "";
  if (!d.upcoming_reminders?.length) {
    upEl.innerHTML = `<div class="empty-state"><div class="icon">🎉</div><p>All done for now!</p></div>`;
  } else {
    d.upcoming_reminders.forEach(r => {
      upEl.innerHTML += reminderHTML(r, true);
    });
  }

  // Health tips
  const tipsEl = document.getElementById("health-tips");
  tipsEl.innerHTML = "";
  (d.health_tips || []).forEach(tip => {
    tipsEl.innerHTML += `<span class="tip-chip">🥗 ${tip}</span>`;
  });
  (d.exercise_tips || []).forEach(tip => {
    tipsEl.innerHTML += `<span class="tip-chip">🏃 ${tip}</span>`;
  });

  // Condition alerts
  const alertsEl = document.getElementById("condition-alerts");
  alertsEl.innerHTML = "";
  (d.condition_alerts || []).forEach(a => {
    alertsEl.innerHTML += `<div class="alert-banner warning"><span>⚠️</span> ${a}</div>`;
  });

  // Adaptive suggestions on dashboard
  const adaptEl = document.getElementById("dash-adaptive");
  if (adaptEl && d.adaptive_suggestions?.length) {
    adaptEl.innerHTML = `<div class="alert-banner info"><span>🤖</span> AI detected ${d.adaptive_suggestions.length} optimization(s). Visit <b>Reports</b> tab.</div>`;
  }
}

function animateScoreRing(score) {
  const circle = document.getElementById("score-circle");
  if (!circle) return;
  const r = 70; const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  circle.style.strokeDasharray = `${circ}`;
  circle.style.strokeDashoffset = `${offset}`;
  // Color based on score
  if (score >= 80) circle.style.stroke = "#22c55e";
  else if (score >= 60) circle.style.stroke = "#3b82f6";
  else if (score >= 40) circle.style.stroke = "#f59e0b";
  else circle.style.stroke = "#ef4444";
}

// ─── REMINDERS ───────────────────────────────────────────────────────────────
function reminderHTML(r, compact = false) {
  const iconMap = { medicine: "💊", water: "💧", exercise: "🏃", meal: "🍽️", sleep: "🌙", health_tip: "💡", wake: "☀️" };
  const icon = iconMap[r.type] || "🔔";
  const isDue = r.is_due;
  const doneClass = r.done ? "completed" : "";
  const dueClass = isDue && !r.done ? "is-due" : "";
  const btns = compact ? "" : `
    <div class="action-btns">
      <button class="btn-action btn-voice" onclick="speak('${escAttr(r.body || r.title)}')">🔊</button>
      <button class="btn-action btn-done"   onclick="doAction(${r.id},'completed')">Done</button>
      <button class="btn-action btn-snooze" onclick="doAction(${r.id},'snoozed')">Snooze</button>
      <button class="btn-action btn-skip"   onclick="doAction(${r.id},'skipped')">Skip</button>
    </div>`;
  return `
    <div class="reminder-item ${dueClass} ${doneClass}" id="rem-${r.id}">
      <div class="reminder-icon ${r.type}">${icon}</div>
      <div class="reminder-body">
        <div class="reminder-title">${r.title}</div>
        <div class="reminder-desc">${r.body || ""}</div>
      </div>
      <div class="reminder-time">${r.scheduled}</div>
      <span class="priority-badge priority-${r.priority}">${r.priority}</span>
      ${btns}
    </div>`;
}

async function loadReminders() {
  if (!currentUserId) return;
  const r = await api("/api/reminders");
  if (!r.success) return;
  const list = document.getElementById("reminder-list");
  const filter = document.getElementById("reminder-filter")?.value || "all";
  let items = r.data;
  if (filter === "due") items = items.filter(x => x.is_due);
  if (filter === "medicine") items = items.filter(x => x.type === "medicine");
  if (filter === "pending") items = items.filter(x => !x.done);

  list.innerHTML = items.length
    ? items.map(x => reminderHTML(x)).join("")
    : `<div class="empty-state"><div class="icon">✅</div><p>No reminders to show.</p></div>`;

  // Update badge
  const due = r.data.filter(x => x.is_due).length;
  document.getElementById("reminder-badge").textContent = due || "";
  document.getElementById("reminder-badge").style.display = due ? "" : "none";
}

async function doAction(rid, action) {
  const r = await api(`/api/reminders/${rid}/action`, "POST", { action });
  if (!r.success) return;
  const el = document.getElementById(`rem-${rid}`);
  if (el) {
    if (action === "completed") { el.classList.add("completed"); toast("✅ Completed!", "Great job staying on track.", "success", 3000, false); }
    else if (action === "snoozed") { toast("⏰ Snoozed", "We'll remind you again in 10 minutes.", "warning"); }
    else { toast("⚠️ Skipped", "Don't skip too many — your health matters!", "danger"); }
  }
  if (r.data?.caregiver_alerted) {
    toast("🚨 Caregiver Alert", "Your caregiver has been notified!", "danger", 8000, true);
  }
  loadReminders();
  loadDashboard();
}

async function generateSchedule() {
  if (!currentUserId) return;
  const btn = document.getElementById("generate-btn");
  if (btn) { btn.textContent = "Generating..."; btn.disabled = true; }
  const r = await api("/api/reminders/generate", "POST");
  if (btn) { btn.textContent = "🔄 Regenerate Schedule"; btn.disabled = false; }
  if (r.success) {
    toast("📅 Schedule Generated", `${r.data.length} reminders created for today.`, "success");
    loadReminders();
  }
}

// Auto-check for due reminders every minute
function startReminderWatcher() {
  reminderCheckInterval = setInterval(async () => {
    if (!currentUserId) return;
    const r = await api("/api/reminders");
    if (!r.success) return;
    const now = new Date().toTimeString().slice(0, 5);
    r.data.forEach(rem => {
      if (rem.scheduled === now && rem.is_due && !rem.done) {
        const iconMap = { medicine: "💊", water: "💧", exercise: "🏃", meal: "🍽️", sleep: "🌙" };
        toast(rem.title, rem.body, rem.priority === "HIGH" ? "danger" : "info", 10000, true);
      }
    });
  }, 60000);
}

// ─── MEDICINES ────────────────────────────────────────────────────────────────
async function loadMedicines() {
  if (!currentUserId) return;
  const r = await api("/api/medicines");
  if (!r.success) return;
  const list = document.getElementById("med-list");
  list.innerHTML = r.data.length ? r.data.map(m => {
    const times = JSON.parse(m.times || '["08:00"]').join(", ");
    return `<div class="med-card">
      <div class="med-icon">💊</div>
      <div style="flex:1">
        <div class="med-name">${m.name}</div>
        <div class="med-detail">${m.dosage} · ${times} · ${m.duration} days</div>
        ${m.from_ocr ? '<span class="badge-pill bg-ocr">📷 From OCR</span>' : ""}
      </div>
      <span class="med-badge priority-${m.priority}">${m.priority}</span>
      <button class="btn-danger btn-sm ml-auto" onclick="deleteMedicine(${m.id})" style="margin-left:10px">🗑️</button>
    </div>`;
  }).join("") : `<div class="empty-state"><div class="icon">💊</div><p>No medicines added yet.</p></div>`;
}

async function addMedicine(e) {
  e.preventDefault();
  const f = e.target;
  const times = [];
  if (f.time1.value) times.push(f.time1.value);
  if (f.time2.value) times.push(f.time2.value);
  if (f.time3.value) times.push(f.time3.value);
  const r = await api("/api/medicines", "POST", {
    name: f.name.value, dosage: f.dosage.value,
    times, duration: parseInt(f.duration.value) || 7,
    priority: f.priority.value
  });
  if (r.success) {
    toast("💊 Medicine Added", `${f.name.value} scheduled successfully.`, "success");
    f.reset(); loadMedicines(); closeModal("med-modal");
  }
}

async function deleteMedicine(mid) {
  if (!confirm("Remove this medicine?")) return;
  const r = await api(`/api/medicines/${mid}`, "DELETE");
  if (r.success) { toast("🗑️ Removed", "Medicine deleted.", "warning"); loadMedicines(); }
}

// ─── HYDRATION ────────────────────────────────────────────────────────────────
async function loadHydration() {
  if (!currentUserId) return;
  const r = await api("/api/hydration");
  if (!r.success) return;
  const { glasses, target, pct } = r.data;

  document.getElementById("hydration-pct").textContent = pct + "%";
  document.getElementById("hydration-bar").style.width = pct + "%";
  document.getElementById("hydration-count").textContent = `${glasses} / ${target} glasses`;

  const grid = document.getElementById("water-grid");
  grid.innerHTML = "";
  for (let i = 0; i < target; i++) {
    const div = document.createElement("span");
    div.className = `water-glass ${i < glasses ? "filled" : "empty"}`;
    div.textContent = "💧";
    div.title = i < glasses ? "Logged" : "Click after drinking";
    div.onclick = () => logGlass();
    grid.appendChild(div);
  }

  // Hydration message
  const msgEl = document.getElementById("hydration-msg");
  if (pct >= 100) msgEl.textContent = "🎉 Daily goal achieved! Amazing!";
  else if (pct >= 60) msgEl.textContent = `🙂 Keep going! ${target - glasses} more glasses to go.`;
  else msgEl.textContent = `💪 Stay hydrated! Drink ${target - glasses} more glasses.`;
}

async function logGlass() {
  const r = await api("/api/hydration", "POST", { glasses: 1 });
  if (r.success) { toast("💧 Water Logged!", "Keep it up!", "info", 2000); loadHydration(); loadDashboard(); }
}

// ─── EXERCISE PAGE ────────────────────────────────────────────────────────────
async function loadExercise() {
  if (!currentUserId) return;
  const r = await api("/api/dashboard");
  if (!r.success) return;
  const tips = document.getElementById("exercise-tips");
  tips.innerHTML = "";
  (r.data.exercise_tips || []).forEach(t => {
    tips.innerHTML += `<div class="med-card"><div class="med-icon">🏃</div><div><div class="med-name">${t}</div></div></div>`;
  });
}

async function logExercise(type) {
  await api("/api/reminders/generate", "POST");
  toast("🏃 Exercise Logged!", `${type} recorded. Great work!`, "success", 3000, true);
  speak(`${type} logged. Excellent effort!`);
}

// ─── REPORTS ─────────────────────────────────────────────────────────────────
async function loadReports() {
  if (!currentUserId) return;
  const r = await api("/api/health-score");
  if (!r.success) return;
  const d = r.data;

  // Score display
  document.getElementById("report-score").textContent = Math.round(d.score || 0);
  document.getElementById("report-grade").textContent = d.grade || "";

  // Breakdown bars
  const bd = d.breakdown || {};
  setBar("bar-medicine",  bd.medicine_score    || 0);
  setBar("bar-hydration", bd.hydration_score   || 0);
  setBar("bar-compliance",bd.compliance_pct    || 0);

  document.getElementById("stat-completed-r").textContent = bd.completed || 0;
  document.getElementById("stat-skipped-r").textContent   = bd.skipped   || 0;
  document.getElementById("stat-snoozed-r").textContent   = bd.snoozed   || 0;
  document.getElementById("stat-hydration-r").textContent = bd.hydration_glasses || 0;

  // 7-day chart
  const history = d.history || [];
  renderChart(history);

  // Adaptive suggestions
  const ar = await api("/api/adaptive");
  const adEl = document.getElementById("adaptive-list");
  adEl.innerHTML = "";
  if (ar.success && ar.data?.length) {
    ar.data.forEach(s => {
      adEl.innerHTML += `
        <div class="suggestion-card">
          <span class="suggestion-icon">🤖</span>
          <div class="suggestion-body">
            <div class="suggestion-title">${s.title}</div>
            <div class="suggestion-detail">${s.reason} · Current: ${s.current_time} → Suggested: ${s.suggested_time}</div>
          </div>
          <button class="btn-primary btn-sm" onclick="applyAdaptive(${s.reminder_id},'${s.suggested_time}')">Apply</button>
        </div>`;
    });
  } else {
    adEl.innerHTML = `<div class="alert-banner success"><span>🤖</span> AI is happy with your current schedule!</div>`;
  }
}

function setBar(id, val) {
  const el = document.getElementById(id);
  if (el) { el.style.width = val + "%"; el.title = Math.round(val) + "%"; }
  const pctEl = document.getElementById(id + "-pct");
  if (pctEl) pctEl.textContent = Math.round(val) + "%";
}

function renderChart(history) {
  const wrap = document.getElementById("score-chart");
  if (!wrap) return;
  wrap.innerHTML = "";
  const days = 7;
  const data = [...history].reverse().slice(-days);
  while (data.length < days) data.unshift({ score: 0, date: "" });
  const maxScore = 100;
  data.forEach(d => {
    const pct = d.score ? Math.round((d.score / maxScore) * 100) : 0;
    const label = d.date ? new Date(d.date).toLocaleDateString("en", { weekday: "short" }) : "—";
    const col = document.createElement("div");
    col.className = "chart-bar-col";
    col.innerHTML = `
      <div class="chart-bar" data-val="${Math.round(d.score || 0)}" style="height:${pct}%"></div>
      <div class="chart-date">${label}</div>`;
    wrap.appendChild(col);
  });
}

async function applyAdaptive(rid, time) {
  const r = await api("/api/adaptive/apply", "POST", { reminder_id: rid, suggested_time: time });
  if (r.success) { toast("🤖 Schedule Updated", `Reminder moved to ${time}.`, "success"); loadReports(); }
}

// ─── CAREGIVER ALERTS ────────────────────────────────────────────────────────
async function loadCaregiverAlerts() {
  if (!currentUserId) return;
  const r = await api("/api/caregiver-alerts");
  if (!r.success) return;
  const list = document.getElementById("caregiver-list");
  list.innerHTML = r.data.length ? r.data.map(a => `
    <div class="alert-banner danger">
      <span>🚨</span>
      <div>
        <div class="fw-700">${a.message}</div>
        <div class="text-muted">${new Date(a.sent_at).toLocaleString()}</div>
      </div>
    </div>`).join("") : `<div class="alert-banner success"><span>✅</span> No alerts — compliance is good!</div>`;
}

// ─── OCR PRESCRIPTION ────────────────────────────────────────────────────────
function initOCR() {
  const drop = document.getElementById("ocr-drop");
  const input = document.getElementById("ocr-file");
  if (!drop || !input) return;

  drop.onclick = () => input.click();
  input.onchange = () => { if (input.files[0]) processOCR(input.files[0]); };

  drop.ondragover = (e) => { e.preventDefault(); drop.classList.add("dragover"); };
  drop.ondragleave = () => drop.classList.remove("dragover");
  drop.ondrop = (e) => {
    e.preventDefault(); drop.classList.remove("dragover");
    if (e.dataTransfer.files[0]) processOCR(e.dataTransfer.files[0]);
  };
}

async function processOCR(file) {
  const statusEl = document.getElementById("ocr-status");
  statusEl.innerHTML = `<div class="alert-banner info"><span>🔍</span> Scanning prescription... please wait.</div>`;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const b64 = e.target.result;
    const r = await api("/api/ocr", "POST", { image_base64: b64 });
    if (!r.success) {
      statusEl.innerHTML = `<div class="alert-banner danger"><span>❌</span> ${r.error}</div>`;
      return;
    }
    const d = r.data;
    let html = `<div class="alert-banner success"><span>✅</span> Found <b>${d.medicines_found}</b> medicine(s) — <b>${d.added_to_profile}</b> added to your profile.</div>`;
    if (d.medicines?.length) {
      html += `<div class="mt-3"><b>Extracted Medicines:</b></div>`;
      d.medicines.forEach(m => {
        html += `<div class="med-card mt-2">
          <div class="med-icon">💊</div>
          <div><div class="med-name">${m.name}</div>
          <div class="med-detail">${m.dosage} · ${Array.isArray(m.times) ? m.times.join(", ") : m.times} · ${m.duration} days</div></div>
          <span class="badge-pill bg-ocr">OCR</span></div>`;
      });
    }
    if (!d.ocr_used) {
      html += `<div class="alert-banner warning mt-3"><span>ℹ️</span> Using demo OCR data. Install <code>pytesseract</code> for real OCR.</div>`;
    }
    statusEl.innerHTML = html;
    toast("📷 Prescription Scanned", `${d.medicines_found} medicines detected!`, "success", 5000, true);
    loadMedicines();
  };
  reader.readAsDataURL(file);
}

// ─── USER SETUP ───────────────────────────────────────────────────────────────
async function loadExistingUsers() {
  const r = await api("/api/users");
  if (!r.success) return;
  const sel = document.getElementById("existing-users");
  if (!sel) return;
  sel.innerHTML = `<option value="">— Select user —</option>`;
  r.data.forEach(u => {
    sel.innerHTML += `<option value="${u.id}">${u.name} (${u.condition || "general"})</option>`;
  });
  if (r.data.length) {
    document.getElementById("existing-user-section").style.display = "";
  }
}

async function selectExistingUser() {
  const uid = document.getElementById("existing-users").value;
  if (!uid) return;
  await api(`/api/session/${uid}`, "POST");
  currentUserId = parseInt(uid);
  const r = await api(`/api/users/${uid}`);
  if (r.success) initAppForUser(r.data);
}

async function createProfile(e) {
  e.preventDefault();
  const f = e.target;
  const data = {
    name: f.name.value, age: parseInt(f.age.value) || 25,
    gender: f.gender.value, condition: f.condition.value,
    wake_time: f.wake_time.value, sleep_time: f.sleep_time.value,
    language: f.language.value, caregiver: f.caregiver.value
  };
  const r = await api("/api/users", "POST", data);
  if (r.success) {
    currentUserId = r.data.id;
    currentVoiceLang = data.language;
    initAppForUser(r.data);
    toast("🎉 Welcome!", `Profile created for ${data.name}.`, "success", 5000, true);
  }
}

function initAppForUser(user) {
  currentUserId = user.id;
  currentVoiceLang = user.language || "en";
  document.getElementById("setup-screen").style.display = "none";
  document.getElementById("app-shell").style.display = "";
  document.getElementById("user-display-name").textContent = user.name;
  document.getElementById("user-display-cond").textContent = user.condition || "General Health";
  document.getElementById("user-avatar-letter").textContent = user.name[0].toUpperCase();
  requestNotifPermission();
  startReminderWatcher();
  showPage("dashboard");
  speak(`Welcome back ${user.name}. Your health companion is ready.`, user.language);
}

// ─── SETTINGS ────────────────────────────────────────────────────────────────
async function saveSettings(e) {
  e.preventDefault();
  if (!currentUserId) return;
  const f = e.target;
  const data = {
    wake_time: f.wake_time.value, sleep_time: f.sleep_time.value,
    language: f.language.value, caregiver: f.caregiver.value
  };
  const r = await api(`/api/users/${currentUserId}`, "PUT", data);
  if (r.success) {
    currentVoiceLang = data.language;
    toast("✅ Settings Saved", "Schedule will be regenerated.", "success");
    await api("/api/reminders/generate", "POST");
  }
}

// ─── MODALS ──────────────────────────────────────────────────────────────────
function openModal(id) { document.getElementById(id)?.classList.add("active"); }
function closeModal(id) { document.getElementById(id)?.classList.remove("active"); }

document.addEventListener("click", e => {
  if (e.target.classList.contains("modal-overlay")) closeModal(e.target.id);
});

// ─── VOICE TEST ──────────────────────────────────────────────────────────────
function testVoice() {
  const msgs = {
    en: "Hello! Your Smart Health Companion is active. Stay healthy!",
    kn: "ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಆರೋಗ್ಯ ಸಹಾಯಕ ಸಕ್ರಿಯವಾಗಿದೆ.",
    te: "నమస్కారం! మీ ఆరోగ్య సహాయకుడు సక్రియంగా ఉన్నారు.",
    hi: "नमस्ते! आपका स्वास्थ्य सहायक सक्रिय है।"
  };
  speak(msgs[currentVoiceLang] || msgs.en);
  toast("🔊 Voice Test", "Playing voice notification...", "info", 3000);
}

// ─── HELPERS ─────────────────────────────────────────────────────────────────
function escAttr(str) { return (str || "").replace(/'/g, "&#39;").replace(/"/g, "&quot;"); }

// ─── INIT ─────────────────────────────────────────────────────────────────────
window.addEventListener("load", async () => {
  const sysR = await api("/api/status");
  if (sysR.success) {
    const s = sysR.data;
    const badges = [
      { id: "badge-ocr", val: s.ocr, label: "OCR" },
      { id: "badge-tts", val: s.tts, label: "gTTS" },
      { id: "badge-sched", val: s.scheduler, label: "Scheduler" }
    ];
    badges.forEach(b => {
      const el = document.getElementById(b.id);
      if (el) { el.textContent = (b.val ? "✓ " : "✗ ") + b.label; el.style.color = b.val ? "#15803d" : "#b91c1c"; }
    });
  }
  initOCR();
  loadExistingUsers();
});
