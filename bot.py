import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ChannelPostHandler
)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Кнопка под каждым постом
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

# Запуск бота (БЕЗ asyncio.run)
def main():
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(ChannelPostHandler(channel_post_handler))
    application.add_handler(CallbackQueryHandler(order_handler, pattern="^order$"))
    application.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Бот працює!")))

    webhook_url = os.getenv("WEBHOOK_URL")

    # Запускаем Webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    main()
