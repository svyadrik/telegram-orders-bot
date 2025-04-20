import logging
import os
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    ChannelPostHandler,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Авторизація Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Заказы Бутер").worksheet("Лист1")

# --- Налаштування логування ---
logging.basicConfig(level=logging.INFO)

# --- Стани розмови ---
WAITING_QUANTITY, WAITING_PHONE = range(2)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Натисніть кнопку 'Замовити' під товаром в каналі, щоб оформити замовлення.")

# --- Обробка кнопки "Замовити" ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product = query.message.caption or "без опису"
    context.user_data["product"] = product
    context.user_data["username"] = query.from_user.full_name
    context.user_data["user_id"] = query.from_user.id

    await query.message.reply_text("Скільки одиниць ви хочете замовити?")
    return WAITING_QUANTITY

# --- Кількість ---
async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quantity"] = update.message.text
    await update.message.reply_text("Залиште номер телефону для зв'язку")
    return WAITING_PHONE

# --- Телефон ---
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context.user_data["datetime"] = now

    sheet.append_row([
        now,
        context.user_data["username"],
        context.user_data["user_id"],
        context.user_data["product"],
        context.user_data["quantity"],
        context.user_data["phone"],
        now,
        "Новий"
    ])

    admin_id = 7333104516
    message = (
        f"Новий заказ:\n"
        f"👤 {context.user_data['username']}\n"
        f"📦 {context.user_data['product']} — {context.user_data['quantity']} шт.\n"
        f"📞 {context.user_data['phone']}"
    )
    keyboard = [[
        InlineKeyboardButton("✅ Підтвердити", callback_data="confirm"),
        InlineKeyboardButton("❌ Скасувати", callback_data="cancel")
    ]]
    await context.bot.send_message(chat_id=admin_id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("Дякуємо! Ваше замовлення прийнято.")
    return ConversationHandler.END

# --- Адмін підтверджує ---
async def admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm":
        await query.edit_message_text("✅ Замовлення підтверджено")
    elif query.data == "cancel":
        await query.edit_message_text("❌ Замовлення скасовано")

# --- Обробка нових постів у каналі ---
async def new_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post.caption:
        keyboard = [[InlineKeyboardButton("Сказати", callback_data="order")]]
        await context.bot.send_message(
            chat_id=update.channel_post.chat_id,
            text=f"<b>{update.channel_post.caption}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

# --- Основна функція ---
def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).webhook_url(os.getenv("WEBHOOK_URL")).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^order$")],
        states={
            WAITING_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_response, pattern="^(confirm|cancel)$"))
    app.add_handler(ChannelPostHandler(new_channel_post))

    app.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 10000)), webhook_url=os.environ["WEBHOOK_URL"])

if __name__ == '__main__':
    main()
