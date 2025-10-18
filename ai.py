from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import asyncio
import threading
import time
import os

# مفاتيح API
GROQ_API_KEY = "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"
TELEGRAM_TOKEN = "8460409458:AAHPcE_QoK5QcFgliCcbirDM-68ashxsPRs"
RENDER_URL = "https://ai-bgc7.onrender.com"

# إنشاء تطبيق Flask
app = Flask(__name__)

# إنشاء تطبيق تيليجرام
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل الواردة"""
    text = update.message.text.strip()
    
    if text.startswith("ai "):
        prompt = text[3:].strip()
        if prompt:
            await update.message.reply_text("جاري المعالجة...")
            response = get_ai_response(prompt)
            await update.message.reply_text(response)
    
    elif text.startswith("emm "):
        prompt = text[4:].strip()
        if prompt:
            await update.message.reply_text("جاري المعالجة...")
            response = get_ai_response(prompt)
            await update.message.reply_text(response)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت - للجميع"""
    await update.message.reply_text(
        "مرحباً! أنا بوت الذكاء الاصطناعي.\n\n"
        "📝 **المطور:** @Mik_emm\n\n"
        "**طريقة الاستخدام:**\n"
        "• ai + سؤالك\n"
        "• emm + سؤالك\n\n"
        "**أمثلة:**\n"
        "`ai ما هو الذكاء الاصطناعي؟`\n"
        "`emm اشرح لي البرمجة`\n\n"
        "تابعنا على: https://t.me/Mik_emm"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار البوت - للجميع"""
    await update.message.reply_text("جاري اختبار البوت...")
    response = get_ai_response("قل test successful")
    await update.message.reply_text(f"✅ البوت يعمل بشكل صحيح!\nالرد: {response}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض حالة البوت - للجميع"""
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🟢 البوت يعمل\n⏰ الوقت: {current_time}")

def keep_alive():
    """نبضة حياة للحفاظ على البوت نشطاً"""
    while True:
        try:
            # إرسال طلب إلى نفس التطبيق للحفاظ على نشاطه
            requests.get(RENDER_URL, timeout=10)
            print(f"💓 نبضة حياة - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(300)  # كل 5 دقائق
        except Exception as e:
            print(f"خطأ في نبضة الحياة: {e}")
            time.sleep(300)

# إضافة handlers للتطبيق
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("test", test_command))
telegram_app.add_handler(CommandHandler("status", status_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# routes لـ Flask
@app.route('/')
def home():
    return "🤖 البوت يعمل! المطور: @Mik_emm"

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالجة طلبات Webhook"""
    json_data = request.get_json()
    update = Update.de_json(json_data, telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return 'OK'

async def setup_webhook():
    """إعداد Webhook"""
    webhook_url = f"{RENDER_URL}/webhook"
    await telegram_app.bot.set_webhook(webhook_url)
    print(f"✅ تم إعداد Webhook: {webhook_url}")

def start_bot():
    """بدء تشغيل البوت في thread منفصل"""
    async def run_bot():
        await telegram_app.initialize()
        await setup_webhook()
        await telegram_app.start()
        print("🚀 البوت يعمل الآن!")
        print("👤 المطور: @Mik_emm")
        print("🌐 Webhook مفعل...")
        
        # انتظار إلى الأبد
        while True:
            await asyncio.sleep(3600)
    
    asyncio.run(run_bot())

if __name__ == "__main__":
    # بدء نبضة الحياة في thread منفصل
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # بدء البوت في thread منفصل
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
