import os, logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image
import io

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(level=logging.INFO)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    bio = io.BytesIO()
    await file.download_to_memory(bio)
    img = Image.open(bio)
    prompt = "اقرأ بيانات ماكينة STOLL من هذه الصورة واستخرج: رقم الماكينة، عدد الغرز، السرعة، والاخطاء اذا وجدت. رد بالعربي باختصار."
    response = model.generate_content([prompt, img])
    await update.message.reply_text(response.text)

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("Abdullah-bot started...")
app.run_polling()
