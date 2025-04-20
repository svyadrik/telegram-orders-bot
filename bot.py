import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# === Google Sheets setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Заказы Бутер").worksheet("Лист1")

# === Logging ===
logging.basicConfig(level=logging.INFO)

# === Global variables ===
ADMIN_ID = 7333104516

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Нажмите кнопку 'Заказать' под товаром в канале, чтобы оформить заказ.")

# === Обработка кнопки "Заказать" ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product = query.message.caption or "Без опису"
    context.user_data["product"] = product
    context.user_data["username"] = query.from_user.full_name
    context.user_data["user_id"] = query.from_user.id

    keyboard = [[InlineKeyboardButton("1", callback_data="qty_1"),
                 InlineKeyboardButton("2", callback_data="qty_2"),
                 InlineKeyboardButton("3", callback_data="qty_3")]]
    await query.message.reply_text("Скільки одиниць ви хочете замовити?", reply_markup=InlineKeyboardMarkup(keyboard))

# === Выбор количества ===
async def qty_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    qty = query.data.split("_")[1]
    context.user_data["quantity"] = qty
    await query.message.reply_text("Залиште, будь ласка, номер телефону для зв'язку")

# === Ввод телефона ===
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data["phone"] = phone
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context.user_data["datetime"] = now

    sheet.append_row([
        now,
        context.user_data["username"],
        context.user_data["user_id"],
        context.user_data["product"],
        context.user_data["quantity"],
        phone,
        now,
        "Новий"
    ])

    message = (
        f"Новий заказ:\n"
        f"👤 {context.user_data['username']}\n"
        f"📦 {context.user_data['product']} — {context.user_data['quantity']} шт.\n"
        f"📞 {phone}"
    )
    keyboard = [[
        InlineKeyboardButton("✅ Підтвердити", callback_data="confirm"),
        InlineKeyboardButton("❌ Скасувати", callback_data="cancel")
    ]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=message, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("Дякуємо! Ваше замовлення прийнято.")

# === Обработка подтверждения от админа ===
async def admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm":
        await query.edit_message_text("✅ Замовлення підтверджено")
    elif query.data == "cancel":
        await query.edit_message_text("❌ Замовлення скасовано")

# === Добавление кнопки к посту в канале ===
async def new_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        post = update.channel_post
        keyboard = [[InlineKeyboardButton("🛒 Замовити", callback_data="order")]]
        await context.bot.edit_message_reply_markup(
            chat_id=post.chat_id,
            message_id=post.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# === Main ===
def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).webhook_url(os.getenv("WEBHOOK_URL")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^order$"))
    app.add_handler(CallbackQueryHandler(qty_chosen, pattern="^qty_\\d+$"))
    app.add_handler(CallbackQueryHandler(admin_response, pattern="^(confirm|cancel)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, new_post_handler))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=os.getenv("WEBHOOK_URL")
    )

if __name__ == '__main__':
    main()
