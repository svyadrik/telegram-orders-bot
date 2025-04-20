from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

# Замовлення зберігаються у словниках
orders = {bread: 0 for bread in ['Батон', 'Багет', 'Калач', 'Чіабатта']}
user_orders = {}
breads = list(orders.keys())

# Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.full_name

    # Ініціалізація для нового користувача
    if user_name not in user_orders:
        user_orders[user_name] = {bread: 0 for bread in breads}

    await update.message.reply_text(
        text="👋 Вітаємо! Оберіть хліб та вкажіть кількість:",
        reply_markup=generate_keyboard(user_name)
    )

# Генерація клавіатури
def generate_keyboard(user_name):
    keyboard = [
        [InlineKeyboardButton("📦 Всього", callback_data="none"),
         InlineKeyboardButton("🧾 Моє замовлення", callback_data="none")]
    ]

    for bread in breads:
        total = orders.get(bread, 0)
        user_count = user_orders[user_name].get(bread, 0)
        keyboard.append([
            InlineKeyboardButton(bread, callback_data=f"bread_{bread}"),
            InlineKeyboardButton(str(total), callback_data=f"total_{bread}"),
            InlineKeyboardButton("➕", callback_data=f"add_{bread}"),
            InlineKeyboardButton(str(user_count), callback_data=f"my_order_{bread}"),
            InlineKeyboardButton("➖", callback_data=f"remove_{bread}")
        ])

    keyboard.append([InlineKeyboardButton("✅ Підтвердити замовлення", callback_data="confirm_order")])
    return InlineKeyboardMarkup(keyboard)

# Обробка натискань кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_name = query.from_user.full_name
    await query.answer()

    data = query.data
    if "add_" in data:
        bread = data.split("_")[1]
        user_orders[user_name][bread] += 1
        await query.edit_message_text("🔁 Оновлення...", reply_markup=generate_keyboard(user_name))

    elif "remove_" in data:
        bread = data.split("_")[1]
        if user_orders[user_name][bread] > 0:
            user_orders[user_name][bread] -= 1
        await query.edit_message_text("🔁 Оновлення...", reply_markup=generate_keyboard(user_name))

    elif "confirm_order" in data:
        for bread in breads:
            orders[bread] += user_orders[user_name].get(bread, 0)

        order_summary = "\n".join([f"{bread}: {user_orders[user_name][bread]} шт." for bread in breads])
        await query.edit_message_text("✅ Замовлення підтверджено!")
        await context.bot.send_message(chat_id=query.message.chat.id, text=f"🧾 Ваше замовлення:\n{order_summary}")

# Головна функція запуску
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ Не вказано BOT_TOKEN в .env файлі!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущено!")
    app.run_polling()

if __name__ == '__main__':
    main()
