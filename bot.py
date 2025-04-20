import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Добавление кнопки под постом
async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.text:
        keyboard = [[InlineKeyboardButton("🛒 Замовити", callback_data="order")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=update.channel_post.chat_id,
                message_id=update.channel_post.message_id,
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Не вдалося додати кнопку: {e}")

# Обработка нажатия кнопки
async def order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Введіть, будь ласка, кількість товару:")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот працює!")

# Основной запуск приложения
async def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    if not BOT_TOKEN or not WEBHOOK_URL:
        raise ValueError("Перевірте змінні оточення BOT_TOKEN і WEBHOOK_URL")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, channel_post_handler))
    application.add_handler(CallbackQueryHandler(order_handler, pattern="^order$"))
    application.add_handler(CommandHandler("start", start))

    await application.bot.set_webhook(url=WEBHOOK_URL)
    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
