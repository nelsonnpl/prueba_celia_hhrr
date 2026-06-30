"""
RIU360 Corporate Portal - Backend Server
Python + Flask with JSON file persistence
"""

import json
import os
import uuid
import secrets
from datetime import datetime, timezone

from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="public", static_url_path="")
app.config["JSON_SORT_KEYS"] = False

PORT = int(os.environ.get("PORT", 3456))

# ─── Persistence Layer ────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "submissions.json")
CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.json")

os.makedirs(DATA_DIR, exist_ok=True)


def read_json(filepath, fallback=None):
    if fallback is None:
        fallback = []
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return fallback


def write_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing {filepath}: {e}")


# ─── Candidate Registry ──────────────────────────────────────────────────────
DEFAULT_CANDIDATES = [
    {"id": "CAND-2024-001", "email": "maria.garcia@riu.com", "name": "Maria Garcia", "testCode": "RIU-PRUEBA-2024", "active": True},
    {"id": "CAND-2024-002", "email": "jean.dupont@consulting.fr", "name": "Jean Dupont", "testCode": "RIU-PRUEBA-2024", "active": True},
    {"id": "CAND-2024-003", "email": "anna.schmidt@riu.de", "name": "Anna Schmidt", "testCode": "RIU-PRUEBA-2024", "active": True},
]


def get_candidates():
    stored = read_json(CANDIDATES_FILE, None)
    if stored is None:
        write_json(CANDIDATES_FILE, DEFAULT_CANDIDATES)
        return DEFAULT_CANDIDATES
    return stored


HONEYPOT_WORD = "anturio"


def calculate_risk_score(honeypot_triggered, tab_switches_count, paste_attempts_count,
                         is_keystroke_anomaly, total_keystrokes, char_count, time_spent_minutes):
    score = 0
    if honeypot_triggered: score += 50
    if is_keystroke_anomaly: score += 25
    if tab_switches_count > 10: score += 10
    elif tab_switches_count > 5: score += 5
    if paste_attempts_count > 0: score += paste_attempts_count * 5
    if time_spent_minutes > 0 and char_count / time_spent_minutes > 500: score += 10
    if total_keystrokes == 0 and char_count > 0: score += 30
    return min(score, 100)


# ─── Static Files ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("public", "index.html")


@app.route("/admin")
def admin():
    return send_from_directory("public", "admin.html")


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request body."}), 400

    candidate_id = data.get("candidateId", "").strip()
    test_code = data.get("testCode", "").strip()

    if not candidate_id or not test_code:
        return jsonify({"success": False, "error": "Candidate ID and test code are required."}), 400

    candidates = get_candidates()
    candidate = None
    for c in candidates:
        match_id = c["id"] == candidate_id or c.get("email", "") == candidate_id
        if match_id and c["testCode"] == test_code and c["active"]:
            candidate = c
            break

    if not candidate:
        return jsonify({"success": False, "error": "Invalid credentials. Please verify your Candidate ID and Test Code."}), 401

    session_token = secrets.token_hex(32)
    login_timestamp = datetime.now(timezone.utc).isoformat()

    return jsonify({
        "success": True,
        "candidate": {"id": candidate["id"], "name": candidate["name"], "email": candidate["email"]},
        "sessionToken": session_token,
        "loginTimestamp": login_timestamp,
    })


@app.route("/api/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request body."}), 400

    candidate_id = data.get("candidateId", "")
    essay_response = data.get("essayResponse", "")

    if not candidate_id or not essay_response:
        return jsonify({"success": False, "error": "Candidate ID and essay response are required."}), 400

    text = essay_response
    honeypot_triggered = HONEYPOT_WORD in text.lower()
    char_count = len(text)
    total_keystrokes = data.get("totalKeystrokes", 0)
    is_keystroke_anomaly = total_keystrokes > 0 and char_count > total_keystrokes * 2
    is_suspicious = honeypot_triggered or is_keystroke_anomaly
    word_count = data.get("wordCount", 0) or len(text.split())
    tab_switches = data.get("tabSwitchesCount", 0)
    paste_attempts = data.get("pasteAttemptsCount", 0)
    time_minutes = data.get("timeSpentMinutes", 0)

    risk_score = calculate_risk_score(honeypot_triggered, tab_switches, paste_attempts,
                                       is_keystroke_anomaly, total_keystrokes, char_count, time_minutes)

    submission = {
        "id": str(uuid.uuid4()),
        "candidateId": candidate_id,
        "sessionToken": data.get("sessionToken"),
        "essayResponse": text,
        "wordCount": word_count,
        "timeSpentMinutes": time_minutes,
        "submittedAt": datetime.now(timezone.utc).isoformat(),
        "telemetry": {
            "tabSwitchesCount": tab_switches,
            "pasteAttemptsCount": paste_attempts,
            "totalKeystrokes": total_keystrokes,
            "rightClickAttempts": data.get("rightClickAttempts", 0),
            "blockedShortcuts": data.get("blockedShortcuts", 0),
            "startTime": data.get("startTime"),
            "endTime": data.get("endTime"),
            "charCount": char_count,
        },
        "analysis": {
            "honeypotTriggered": honeypot_triggered,
            "isKeystrokeAnomaly": is_keystroke_anomaly,
            "isSuspicious": is_suspicious,
            "riskScore": risk_score,
        },
    }

    submissions = read_json(DB_FILE, [])
    submissions.append(submission)
    write_json(DB_FILE, submissions)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{now}] Submission from {candidate_id} | Suspicious: {is_suspicious} | Honeypot: {honeypot_triggered} | Risk: {risk_score}")

    return jsonify({"success": True, "message": "Evaluation submitted successfully.", "submissionId": submission["id"]})


