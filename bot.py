import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    ChannelPostHandler,
    filters,
)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Обработчик новых постов в канале
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

# Ответ на нажатие кнопки
async def order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Введіть, будь ласка, кількість товару:")

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот працює!")

# Главная функция
async def main():
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(ChannelPostHandler(channel_post_handler))
    application.add_handler(CallbackQueryHandler(order_handler, pattern="^order$"))
    application.add_handler(CommandHandler("start", start))

    webhook_url = os.getenv("WEBHOOK_URL")
    await application.bot.set_webhook(url=webhook_url)

    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=webhook_url
    )

# Старт
if __name__ == '__main__':
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
