import os
import logging
import threading
import io
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Abdullah-bot Live!"

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
logging.basicConfig(level=logging.INFO)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        f = await context.bot.get_file(photo.file_id)
        bio = io.BytesIO()
        await f.download_to_memory(bio)
        img = Image.open(bio)
        res = model.generate_content(["حللي صورة ماكينة STOLL بالعربي باختصار", img])
        await update.message.reply_text(res.text)
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلا! بوت Abdullah-bot شغال 🤖 ابعت صورة")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.COMMAND, cmd_start))
    app.run_polling()
