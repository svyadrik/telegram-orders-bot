# bot.py
import logging
import os
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, CommandHandler, filters, ContextTypes

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Налаштування ---
TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_NAME = "Заказы Бутер"

# Підключення до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).sheet1

# --- Логування ---
logging.basicConfig(level=logging.INFO)

# --- Обробка команди /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вітаю! Надішліть повідомлення з товаром, який хочете замовити.")

# --- Обробка кнопки ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    caption = query.message.caption or "Без опису"

    keyboard = [[InlineKeyboardButton("✅ Підтвердити замовлення", callback_data=f"confirm|{caption}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"Ви хочете замовити: *{caption}*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# --- Підтвердження замовлення ---
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    if query.data.startswith("confirm"):
        _, product = query.data.split("|", 1)

        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        sheet.append_row([
            datetime.today().strftime("%d.%m.%Y"),
            user.full_name,
            user.id,
            product,
            1,
            "",
            now,
            "Новий"
        ])

        await query.answer("Замовлення прийнято!")
        await query.edit_message_text("✅ Ваше замовлення збережено.")

# --- Автоматичне додавання кнопки ---
async def handle_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        post = update.channel_post
        keyboard = [[InlineKeyboardButton("🛒 Замовити", callback_data="order")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=post.chat_id,
            text="⬇️ Натисніть кнопку, щоб замовити:",
            reply_to_message_id=post.message_id,
            reply_markup=reply_markup
        )

# --- Запуск ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(confirm, pattern="^confirm"))
    app.add_handler(CallbackQueryHandler(button, pattern="^order"))
    app.add_handler(MessageHandler(filters.ALL, handle_post))

    app.run_polling()

if __name__ == '__main__':
    main()
