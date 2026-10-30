import os, threading, io, logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Abdullah-bot Live!"

genai.configure(api_key=GEMINI_KEY)
logging.basicConfig(level=logging.INFO)

# جرب الموديلات من الأحدث للأقدم
def get_model():
    for name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]:
        try:
            m = genai.GenerativeModel(name)
            # اختبار سريع
            return m
        except:
            continue
    return genai.GenerativeModel("gemini-1.5-flash")

model = get_model()

SYSTEM_PROMPT = """
انت خبير ماكينات STOLL الألمانية.
جاوب دائما بالعربي باختصار ومباشر.
اذا في صورة فيها STOP او Critical Application Error او Master fatal error
اشرح انو خطأ ماستر فادح وبدو ريستارت ومسح اللوغات.
"""

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.send_action("typing")
        f = await context.bot.get_file(update.message.photo[-1].file_id)
        bio = io.BytesIO()
        await f.download_to_memory(bio)
        img = Image.open(bio)
        res = model.generate_content([SYSTEM_PROMPT + "\nحللي هذه الصورة:", img])
        await update.message.reply_text(res.text)
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.send_action("typing")
        q = update.message.text
        res = model.generate_content(SYSTEM_PROMPT + f"\nسؤال: {q}")
        await update.message.reply_text(res.text)
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلا! بوت Abdullah-bot شغال 🤖\n📸 ابعت صورة شاشة STOLL\n💬 أو اسألني أي سؤال")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.COMMAND, cmd_start))
    app.run_polling()
