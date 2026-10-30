import os, threading, io, logging, time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from google import genai
from google.genai import types
from PIL import Image

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Abdullah-bot Live!"

client = genai.Client(api_key=GEMINI_KEY)
logging.basicConfig(level=logging.INFO)

MACHINES = ["CMS 330", "CMS 530", "CMS 830", "CMS 530 HP", "ADF 530", "ADF 830", "OKC"]

def get_keyboard():
    buttons = [[InlineKeyboardButton(m, callback_data=m)] for m in MACHINES]
    buttons.append([InlineKeyboardButton("ما بعرف / عام", callback_data="عام")])
    return InlineKeyboardMarkup(buttons)

def resize_image(img):
    # تصغير الصورة لتصير سريعة - من 5MB لـ 200KB
    img.thumbnail((800, 800))
    return img

def ask_gemini(text, machine_type, img=None):
    prompt = f"خبير STOLL {machine_type}. جاوب باختصار جدا: سبب + حل سطرين. سؤال: {text}"
    contents = [prompt]
    if img:
        contents.append(resize_image(img))

    # الموديلات من الأسرع للأبطأ - بنبلش بالأسرع
    models = ["gemini-2.0-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash"]
    
    for model_name in models:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    # اطفاء التفكير العميق للسرعة
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    max_output_tokens=300,  # جواب قصير = أسرع
                    temperature=0.2
                )
            )
            return resp.text
        except Exception as e:
            if "503" in str(e) or "404" in str(e) or "UNAVAILABLE" in str(e):
                continue
            if model_name == models[-1]:
                return "جرب بعد 10 ثواني، السيرفر مضغوط"
            continue
    return "جرب مرة تانية"

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلا 🤖 اختر نوع ماكينتك:", reply_markup=get_keyboard())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    machine = query.data
    if machine == "change":
        await query.message.reply_text("اختار النوع الجديد:", reply_markup=get_keyboard())
        return
    context.user_data['machine_type'] = machine
    await query.edit_message_text(f"✅ {machine}\n\nابعت صورة أو اسأل: كيف نزل رسمه؟")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    machine = context.user_data.get('machine_type')
    if not machine:
        await update.message.reply_text("اختار النوع أول شي:", reply_markup=get_keyboard())
        return
    await update.message.chat.send_action("typing")
    f = await context.bot.get_file(update.message.photo[-1].file_id)
    bio = io.BytesIO()
    await f.download_to_memory(bio)
    img = Image.open(bio)
    ans = ask_gemini("حللي الصورة", machine, img)
    await update.message.reply_text(ans)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    machine = context.user_data.get('machine_type')
    if not machine:
        await update.message.reply_text("اختار النوع أول شي:", reply_markup=get_keyboard())
        return
    await update.message.chat.send_action("typing")
    ans = ask_gemini(update.message.text, machine)
    await update.message.reply_text(ans)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
