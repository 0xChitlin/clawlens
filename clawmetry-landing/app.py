"""Minimal Flask backend for ClawMetry landing - serves static files + email subscribe via Resend.
Includes admin panel for inbox, subscribers, copy events."""
import os
import re
import json
import sqlite3
import hashlib
import logging
import sys
import time
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Flask, request, jsonify, send_from_directory, make_response, redirect, url_for

app = Flask(__name__, static_folder=".", static_url_path="")

# Force logs to stdout for Cloud Run
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("clawmetry")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "clawmetry-admin-2026")
ADMIN_DB = "/tmp/clawmetry_admin.db"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_jWLL59fj_PBctxiwxDLFiWjBZ9MiJ4ems")
RESEND_AUDIENCE_ID = os.environ.get("RESEND_AUDIENCE_ID", "48212e72-0d6c-489c-90c3-85a03a52d54c")
FROM_EMAIL = "ClawMetry <hello@clawmetry.com>"
UPDATES_EMAIL = "ClawMetry Updates <updates@clawmetry.com>"
NOTIFY_SECRET = os.environ.get("NOTIFY_SECRET", "clawmetry-notify-2026")

VIVEK_EMAIL = "vivekchand19@gmail.com"
RESEND_HEADERS = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

WELCOME_HTML = """\
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;color:#1a1a2e;">
  <div style="text-align:center;padding:32px 0 24px;">
    <span style="font-size:48px;">&#x1F99E;</span>
    <h1 style="font-size:24px;margin:12px 0 0;">Welcome to ClawMetry</h1>
  </div>
  <p>Thanks for subscribing! You're now on the list for release updates.</p>
  <p><strong>What is ClawMetry?</strong><br>
  A free, open-source real-time observability dashboard for AI agents. See token costs, cron jobs, sub-agents, memory files, and session history in one place.</p>
  <div style="background:#f4f4f8;border-radius:8px;padding:16px;margin:20px 0;font-family:'Courier New',monospace;font-size:14px;">
    <span style="color:#888;">$</span> curl -fsSL https://clawmetry.com/install.sh | bash
  </div>
  <p>
    <a href="https://github.com/vivekchand/clawmetry" style="color:#E5443A;">GitHub</a> |
    <a href="https://pypi.org/project/clawmetry/" style="color:#E5443A;">PyPI</a> |
    <a href="https://clawmetry.com" style="color:#E5443A;">Website</a>
  </p>
  <p style="color:#888;font-size:13px;margin-top:32px;border-top:1px solid #eee;padding-top:16px;">
    We'll email you on major releases only. No spam. Ever.
  </p>
</div>
"""


def _resend_post(path, payload):
    """POST to Resend API, return (ok, data)."""
    try:
        r = requests.post(f"https://api.resend.com{path}", headers=RESEND_HEADERS, json=payload, timeout=10)
        return r.status_code in (200, 201), r.json() if r.content else {}
    except Exception as e:
        return False, {"error": str(e)}


def _resend_get(path):
    """GET from Resend API."""
    try:
        r = requests.get(f"https://api.resend.com{path}", headers=RESEND_HEADERS, timeout=10)
        return r.json() if r.content else {}
    except Exception:
        return {}


def send_welcome_email(email):
    return _resend_post("/emails", {
        "from": FROM_EMAIL,
        "to": [email],
        "subject": "Welcome to ClawMetry \U0001f99e",
        "html": WELCOME_HTML,
    })


def _get_visitor_info(req):
    """Extract location/browser info from request."""
    ip = req.headers.get("X-Forwarded-For", req.headers.get("X-Real-IP", req.remote_addr))
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    ua = req.headers.get("User-Agent", "Unknown")
    referer = req.headers.get("Referer", "Direct")
    # Try IP geolocation (best-effort)
    location = "Unknown"
    try:
        geo = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2).json()
        city = geo.get("city", "")
        region = geo.get("region", "")
        country = geo.get("country_name", "")
        loc = ", ".join(filter(None, [city, region, country]))
        if loc:
            location = loc
    except Exception as e:
        log.info(f"[geo] Failed for {ip}: {e}")
    return {"ip": ip, "user_agent": ua, "referer": referer, "location": location or "Unknown"}


