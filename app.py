"""Minimal secure contact endpoint for the Shakthivel OSINT portfolio.
Run with: python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && flask --app app run
For production, use HTTPS, a production WSGI server, reverse-proxy limits, and a real CSRF strategy.
"""
import os, re, time, sqlite3
from collections import defaultdict, deque
from flask import Flask, request, jsonify, session, send_from_directory, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from email_validator import validate_email, EmailNotValidError

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "") or None,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
    MAX_CONTENT_LENGTH=12_000,
    WTF_CSRF_TIME_LIMIT=3600,
)
if not app.config["SECRET_KEY"]:
    raise RuntimeError("Set a strong random FLASK_SECRET_KEY environment variable before starting.")
csrf = CSRFProtect(app)
# Do not enable ProxyFix unless your deployment has a trusted proxy configured.
DB = os.environ.get("CONTACT_DB", os.path.join(BASE, "contact_submissions.sqlite3"))
RATE = defaultdict(deque)


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")

init_db()

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://db.onlinewebfonts.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://db.onlinewebfonts.com https://cdnjs.cloudflare.com; media-src https://d8j0ntlcm91z4.cloudfront.net; img-src 'self' data:; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    return response

@app.get("/styles.css")
def styles():
    return send_from_directory(BASE, "styles.css", mimetype="text/css")

@app.get("/main.js")
def main_js():
    return send_from_directory(BASE, "main.js", mimetype="application/javascript")

@app.get("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(os.path.join(BASE, "assets"), filename)

@app.get("/fonts/<path:filename>")
def fonts(filename):
    return send_from_directory(os.path.join(BASE, "fonts"), filename)

@app.get("/")
def home():
    session.setdefault("contact_form_opened", int(time.time()))
    return send_from_directory(BASE, "index.html")

@app.get("/approach")
def approach_page():
    return send_from_directory(BASE, "approach.html")

@app.get("/services")
def services_page():
    return send_from_directory(BASE, "services.html")

@app.get("/contact")
def contact_page():
    session.setdefault("contact_form_opened", int(time.time()))
    return send_from_directory(BASE, "contact.html")

@app.get("/api/csrf")
def csrf_token():
    # Flask-WTF injects the CSRF token into the session/cookie context; token is returned for JS clients.
    from flask_wtf.csrf import generate_csrf
    return jsonify(csrf_token=generate_csrf())

@app.post("/api/contact")
def contact():
    # Flask-WTF validates the X-CSRFToken header or form field before this function runs.
    now = time.time()
    ip = request.remote_addr or "unknown"
    recent = RATE[ip]
    while recent and now - recent[0] > 600:
        recent.popleft()
    if len(recent) >= 5:
        return jsonify(error="Too many requests. Please try again later."), 429
    recent.append(now)
    if not request.is_json:
        return jsonify(error="JSON request required."), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Invalid request."), 400
    # Honeypot: return a generic response; do not store bot submissions.
    if str(payload.get("website", "")).strip():
        return jsonify(ok=True), 200
    name = payload.get("name")
    email = payload.get("email")
    message = payload.get("message")
    if not all(isinstance(x, str) for x in (name, email, message)):
        return jsonify(error="Invalid field values."), 400
    name, email, message = name.strip(), email.strip(), message.strip()
    if not 2 <= len(name) <= 80 or not re.fullmatch(r"[\wÀ-ž .’'-]+", name, flags=re.UNICODE):
        return jsonify(error="Name must be 2–80 characters and contain no control characters."), 400
    if len(email) > 254 or "\r" in email or "\n" in email:
        return jsonify(error="Please provide a valid email address."), 400
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        return jsonify(error="Please provide a valid email address."), 400
    if not 10 <= len(message) <= 2000 or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in message):
        return jsonify(error="Comment must be 10–2,000 characters."), 400
    # Parameterized SQL prevents SQL injection. Do not render these values as trusted HTML.
    with sqlite3.connect(DB, timeout=5) as con:
        con.execute("INSERT INTO enquiries (name, email, message) VALUES (?, ?, ?)", (name, email, message))
    return jsonify(ok=True), 201

if __name__ == "__main__":
    # Development server only. Do not expose this server directly to the internet.
    app.run(host="127.0.0.1", port=5000, debug=False)
