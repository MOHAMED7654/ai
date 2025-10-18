from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import asyncio
from datetime import datetime
import logging
import os

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# مفاتيح API
GROQ_API_KEY = "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"
TELEGRAM_TOKEN = "8460409458:AAHPcE_QoK5QcFgliCcbirDM-68ashxsPRs"
RENDER_URL = "https://ai-bgc7.onrender.com"  # رابط تطبيقك على Render

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
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🟢 البوت يعمل\n⏰ الوقت: {current_time}")

async def keep_alive():
    """نبضة حياة للحفاظ على البوت نشطاً"""
    while True:
        try:
            # إرسال طلب إلى نفس التطبيق للحفاظ على نشاطه
            requests.get(RENDER_URL, timeout=10)
            print(f"💓 نبضة حياة - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(300)  # كل 5 دقائق
        except Exception as e:
            print(f"خطأ في نبضة الحياة: {e}")
            await asyncio.sleep(300)

async def setup_webhook(app):
    """إعداد Webhook"""
    webhook_url = f"{RENDER_URL}/webhook"
    await app.bot.set_webhook(webhook_url)
    print(f"✅ تم إعداد Webhook: {webhook_url}")

async def main():
    """الدالة الرئيسية"""
    # إنشاء التطبيق
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("status", status_command))
    
    # إضافة معالجة الرسائل العادية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # إعداد Webhook
    await setup_webhook(app)
    
    # بدء نبضة الحياة
    asyncio.create_task(keep_alive())
    
    print("🚀 بدء تشغيل البوت...")
    print("👤 المطور: @Mik_emm")
    print("🌐 Webhook مفعل...")
    print("💓 نبضات الحياة مفعلة...")
    
    # بدء البوت (لـ Render نحتاج لتشغيل خادم ويب)
    from flask import Flask, request
    flask_app = Flask(__name__)
    
    @flask_app.route('/')
    def home():
        return "🤖 البوت يعمل! المطور: @Mik_emm"
    
    @flask_app.route('/webhook', methods=['POST'])
    async def webhook():
        """معالجة طلبات Webhook"""
        update = Update.de_json(request.get_json(), app.bot)
        await app.process_update(update)
        return 'OK'
    
    # تشغيل الخادم
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    asyncio.run(main())