def _format_source(utm, referer):
    """Determine traffic source from UTM params or referer."""
    if not utm:
        if referer and referer != "Direct":
            return f"Referer: {referer}"
        return "Direct / Unknown"

    source = utm.get("utm_source", "")
    medium = utm.get("utm_medium", "")
    campaign = utm.get("utm_campaign", "")
    gclid = utm.get("gclid", "")
    gad = utm.get("gad_source", "")
    fbclid = utm.get("fbclid", "")

    if gclid or gad:
        label = "Google Ads"
        if campaign:
            label += f" ({campaign})"
        return label
    if fbclid:
        return "Facebook/Meta Ads"
    if source:
        parts = [source]
        if medium:
            parts.append(medium)
        if campaign:
            parts.append(campaign)
        return " / ".join(parts)
    return "Direct / Unknown"


def _utm_html(utm):
    """Render UTM params as HTML rows."""
    if not utm:
        return ""
    rows = ""
    for k, v in utm.items():
        if k != "landing_url":
            rows += f"<p><strong>{k}:</strong> {v}</p>"
    landing = utm.get("landing_url", "")
    if landing:
        rows += f"<p><strong>Landing URL:</strong> <a href='{landing}'>{landing[:80]}</a></p>"
    return rows


def notify_vivek(subject, body_html):
    """Send a notification email to Vivek."""
    try:
        ok, resp = _resend_post("/emails", {
            "from": FROM_EMAIL,
            "to": [VIVEK_EMAIL],
            "subject": subject,
            "html": body_html,
        })
        if not ok:
            log.info(f"[notify_vivek] Resend error: {resp}")
    except Exception as e:
        log.info(f"[notify_vivek] Exception: {e}")


def add_contact(email):
    """Add contact to Resend audience. Returns (ok, already_existed)."""
    ok, data = _resend_post(f"/audiences/{RESEND_AUDIENCE_ID}/contacts", {
        "email": email,
        "unsubscribed": False,
    })
    # Resend returns the contact even if it already exists
    return ok, data


def get_all_contacts():
    """Get all subscribed contacts from Resend audience."""
    data = _resend_get(f"/audiences/{RESEND_AUDIENCE_ID}/contacts")
    contacts = data.get("data", [])
    return [c for c in contacts if not c.get("unsubscribed")]


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email"}), 400

    log.info(f"[subscribe] New subscription: {email}")
    ok, resp = add_contact(email)
    if not ok:
        log.error(f"[subscribe] add_contact failed: {resp}")
        return jsonify({"error": "Failed to subscribe. Try again."}), 500

    send_welcome_email(email)
    log.info(f"[subscribe] Welcome email sent to {email}")

    # Small delay to avoid Resend rate limit (2 req/s)
    time.sleep(1)

    # Track in local SQLite
    try:
        visitor = _get_visitor_info(request)
        utm = data.get("utm", {})
        source = _format_source(utm, visitor['referer'])
        db = get_db()
        db.execute("INSERT INTO subscribers (email, source, location, ip, user_agent, utm_json) VALUES (?,?,?,?,?,?)",
                    (email, source, visitor['location'], visitor['ip'], visitor['user_agent'], json.dumps(utm)))
        db.commit()
        db.close()
    except Exception as e:
        log.error(f"[subscribe] DB insert error: {e}")

    # Notify Vivek (best-effort, don't block response)
    try:
        visitor = _get_visitor_info(request)
        utm = data.get("utm", {})
        source = _format_source(utm, visitor['referer'])
        notify_vivek(
            f"🦞 New ClawMetry subscriber: {email} [{source}]",
            f"""<div style="font-family:sans-serif;max-width:500px;">
            <h2>New Subscriber!</h2>
            <p><strong>Email:</strong> {email}</p>
            <p style="font-size:18px;color:#E5443A;"><strong>Source:</strong> {source}</p>
            <p><strong>Location:</strong> {visitor['location']}</p>
            <p><strong>IP:</strong> {visitor['ip']}</p>
            <p><strong>Browser:</strong> {visitor['user_agent'][:120]}</p>
            {_utm_html(utm)}
            <p><strong>Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
            </div>"""
        )
        log.info(f"[subscribe] Notification sent to Vivek for {email}")
    except Exception as e:
        log.error(f"[subscribe] Notify error: {e}", exc_info=True)

    return jsonify({"ok": True, "message": "Subscribed!"})


