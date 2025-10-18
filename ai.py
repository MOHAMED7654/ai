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
    """الحصول على رد من الذكاء الاصطناعي مع تحسين للبرمجة"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # تحسين الprompt لأسئلة البرمجة
        improved_message = message
        programming_keywords = ['c', 'سي', 'برمجة', 'كود', 'برنامج', 'code', 'programming']
        
        if any(keyword in message.lower() for keyword in programming_keywords):
            improved_message = f"{message}\n\nيرجى تقديم إجابة واضحة ومفيدة مع أمثلة عملية إذا أمكن."
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": improved_message}],
            "temperature": 0.7,
            "max_tokens": 2000  # زيادة للأسئلة البرمجية
        }
        
        print(f"📤 إرسال طلب إلى Groq: {message}")
        response = requests.post(url, json=data, headers=headers, timeout=35)
        print(f"📥 استجابة Groq: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            print(f"✅ الرد المستلم: {response_text[:100]}...")
            return response_text
        else:
            print(f"❌ خطأ في الخادم: {response.status_code}")
            
            # محاولة نموذج بديل
            data["model"] = "mixtral-8x7b-32768"
            response = requests.post(url, json=data, headers=headers, timeout=35)
            
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
        response = requests.post(url, json=data, timeout=15)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة: {e}")
        return False

def process_message(chat_id, text, chat_type):
    """معالجة الرسالة وإرسال الرد"""
    print(f"🔍 معالجة رسالة من {chat_id} في {chat_type}: {text}")
    
    try:
        text_lower = text.lower().strip()
        
        # في المحادثات الخاصة
        if chat_type == "private":
            # أوامر التحكم
            if text_lower in ["تشغيل", "تفعيل", "ابدأ", "/on"]:
                user_states[chat_id] = True
                send_telegram_message(chat_id, 
                    "✅ <b>تم تفعيل الوضع الدائم!</b>\n\n"
                    "الآن يمكنك إرسال أي رسالة وسأرد عليك مباشرة بدون استخدام 'ai' أو 'emm'.\n\n"
                    "لإيقاف الرد التلقائي: اكتب <code>ايقاف</code>"
                )
                return
            
            elif text_lower in ["ايقاف", "إيقاف", "توقف", "/off"]:
                user_states[chat_id] = False
                send_telegram_message(chat_id, 
                    "🛑 <b>تم إيقاف الوضع الدائم.</b>\n\n"
                    "للاستخدام العادي: اكتب <code>ai</code> أو <code>emm</code> ثم رسالتك"
                )
                return
            
            # إذا كان الوضع الدائم مفعل
            elif user_states.get(chat_id, False):
                send_telegram_message(chat_id, "⏳ جاري المعالجة...")
                response = get_ai_response(text)
                send_telegram_message(chat_id, response)
                return
            
            # الأوامر العادية
            elif text_lower.startswith("ai ") or text_lower.startswith("emm "):
                # تحديد البادئة واستخراج النص
                if text_lower.startswith("ai "):
                    prompt = text[3:].strip()
                else:
                    prompt = text[4:].strip()
                
                if prompt:
                    send_telegram_message(chat_id, "⏳ جاري المعالجة...")
                    response = get_ai_response(prompt)
                    send_telegram_message(chat_id, response)
                else:
                    send_telegram_message(chat_id, "❌ يرجى كتابة رسالة بعد 'ai' أو 'emm'")
                return
            
            elif text_lower == "/start":
                response_text = (
                    "🚀 <b>مرحباً! أنا بوت الذكاء الاصطناعي</b>\n\n"
                    "📝 <b>المطور:</b> @Mik_emm\n\n"
                    "💬 <b>في المحادثات الخاصة:</b>\n"
                    "• <code>ai سؤالك</code> - رد فوري\n"
                    "• <code>emm سؤالك</code> - رد فوري\n"
                    "• <code>تشغيل</code> - تفعيل الرد التلقائي\n"
                    "• <code>ايقاف</code> - إيقاف الرد التلقائي\n\n"
                    "👥 <b>في المجموعات:</b>\n"
                    "• <code>ai سؤالك</code> - للجميع\n"
                    "• <code>emm سؤالك</code> - للجميع\n\n"
                
                    "📢 <b>تابعنا:</b> https://t.me/Mik_emm"
                )
                send_telegram_message(chat_id, response_text)
                return
            
            elif text_lower == "/test":
                send_telegram_message(chat_id, "🔍 جاري اختبار البوت والبرمجة...")
                response = get_ai_response("أكتب كود بسيط في لغة C لجمع عددين وإظهار النتيجة")
                send_telegram_message(chat_id, f"✅ <b>نتيجة الاختبار:</b>\n{response}")
                return
            
            elif text_lower == "/status":
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                status = "🟢 مفعل" if user_states.get(chat_id, False) else "🔴 متوقف"
                send_telegram_message(chat_id, 
                    f"<b>حالة البوت:</b>\n"
                    f"• الوضع الدائم: {status}\n"
                    f"• ⏰ الوقت: {current_time}\n"
                    f"• 👤 المستخدم: {chat_id}"
                )
                return
            
            elif text_lower == "/c":
                send_telegram_message(chat_id, 
                    "💻 <b>مساعد لغة C</b>\n\n"
                    "اسألني عن:\n"
                    "• أساسيات لغة C\n"
                    "• الأكواد والبرامج\n"
                    "• حلول المشاكل\n"
                    "• شرح المفاهيم\n\n"
                    "<b>أمثلة:</b>\n"
                    "<code>ai ما هي لغة C</code>\n"
                    "<code>emm اكتب كود hello world</code>\n"
                    "<code>ai شرح المؤشرات في C</code>"
                )
                return
            
            else:
                # إذا لم يكن أمر معروف، نعطي التعليمات
                send_telegram_message(chat_id,
                    "🤖 <b>طريقة الاستخدام:</b>\n\n"
                    "💬 <b>للرد الفوري:</b>\n"
                    "<code>ai سؤالك</code> أو <code>emm سؤالك</code>\n\n"
                    "🔄 <b>للتفعيل الدائم:</b>\n"
                    "اكتب <code>تشغيل</code> ثم أرسل أي رسالة\n\n"
                    "💻 <b>لأسئلة لغة C:</b>\n"
                    "<code>ai اشرح لغة C</code>\n"
                    "<code>emm كود C بسيط</code>\n"
                    "<code>/c</code> - للمساعدة في C\n\n"
                    "📚 <b>أنت تدرس C الآن، يمكنني مساعدتك!</b>"
                )
                return
        
        # في المجموعات
        else:
            if text_lower.startswith("ai ") or text_lower.startswith("emm "):
                # تحديد البادئة واستخراج النص
                if text_lower.startswith("ai "):
                    prompt = text[3:].strip()
                else:
                    prompt = text[4:].strip()
                
                if prompt:
                    send_telegram_message(chat_id, "⏳ جاري المعالجة...")
                    response = get_ai_response(prompt)
                    send_telegram_message(chat_id, response)
                else:
                    send_telegram_message(chat_id, "❌ يرجى كتابة رسالة بعد 'ai' أو 'emm'")
                return
            
            elif text_lower == "/start":
                send_telegram_message(chat_id,
                    "👋 <b>أهلاً بالجميع!</b>\n\n"
                    "🤖 أنا بوت الذكاء الاصطناعي\n\n"
                    "📝 <b>طريقة الاستخدام في المجموعة:</b>\n"
                    "• <code>ai سؤالك</code>\n"
                    "• <code>emm سؤالك</code>\n\n"
                 
                    "📢 <b>المطور:</b> @Mik_emm"
                )
                return
    
    except Exception as e:
        error_msg = f"❌ خطأ في المعالجة: {str(e)}"
        print(error_msg)
        send_telegram_message(chat_id, "⚠️ حدث خطأ أثناء المعالجة. حاول مرة أخرى.")

def keep_alive():
    """نبضة حياة للحفاظ على البوت نشطاً"""
    while True:
        try:
            response = requests.get(RENDER_URL, timeout=10)
            print(f"💓 نبضة حياة - {time.strftime('%Y-%m-%d %H:%M:%S')} - الحالة: {response.status_code}")
        except Exception as e:
            print(f"⚠️ خطأ في نبضة الحياة: {e}")
        time.sleep(300)  # كل 5 دقائق

@app.route('/')
def home():
    return "🤖 البوت يعمل! المطور: @Mik_emm - متخصص في مساعدة طلاب لغة C"

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالجة طلبات Webhook من تيليجرام"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            chat_type = message['chat']['type']
            
            if text:
                print(f"📩 طلب Webhook: {chat_type} - {text[:50]}...")
                # معالجة الرسالة في thread منفصل
                thread = threading.Thread(target=process_message, args=(chat_id, text, chat_type))
                thread.daemon = True
                thread.start()
        
        return 'OK'
    
    except Exception as e:
        print(f"❌ خطأ في webhook: {e}")
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
    print("💻 تحسينات لغة C مضاف...")
    print("🔄 الوضع الدائم متاح في الخاص...")
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
