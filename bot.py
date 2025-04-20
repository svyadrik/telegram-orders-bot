import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import gspread
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

gc = gspread.service_account(filename='google-credentials.json')
sheet = gc.open_by_key(os.getenv("SHEET_ID")).sheet1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Напишите сюда, если хотите оформить заказ или задать вопрос!")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = query.data.replace("order_", "")
    user = query.from_user
    context.user_data["product"] = product
    await context.bot.send_message(
        chat_id=user.id,
        text=f"🛍 Вы хотите заказать: *{product}*

Сколько штук?",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text.strip()
    if "product" not in context.user_data:
        await update.message.reply_text("Сначала нажмите кнопку 'Заказать' под товаром в канале.")
        return
    if "quantity" not in context.user_data:
        context.user_data["quantity"] = text
        await update.message.reply_text("📞 Укажите, пожалуйста, ваш телефон:")
        return
    if "phone" not in context.user_data:
        context.user_data["phone"] = text
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [
            now,
            user.full_name,
            user.id,
            context.user_data["product"],
            context.user_data["quantity"],
            context.user_data["phone"],
            now,
            "В обработке"
        ]
        sheet.append_row(row)
        admin_chat_id = os.getenv("ADMIN_ID")
        msg = (
            f"🆕 Новый заказ:
"
            f"👤 {user.full_name}
"
            f"📦 {context.user_data['product']}
"
            f"🔢 {context.user_data['quantity']}
"
            f"📞 {context.user_data['phone']}
"
            f"🕓 {now}"
        )
        buttons = [[
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{user.id}_{now}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{user.id}_{now}")
        ]]
        await context.bot.send_message(chat_id=admin_chat_id, text=msg, reply_markup=InlineKeyboardMarkup(buttons))
        await update.message.reply_text("✅ Ваш заказ принят! Мы скоро свяжемся с вами.")

def main():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^order_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.run_polling()

if __name__ == '__main__':
    main()