@app.route("/api/notify", methods=["POST"])
def notify():
    """Send version bump notification to all subscribers.

    POST /api/notify
    Headers: X-Notify-Secret: <secret>
    Body: {"version": "0.5.0", "changes": "- Feature X\\n- Fix Y", "subject": "optional custom subject"}
    """
    if request.headers.get("X-Notify-Secret") != NOTIFY_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    version = data.get("version", "")
    changes = data.get("changes", "")
    subject = data.get("subject") or f"ClawMetry {version} released \U0001f680"

    if not version:
        return jsonify({"error": "version is required"}), 400

    changes_html = "".join(f"<li>{line.lstrip('- ')}</li>" for line in changes.strip().split("\n") if line.strip())

    html = f"""\
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;color:#1a1a2e;">
  <div style="text-align:center;padding:32px 0 24px;">
    <span style="font-size:48px;">&#x1F680;</span>
    <h1 style="font-size:24px;margin:12px 0 0;">ClawMetry {version}</h1>
  </div>
  <p>A new version of ClawMetry is out!</p>
  {"<h3>What's new:</h3><ul>" + changes_html + "</ul>" if changes_html else ""}
  <div style="background:#f4f4f8;border-radius:8px;padding:16px;margin:20px 0;font-family:'Courier New',monospace;font-size:14px;">
    <span style="color:#888;">$</span> pip install --upgrade clawmetry
  </div>
  <p>
    <a href="https://github.com/vivekchand/clawmetry/releases" style="color:#E5443A;">Release Notes</a> |
    <a href="https://pypi.org/project/clawmetry/" style="color:#E5443A;">PyPI</a> |
    <a href="https://clawmetry.com" style="color:#E5443A;">Website</a>
  </p>
  <p style="color:#888;font-size:13px;margin-top:32px;border-top:1px solid #eee;padding-top:16px;">
    You're receiving this because you subscribed at clawmetry.com.
  </p>
</div>"""

    contacts = get_all_contacts()
    if not contacts:
        return jsonify({"ok": True, "sent": 0, "message": "No subscribers yet"})

    # Use Resend batch send
    emails = [c["email"] for c in contacts]
    sent = 0
    errors = []
    for email in emails:
        ok, resp = _resend_post("/emails", {
            "from": UPDATES_EMAIL,
            "to": [email],
            "subject": subject,
            "html": html,
        })
        if ok:
            sent += 1
        else:
            errors.append({"email": email, "error": resp})

    return jsonify({"ok": True, "sent": sent, "total": len(emails), "errors": errors})


@app.route("/api/copy-track", methods=["POST"])
def copy_track():
    """Track when someone copies the install command."""
    data = request.get_json(silent=True) or {}
    tab = data.get("tab", "unknown")
    command = data.get("command", "")
    utm = data.get("utm", {})
    visitor = _get_visitor_info(request)
    source = _format_source(utm, visitor['referer'])

    # Track in local SQLite
    try:
        db = get_db()
        db.execute("INSERT INTO copy_events (tab, command, source, location, ip, user_agent, utm_json) VALUES (?,?,?,?,?,?,?)",
                    (tab, command, source, visitor['location'], visitor['ip'], visitor['user_agent'], json.dumps(utm)))
        db.commit()
        db.close()
    except Exception as e:
        log.error(f"[copy-track] DB insert error: {e}")

    notify_vivek(
        f"🦞 Install command copied ({tab}) [{source}]",
        f"""<div style="font-family:sans-serif;max-width:500px;">
        <h2>Install Command Copied!</h2>
        <p><strong>Tab:</strong> {tab}</p>
        <p><strong>Command:</strong> <code>{command}</code></p>
        <p style="font-size:18px;color:#E5443A;"><strong>Source:</strong> {source}</p>
        <p><strong>Location:</strong> {visitor['location']}</p>
        <p><strong>IP:</strong> {visitor['ip']}</p>
        <p><strong>Browser:</strong> {visitor['user_agent'][:120]}</p>
        {_utm_html(utm)}
        <p><strong>Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
        </div>"""
    )

    return jsonify({"ok": True})


@app.route("/api/subscribers", methods=["GET"])
def list_subscribers():
    """List subscriber count (protected)."""
    if request.headers.get("X-Notify-Secret") != NOTIFY_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    contacts = get_all_contacts()
    return jsonify({"count": len(contacts), "subscribers": [c["email"] for c in contacts]})


##############################################################################
# SQLite Database (ephemeral on Cloud Run /tmp)
##############################################################################

