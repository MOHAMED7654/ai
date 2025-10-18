from flask import Flask, request
import requests
import threading
import time
import os
import json

# مفاتيح API
GROQ_API_KEY = "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"
TELEGRAM_TOKEN = "8460409458:AAHPcE_QoK5QcFgliCcbirDM-68ashxsPRs"
RENDER_URL = "https://ai-bgc7.onrender.com"

# إنشاء تطبيق Flask
app = Flask(__name__)

# تخزين حالة المستخدمين
user_states = {}

def get_ai_response(message):
    """الحصول على رد من الذكاء الاصطناعي"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # العودة للنموذج الأساسي مع تحسينات
        data = {
            "model": "llama-3.1-8b-instant",  # النموذج الأساسي الموثوق
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 1500,
            "top_p": 1
        }
        
        print(f"📤 إرسال طلب إلى Groq: {message}")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"📥 استجابة Groq: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            print(f"✅ الرد المستلم: {response_text[:100]}...")
            return response_text
        else:
            print(f"❌ خطأ في الخادم: {response.status_code} - {response.text}")
            
            # محاولة نموذج بديل إذا فشل الأول
            data["model"] = "mixtral-8x7b-32768"
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content']
                print(f"✅ الرد المستلم (النموذج البديل): {response_text[:100]}...")
                return response_text
            else:
                return "⚠️ حدث خطأ في الخادم. حاول مرة أخرى."
            
    except requests.exceptions.Timeout:
        return "⏰ انتهت مهلة الاتصال. جرب سؤالاً أقصر."
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return "⚠️ تعذر الاتصال بالخدمة."

def send_telegram_message(chat_id, text):
    """إرسال رسالة إلى تيليجرام"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة: {e}")
        return False

def process_message(chat_id, text, chat_type):
    """معالجة الرسالة وإرسال الرد"""
    print(f"🔍 معالجة رسالة من {chat_id}: {text}")
    
    try:
        text_lower = text.lower().strip()
        
        # في المحادثات الخاصة
        if chat_type == "private":
            if text_lower in ["تشغيل", "تفعيل", "ابدأ"]:
                user_states[chat_id] = True
                send_telegram_message(chat_id, "✅ تم تفعيل الوضع الدائم! الآن أرسل أي رسالة وسأرد مباشرة.")
                return
            
            elif text_lower in ["ايقاف", "إيقاف", "توقف"]:
                user_states[chat_id] = False
                send_telegram_message(chat_id, "🛑 تم إيقاف الوضع الدائم.")
                return
            
            # الوضع الدائم
            elif user_states.get(chat_id, False):
                send_telegram_message(chat_id, "⏳ جاري المعالجة...")
                response = get_ai_response(text)
                send_telegram_message(chat_id, response)
                return
            
            # الأوامر العادية
            elif text_lower.startswith("ai ") or text_lower.startswith("emm "):
                if text_lower.startswith("ai "):
                    prompt = text[3:].strip()
                else:
                    prompt = text[4:].strip()
                
                if prompt:
                    send_telegram_message(chat_id, "⏳ جاري المعالجة...")
                    response = get_ai_response(prompt)
                    send_telegram_message(chat_id, response)
                return
            
            elif text_lower == "/start":
                send_telegram_message(chat_id,
                    "🚀 <b>مرحباً! أنا بوت الذكاء الاصطناعي</b>\n\n"
                    "📝 <b>المطور:</b> @Mik_emm\n\n"
                    "💬 <b>الاستخدام:</b>\n"
                    "• ai سؤالك\n"
                    "• emm سؤالك\n"
                    "• تشغيل - للوضع الدائم\n"
                    "• ايقاف - لإيقاف الدائم\n\n"
                    "💻 <b>للبرمجة:</b>\n"
                    "<code>ai كود C لجمع عددين</code>\n"
                    "<code>emm شرح Python</code>\n\n"
                    "📢 <b>القناة:</b> @Mik_emm"
                )
                return
            
            elif text_lower == "/test":
                send_telegram_message(chat_id, "🔍 جاري اختبار البوت...")
                response = get_ai_response("أكتب كود بسيط في C لجمع عددين وأظهر النتيجة")
                send_telegram_message(chat_id, f"<b>النتيجة:</b>\n{response}")
                return
        
        # في المجموعات
        else:
            if text_lower.startswith("ai ") or text_lower.startswith("emm "):
                if text_lower.startswith("ai "):
                    prompt = text[3:].strip()
                else:
                    prompt = text[4:].strip()
                
                if prompt:
                    send_telegram_message(chat_id, "⏳ جاري المعالجة...")
                    response = get_ai_response(prompt)
                    send_telegram_message(chat_id, response)
                return
            
            elif text_lower == "/start":
                send_telegram_message(chat_id,
                    "👋 <b>أهلاً بالجميع!</b>\n\n"
                    "🤖 بوت الذكاء الاصطناعي\n\n"
                    "📝 <b>الاستخدام:</b>\n"
                    "• ai سؤالك\n"
                    "• emm سؤالك\n\n"
                    "📢 <b>المطور:</b> @Mik_emm"
                )
                return
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        send_telegram_message(chat_id, "⚠️ حدث خطأ. حاول مرة أخرى.")

def keep_alive():
    """نبضة حياة"""
    while True:
        try:
            requests.get(RENDER_URL, timeout=10)
            print(f"💓 نبضة حياة - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            pass
        time.sleep(300)

@app.route('/')
def home():
    return "🤖 البوت يعمل! @Mik_emm"

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالجة Webhook"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            chat_type = message['chat']['type']
            
            if text:
                thread = threading.Thread(target=process_message, args=(chat_id, text, chat_type))
                thread.daemon = True
                thread.start()
        
        return 'OK'
    
    except Exception as e:
        print(f"❌ خطأ في webhook: {e}")
        return 'OK'

def setup_webhook():
    """إعداد Webhook"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        webhook_url = f"{RENDER_URL}/webhook"
        data = {"url": webhook_url}
        
        response = requests.post(url, json=data)
        print(f"✅ تم إعداد Webhook: {webhook_url}")
        print(f"📋 الاستجابة: {response.json()}")
    
    except Exception as e:
        print(f"❌ خطأ في Webhook: {e}")

if __name__ == "__main__":
    setup_webhook()
    
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    print("🚀 البوت يعمل...")
    print("👤 المطور: @Mik_emm")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