# ─── Admin API ────────────────────────────────────────────────────────────────

@app.route("/api/admin/submissions", methods=["GET"])
def admin_submissions():
    submissions = read_json(DB_FILE, [])
    candidates = get_candidates()
    candidate_map = {c["id"]: c for c in candidates}

    overview = []
    for s in submissions:
        cand = candidate_map.get(s["candidateId"], {})
        overview.append({
            "id": s["id"],
            "candidateId": s["candidateId"],
            "candidateName": cand.get("name", "Unknown"),
            "candidateEmail": cand.get("email", ""),
            "wordCount": s["wordCount"],
            "timeSpentMinutes": s["timeSpentMinutes"],
            "submittedAt": s["submittedAt"],
            "analysis": s["analysis"],
            "telemetry": s["telemetry"],
        })
    return jsonify(overview)


@app.route("/api/admin/submission/<submission_id>", methods=["GET"])
def admin_submission_detail(submission_id):
    submissions = read_json(DB_FILE, [])
    candidates = get_candidates()
    candidate_map = {c["id"]: c for c in candidates}

    for s in submissions:
        if s["id"] == submission_id:
            cand = candidate_map.get(s["candidateId"], {})
            result = dict(s)
            result["candidateName"] = cand.get("name", "Unknown")
            result["candidateEmail"] = cand.get("email", "")
            return jsonify(result)

    return jsonify({"error": "Submission not found"}), 404


@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    submissions = read_json(DB_FILE, [])
    candidates = get_candidates()

    total = len(submissions)
    suspicious = sum(1 for s in submissions if s.get("analysis", {}).get("isSuspicious", False))
    honeypot = sum(1 for s in submissions if s.get("analysis", {}).get("honeypotTriggered", False))
    avg_words = sum(s.get("wordCount", 0) for s in submissions) / total if total else 0
    avg_time = sum(s.get("timeSpentMinutes", 0) for s in submissions) / total if total else 0
    avg_risk = sum(s.get("analysis", {}).get("riskScore", 0) for s in submissions) / total if total else 0
    total_candidates = len(candidates)
    submitted_ids = set(s["candidateId"] for s in submissions)
    pending = total_candidates - len(submitted_ids)

    return jsonify({
        "totalSubmissions": total,
        "totalCandidates": total_candidates,
        "pendingSubmissions": pending,
        "suspiciousCount": suspicious,
        "honeypotCount": honeypot,
        "averageWordCount": round(avg_words),
        "averageTimeMinutes": round(avg_time, 1),
        "averageRiskScore": round(avg_risk, 1),
    })


@app.route("/api/admin/candidates", methods=["GET"])
def admin_candidates():
    candidates = get_candidates()
    submissions = read_json(DB_FILE, [])
    submitted_ids = set(s["candidateId"] for s in submissions)

    result = []
    for c in candidates:
        result.append({
            "id": c["id"],
            "name": c["name"],
            "email": c["email"],
            "active": c["active"],
            "hasSubmitted": c["id"] in submitted_ids,
        })
    return jsonify(result)


# ─── Start Server ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    candidates = get_candidates()
    print("=" * 55)
    print("  RIU360 Corporate Portal - Assessment Server (Python)")
    print(f"  Running on: http://localhost:{PORT}")
    print(f"  Admin panel: http://localhost:{PORT}/admin")
    print("  Environment: Production Simulation")
    print("=" * 55)
    print(f"  Test candidates loaded: {len(candidates)}")
    print(f"  Submissions DB: {DB_FILE}")
    print("=" * 55)
    app.run(host="0.0.0.0", port=PORT, debug=False)
