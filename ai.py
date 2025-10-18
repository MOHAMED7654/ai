from flask import Flask, request
import requests
import threading
import time
import os

# مفاتيح API
GROQ_API_KEY = "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"
TELEGRAM_TOKEN = "8460409458:AAHPcE_QoK5QcFgliCcbirDM-68ashxsPRs"
RENDER_URL = "https://ai-bgc7.onrender.com"

# إنشاء تطبيق Flask
app = Flask(__name__)

def get_ai_response(message):
    """الحصول على رد من الذكاء الاصطناعي"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "حدث خطأ في الخادم."
            
    except Exception as e:
        return "تعذر الاتصال بالخدمة."

def send_telegram_message(chat_id, text):
    """إرسال رسالة إلى تيليجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=data)

def process_message(chat_id, text):
    """معالجة الرسالة وإرسال الرد"""
    if text.startswith("/start"):
        response_text = (
            "مرحباً! أنا بوت الذكاء الاصطناعي.\n\n"
            "📝 <b>المطور:</b> @Mik_emm\n\n"
            "<b>طريقة الاستخدام:</b>\n"
            "• ai + سؤالك\n"
            "• emm + سؤالك\n\n"
            "<b>أمثلة:</b>\n"
            "<code>ai ما هو الذكاء الاصطناعي؟</code>\n"
            "<code>emm اشرح لي البرمجة</code>\n\n"
            "تابعنا على: https://t.me/Mik_emm"
        )
        send_telegram_message(chat_id, response_text)
    
    elif text.startswith("/test"):
        send_telegram_message(chat_id, "جاري اختبار البوت...")
        response = get_ai_response("قل test successful")
        send_telegram_message(chat_id, f"✅ البوت يعمل بشكل صحيح!\nالرد: {response}")
    
    elif text.startswith("/status"):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_message(chat_id, f"🟢 البوت يعمل\n⏰ الوقت: {current_time}")
    
    elif text.startswith("ai "):
        prompt = text[3:].strip()
        if prompt:
            send_telegram_message(chat_id, "جاري المعالجة...")
            response = get_ai_response(prompt)
            send_telegram_message(chat_id, response)
    
    elif text.startswith("emm "):
        prompt = text[4:].strip()
        if prompt:
            send_telegram_message(chat_id, "جاري المعالجة...")
            response = get_ai_response(prompt)
            send_telegram_message(chat_id, response)

def keep_alive():
    """نبضة حياة للحفاظ على البوت نشطاً"""
    while True:
        try:
            requests.get(RENDER_URL, timeout=10)
            print(f"💓 نبضة حياة - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(300)  # كل 5 دقائق
        except Exception as e:
            print(f"خطأ في نبضة الحياة: {e}")
            time.sleep(300)

@app.route('/')
def home():
    return "🤖 البوت يعمل! المطور: @Mik_emm"

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالجة طلبات Webhook من تيليجرام"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if text:
                # معالجة الرسالة في thread منفصل
                thread = threading.Thread(target=process_message, args=(chat_id, text))
                thread.daemon = True
                thread.start()
        
        return 'OK'
    
    except Exception as e:
        print(f"خطأ في webhook: {e}")
        return 'OK'

def setup_webhook():
    """إعداد Webhook على تيليجرام"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        webhook_url = f"{RENDER_URL}/webhook"
        data = {"url": webhook_url}
        
        response = requests.post(url, json=data)
        print(f"✅ تم إعداد Webhook: {webhook_url}")
        print(f"📋 استجابة تيليجرام: {response.json()}")
    
    except Exception as e:
        print(f"❌ خطأ في إعداد Webhook: {e}")

if __name__ == "__main__":
    # إعداد Webhook
    setup_webhook()
    
    # بدء نبضة الحياة في thread منفصل
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    print("🚀 بدء تشغيل البوت...")
    print("👤 المطور: @Mik_emm")
    print("🌐 Webhook مفعل...")
    print("💓 نبضات الحياة مفعلة...")
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
