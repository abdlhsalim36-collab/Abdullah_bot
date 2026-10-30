import os, threading, io, logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from google import genai
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

def ask_gemini(text, machine_type, img=None):
    prompt = f"""
انت خبير صيانة ماكينات STOLL.
نوع الماكينة الحالي: {machine_type}
قوانينك:
- لا تسأل عن نوع الماكينة مرة ثانية - استخدم النوع المذكور.
- جاوب باختصار: السبب + الحل بخطوتين.
- اذا سأل كيف نزل رسمه: Pattern -> Load -> Select file -> Knit
سؤال المستخدم: {text}
"""
    contents = [prompt]
    if img:
        contents.append(img)
    resp = client.models.generate_content(model="gemini-3.8-flash", contents=contents)
    return resp.text

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلا بـ Abdullah-bot 🤖\n\nاختر نوع ماكينتك أول شي:",
        reply_markup=get_keyboard()
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    machine = query.data
    context.user_data['machine_type'] = machine
    await query.edit_message_text(
        f"✅ تم اختيار: {machine}\n\nهلا ابعت صورة الشاشة أو اسأل أي سؤال عن الماكينة.\n\nاذا بدك تغير النوع اكتب /start",
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        machine = context.user_data.get('machine_type', 'STOLL عام')
        await update.message.chat.send_action("typing")
        f = await context.bot.get_file(update.message.photo[-1].file_id)
        bio = io.BytesIO()
        await f.download_to_memory(bio)
        img = Image.open(bio)
        answer = ask_gemini("حللي هذه الصورة واعطي حل مختصر", machine, img)
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 غير نوع الماكينة", callback_data="change")]]))
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.text == "/start":
            return
        machine = context.user_data.get('machine_type')
        if not machine:
            await update.message.reply_text("اختار نوع الماكينة أول شي 👇", reply_markup=get_keyboard())
            return
        await update.message.chat.send_action("typing")
        answer = ask_gemini(update.message.text, machine)
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

# للزر غير نوع الماكينة
async def handle_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == "change":
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("اختار النوع الجديد:", reply_markup=get_keyboard())

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(button_click, pattern="^(?!change$).*"))
    app.add_handler(CallbackQueryHandler(handle_change, pattern="^change$"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
