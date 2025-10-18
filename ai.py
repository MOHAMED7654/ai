from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import asyncio
from datetime import datetime
import logging

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# مفاتيح API
GROQ_API_KEY = "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"
TELEGRAM_TOKEN = "8460409458:AAHPcE_QoK5QcFgliCcbirDM-68ashxsPRs"

# قائمة المشرفين (يمكن إضافة المزيد من الأرقام)
ADMINS = [8460409458]  # أضف أرقام المشرفين هنا

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
        "الاستخدام:\n"
        "• ai + سؤالك\n"
        "• emm + سؤالك\n\n"
        "تابعنا على: https://t.me/Mik_emm\n\n"
        "مثال:\n"
        "ai ما هو الذكاء الاصطناعي؟\n"
        "emm اشرح لي البرمجة"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار البوت - للمشرفين فقط"""
    user_id = update.effective_user.id
    if user_id in ADMINS:
        await update.message.reply_text("جاري اختبار البوت...")
        response = get_ai_response("قل test successful")
        await update.message.reply_text(f"✅ البوت يعمل بشكل صحيح!\nالرد: {response}")
    else:
        await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض حالة البوت - للمشرفين فقط"""
    user_id = update.effective_user.id
    if user_id in ADMINS:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(f"🟢 البوت يعمل\n⏰ الوقت: {current_time}")
    else:
        await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط.")

async def keep_alive():
    """نبضة حياة للحفاظ على البوت نشطاً"""
    while True:
        try:
            print(f"💓 نبضة حياة - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(300)  # كل 5 دقائق
        except Exception as e:
            print(f"خطأ في نبضة الحياة: {e}")

async def start_keep_alive():
    """بدء نبضة الحياة في الخلفية"""
    asyncio.create_task(keep_alive())

def main():
    """الدالة الرئيسية مع Webhook"""
    try:
        # إنشاء التطبيق
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # إضافة معالجات الأوامر
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("test", test_command))
        app.add_handler(CommandHandler("status", status_command))
        
        # إضافة معالجة الرسائل العادية
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # بدء نبضة الحياة
        app.run_polling()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    print("🚀 بدء تشغيل البوت...")
    print("📞 قناة المطور: https://t.me/Mik_emm")
    print("💓 نبضات الحياة مفعلة...")
    main()
