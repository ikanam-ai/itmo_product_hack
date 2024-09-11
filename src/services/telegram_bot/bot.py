import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from pymongo import MongoClient
from datetime import datetime

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Подключение к MongoDB
mongo_addr = os.getenv("MONGO_HOST", "localhost")
mongo_port = os.getenv("MONGO_PORT", "27017")
db_name = os.getenv("DB_NAME", "ai_hack")
mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
mongo_client = MongoClient(mongo_full_addr)
db = mongo_client[db_name]
tg_messages_collection = db["tg_messages"]

# Функция для записи сообщений в MongoDB
def save_message(user_id, message, direction, command=None):
    tg_messages_collection.insert_one({
        "user_id": user_id,
        "message": message,
        "direction": direction,
        "command": command,
        "timestamp": datetime.now()
    })

# Обработчики команд
async def start(update: Update, context) -> None:
    user_id = update.message.from_user.id
    text = "Welcome to the bot! Type /help to see available commands."
    await update.message.reply_text(text)
    save_message(user_id, text, "out", "/start")

async def help_command(update: Update, context) -> None:
    user_id = update.message.from_user.id
    text = "Available commands:\\n/start - Start the bot\\n/help - Show this message"
    await update.message.reply_text(text)
    save_message(user_id, text, "out", "/help")

# Обработчик простых сообщений
async def echo(update: Update, context) -> None:
    user_id = update.message.from_user.id
    message = update.message.text
    await update.message.reply_text(message)
    save_message(user_id, message, "in")
    save_message(user_id, message, "out")

# Обработка ошибок
async def error_handler(update: Update, context, error) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=error)

def main() -> None:
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == '__main__':
    main()