def get_db():
    conn = sqlite3.connect(ADMIN_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS emails_received (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_email TEXT, to_email TEXT, subject TEXT,
        body_html TEXT, body_text TEXT,
        received_at TEXT DEFAULT (datetime('now')),
        read INTEGER DEFAULT 0, replied INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS emails_sent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_email TEXT, subject TEXT, body_html TEXT,
        sent_at TEXT DEFAULT (datetime('now')),
        in_reply_to INTEGER REFERENCES emails_received(id)
    );
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, source TEXT, location TEXT, ip TEXT,
        user_agent TEXT, utm_json TEXT,
        subscribed_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS copy_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tab TEXT, command TEXT, source TEXT, location TEXT, ip TEXT,
        user_agent TEXT, utm_json TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.close()

init_db()

##############################################################################
# Admin Auth
##############################################################################

def _admin_token():
    return hashlib.sha256(f"clawmetry-admin-{ADMIN_PASSWORD}".encode()).hexdigest()[:32]

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.cookies.get("admin_token") != _admin_token():
            return redirect("/admin")
        return f(*args, **kwargs)
    return decorated

##############################################################################
# Admin CSS
##############################################################################

ADMIN_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0B0F1A;color:#E0E0E0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6}
a{color:#E5443A;text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:960px;margin:0 auto;padding:24px 16px}
h1{font-size:28px;margin-bottom:24px;color:#fff}
h2{font-size:22px;margin-bottom:16px;color:#fff}
.nav{display:flex;gap:16px;padding:16px;background:#111627;border-bottom:1px solid #1E2540}
.nav a{color:#E0E0E0;font-weight:500;padding:6px 12px;border-radius:6px}
.nav a:hover,.nav a.active{background:#1E2540;color:#E5443A;text-decoration:none}
.card{background:#111627;border:1px solid #1E2540;border-radius:10px;padding:24px;margin-bottom:16px}
.stat{text-align:center;padding:20px}.stat .num{font-size:42px;font-weight:700;color:#E5443A}.stat .label{color:#888;font-size:14px;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;color:#888;padding:10px 12px;border-bottom:1px solid #1E2540;font-weight:500}
td{padding:10px 12px;border-bottom:1px solid #1E2540}
tr:hover{background:#0D1225}
tr.unread td{color:#fff;font-weight:500}
.badge{display:inline-block;background:#E5443A;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px;margin-left:6px}
input[type=text],input[type=password],input[type=email],textarea{width:100%;background:#0B0F1A;border:1px solid #1E2540;color:#E0E0E0;padding:10px 12px;border-radius:6px;font-size:14px;font-family:inherit}
textarea{min-height:160px;resize:vertical}
.btn{display:inline-block;background:#E5443A;color:#fff;border:none;padding:10px 24px;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500}
.btn:hover{background:#c9382f}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.muted{color:#666;font-size:13px}
.email-body{background:#0B0F1A;border:1px solid #1E2540;border-radius:8px;padding:16px;margin:16px 0;overflow-x:auto}
.flash{background:#1a3a1a;border:1px solid #2a5a2a;color:#8f8;padding:12px;border-radius:6px;margin-bottom:16px}
@media(max-width:640px){.grid3{grid-template-columns:1fr}}
</style>
"""

def _admin_page(title, content, active=""):
    nav_items = [
        ("/admin", "Dashboard", "dashboard"),
        ("/admin/inbox", "Inbox", "inbox"),
        ("/admin/subscribers", "Subscribers", "subscribers"),
        ("/admin/events", "Events", "events"),
    ]
    nav_html = "".join(f'<a href="{u}" class="{"active" if k==active else ""}">{l}</a>' for u, l, k in nav_items)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — ClawMetry Admin</title>{ADMIN_CSS}</head><body>
<nav class="nav"><a href="/admin" style="color:#E5443A;font-weight:700;margin-right:8px">🦞 Admin</a>{nav_html}
<a href="/admin/logout" style="margin-left:auto;color:#666">Logout</a></nav>
<div class="wrap">{content}</div></body></html>"""

##############################################################################
# Admin Routes
##############################################################################

@app.route("/admin")
def admin_index():
    if request.cookies.get("admin_token") != _admin_token():
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClawMetry Admin Login</title>{ADMIN_CSS}</head><body>
<div class="wrap" style="max-width:400px;margin-top:80px">
<div class="card" style="text-align:center"><h2>🦞 ClawMetry Admin</h2>
<form method="POST" action="/admin/login" style="margin-top:20px">
<input type="password" name="password" placeholder="Password" style="margin-bottom:12px" autofocus>
<button class="btn" style="width:100%">Login</button></form></div>
<p class="muted" style="text-align:center;margin-top:12px">⚠️ Data is ephemeral (Cloud Run /tmp). Resets on redeploy.</p>
</div></body></html>"""

    db = get_db()
    subs = db.execute("SELECT COUNT(*) c FROM subscribers").fetchone()["c"]
    events = db.execute("SELECT COUNT(*) c FROM copy_events").fetchone()["c"]
    unread = db.execute("SELECT COUNT(*) c FROM emails_received WHERE read=0").fetchone()["c"]
    db.close()

    return _admin_page("Dashboard", f"""
<h1>Dashboard</h1>
<div class="grid3">
<div class="card stat"><div class="num">{subs}</div><div class="label">Subscribers</div></div>
<div class="card stat"><div class="num">{events}</div><div class="label">Copy Events</div></div>
<div class="card stat"><div class="num">{unread}</div><div class="label">Unread Emails</div></div>
</div>
<p class="muted" style="margin-top:16px">⚠️ SQLite on /tmp — data resets when Cloud Run instance recycles. For persistence, migrate to Cloud SQL.</p>
""", "dashboard")

@app.route("/admin/login", methods=["POST"])
def admin_login():
    pw = request.form.get("password", "")
    if pw == ADMIN_PASSWORD:
        resp = make_response(redirect("/admin"))
        resp.set_cookie("admin_token", _admin_token(), max_age=86400*30, httponly=True, samesite="Lax")
        return resp
    return redirect("/admin")

@app.route("/admin/logout")
def admin_logout():
    resp = make_response(redirect("/admin"))
    resp.delete_cookie("admin_token")
    return resp

@app.route("/admin/inbox")
@admin_required
def admin_inbox():
    db = get_db()
    emails = db.execute("SELECT * FROM emails_received ORDER BY received_at DESC").fetchall()
    db.close()
    rows = ""
    for e in emails:
        cls = ' class="unread"' if not e["read"] else ""
        badge = '<span class="badge">NEW</span>' if not e["read"] else ""
        rows += f'<tr{cls}><td><a href="/admin/inbox/{e["id"]}">{e["subject"] or "(no subject)"}</a>{badge}</td><td>{e["from_email"]}</td><td>{e["received_at"][:16]}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="3" class="muted" style="text-align:center;padding:40px">No emails yet. Set up Resend webhook → <code>POST https://clawmetry.com/api/webhook/resend</code></td></tr>'
    return _admin_page("Inbox", f"""<h1>Inbox</h1><div class="card"><table>
<tr><th>Subject</th><th>From</th><th>Date</th></tr>{rows}</table></div>""", "inbox")

@app.route("/admin/inbox/<int:eid>")
@admin_required
def admin_email_view(eid):
    db = get_db()
    e = db.execute("SELECT * FROM emails_received WHERE id=?", (eid,)).fetchone()
    if not e:
        db.close()
        return redirect("/admin/inbox")
    if not e["read"]:
        db.execute("UPDATE emails_received SET read=1 WHERE id=?", (eid,))
        db.commit()
    replies = db.execute("SELECT * FROM emails_sent WHERE in_reply_to=? ORDER BY sent_at", (eid,)).fetchall()
    db.close()

    body = e["body_html"] or f'<pre style="white-space:pre-wrap">{e["body_text"] or "(empty)"}</pre>'
    replied_html = ""
    for r in replies:
        replied_html += f'<div class="card" style="border-color:#2a5a2a"><p class="muted">Replied {r["sent_at"][:16]}</p><div>{r["body_html"]}</div></div>'

    flash = '<div class="flash">✅ Reply sent!</div>' if request.args.get("sent") else ""
    return _admin_page(e["subject"] or "Email", f"""
<p><a href="/admin/inbox">← Inbox</a></p>
{flash}
<h1>{e["subject"] or "(no subject)"}</h1>
<p>From: <strong>{e["from_email"]}</strong> → {e["to_email"]} · {e["received_at"][:16]}</p>
<div class="email-body">{body}</div>
{replied_html}
<div class="card"><h2>Reply</h2>
<form method="POST" action="/admin/inbox/{eid}/reply">
<textarea name="body" placeholder="Type your reply..."></textarea>
<button class="btn" style="margin-top:12px">Send Reply</button></form></div>
""", "inbox")

@app.route("/admin/inbox/<int:eid>/reply", methods=["POST"])
@admin_required
def admin_reply(eid):
    db = get_db()
    e = db.execute("SELECT * FROM emails_received WHERE id=?", (eid,)).fetchone()
    if not e:
        db.close()
        return redirect("/admin/inbox")

    body_text = request.form.get("body", "").strip()
    if not body_text:
        db.close()
        return redirect(f"/admin/inbox/{eid}")

    body_html = f'<div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#333"><p>{"</p><p>".join(body_text.split(chr(10)))}</p><p style="color:#888;font-size:13px;margin-top:24px;border-top:1px solid #eee;padding-top:12px">— ClawMetry Team</p></div>'
    subject = f"Re: {e['subject']}" if e["subject"] and not e["subject"].startswith("Re:") else (e["subject"] or "Re: your email")

    ok, resp = _resend_post("/emails", {
        "from": FROM_EMAIL,
        "to": [e["from_email"]],
        "subject": subject,
        "html": body_html,
    })

    if ok:
        db.execute("INSERT INTO emails_sent (to_email, subject, body_html, in_reply_to) VALUES (?,?,?,?)",
                    (e["from_email"], subject, body_html, eid))
        db.execute("UPDATE emails_received SET replied=1 WHERE id=?", (eid,))
        db.commit()
    db.close()
    return redirect(f"/admin/inbox/{eid}?sent=1")

@app.route("/admin/subscribers")
@admin_required
def admin_subscribers():
    db = get_db()
    subs = db.execute("SELECT * FROM subscribers ORDER BY subscribed_at DESC").fetchall()
    db.close()
    rows = ""
    for s in subs:
        rows += f'<tr><td>{s["email"]}</td><td>{s["source"] or "-"}</td><td>{s["location"] or "-"}</td><td>{s["subscribed_at"][:16]}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="4" class="muted" style="text-align:center;padding:40px">No subscribers tracked yet</td></tr>'
    return _admin_page("Subscribers", f"""<h1>Subscribers</h1><div class="card"><table>
<tr><th>Email</th><th>Source</th><th>Location</th><th>Date</th></tr>{rows}</table></div>""", "subscribers")

@app.route("/admin/events")
@admin_required
def admin_events():
    db = get_db()
    evts = db.execute("SELECT * FROM copy_events ORDER BY created_at DESC").fetchall()
    db.close()
    rows = ""
    for e in evts:
        rows += f'<tr><td>{e["tab"]}</td><td>{e["command"][:50] if e["command"] else "-"}</td><td>{e["source"] or "-"}</td><td>{e["location"] or "-"}</td><td>{e["created_at"][:16]}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="5" class="muted" style="text-align:center;padding:40px">No copy events yet</td></tr>'
    return _admin_page("Events", f"""<h1>Copy Events</h1><div class="card"><table>
<tr><th>Tab</th><th>Command</th><th>Source</th><th>Location</th><th>Date</th></tr>{rows}</table></div>""", "events")

##############################################################################
# Resend Inbound Webhook
##############################################################################

@app.route("/api/webhook/resend", methods=["POST"])
def resend_webhook():
    """Receive inbound emails from Resend webhook."""
    data = request.get_json(silent=True) or {}
    log.info(f"[webhook] Resend inbound: {json.dumps(data)[:500]}")

    # Resend webhook payload: type=email.received, data={...}
    etype = data.get("type", "")
    payload = data.get("data", data)  # fallback to root if no wrapper

    from_email = payload.get("from", "") or ""
    to_email = payload.get("to", [""])[0] if isinstance(payload.get("to"), list) else payload.get("to", "")
    subject = payload.get("subject", "")
    body_html = payload.get("html", "")
    body_text = payload.get("text", "")

    if from_email or subject:
        db = get_db()
        db.execute("INSERT INTO emails_received (from_email, to_email, subject, body_html, body_text) VALUES (?,?,?,?,?)",
                    (from_email, to_email, subject, body_html, body_text))
        db.commit()
        db.close()

    return jsonify({"ok": True})

##############################################################################
# Static routes
##############################################################################

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
