from datetime import datetime
from pymongo import MongoClient
import os
import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext


# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Подключение к MongoDB
# mongo_addr = os.getenv("MONGO_HOST", "localhost")   - убрать
# mongo_port = os.getenv("MONGO_PORT", "27017")
# db_name = os.getenv("DB_NAME", "ai_hack")
mongo_addr = os.getenv("MONGO_HOST")
mongo_port = os.getenv("MONGO_PORT")
db_name = os.getenv("DB_NAME")
mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
mongo_client = MongoClient(mongo_full_addr)
db = mongo_client[db_name]

# Коллекция отправленных сообщений
tg_messages_collection_posted = db["tg_messages_posted"]
# Коллекция полученных сообщений
tg_messages_collection_received = db["tg_messages_received"]

# Бот
telegram_token = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=telegram_token)


# Отправка сообщения конкретному пользователю
async def send_message_to_id(id: str, text: str):
    await bot.send_message(chat_id=id, text=text)



# Получение новых сообщений от пользователя и занесение их в БД
# ___Должен вернуть from - id___
def retrieve_new_tg_message(db):
    collection = db["tg_messages_received"]
    return collection.find_one({"processed": False})


# Пометка сообщения как обработанного
def mark_message_processed(db, msg, status):
    collection = db["tg_messages_received"]
    collection.update_one({"_id": msg["_id"]}, {"$set": {"processed": True, "process_status": status, "updated": datetime.now()}})


# Отправка сообщения Telegram пользователю
# ___Добавить логику с отсылкой attachment (pdf)___
# def post_message(db, tg_id, msg, attachment_data=None, attachment_name=None):
#     message = {
#         "tg_id": tg_id,
#         "msg": msg,
#         "attachment_data": attachment_data,
#         "attachment_name": attachment_name,
#         "created": datetime.now(),
#         "processed": False
#     }
#     collection = db["tg_messages"]
#     collection.insert_one(message)

async def post_message(db, tg_id, msg, attachment_data=None, attachment_name=None):
    try:
        await bot.send_message(chat_id=tg_id, text=msg)
        if attachment_data and attachment_name:
            await bot.send_document(chat_id=tg_id, document=attachment_data.read(), filename=attachment_name)
        message = {
            "tg_id": tg_id,
            "msg": msg,
            "attachment_data": attachment_data,
            "attachment_name": attachment_name,
            "created": datetime.now(),
            "processed": False
        }
        collection = db["tg_messages_posted"]
        collection.insert_one(message)
    except Exception as e:
        logger.error(f"Failed to send message to {tg_id}: {e}")

def save_message(user_id, message, direction, command=None):
    tg_messages_collection_received.insert_one({
        "user_id": user_id,
        "message": message,
        "direction": direction,
        "command": command,
        "timestamp": datetime.now()
    })


# Обработчики команд
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = "Welcome to the bot! Type /help to see available commands."
    await update.message.reply_text(text)
    save_message(user_id, text, "out", "/start")

# Обработка ошибок
async def error_handler(context: CallbackContext, error) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=error)

def main() -> None:
    application = ApplicationBuilder().token(telegram_token).build()

    application.add_handler(CommandHandler("start", start))

    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == '__main__':
    main()

# Ниже старая версия


# TG_TO_SEND_COLLECTION = "send_tg"
# TG_TO_RECV_COLLECTION = "recv_tg"
#
#
# def retrieve_new_tg_message(db):
#     collection = db[TG_TO_RECV_COLLECTION]
#     return collection.find_one({"processed": False})
#
#
# def mark_message_processed(db, msg, process_status):
#     collection = db[TG_TO_RECV_COLLECTION]
#     collection.update_one(
#         {"_id": msg["_id"]},
#         {"$set": {"processed": True, "process_status": process_status}},
#     )
#
#
# def post_message(db, tg_id, msg, attachment_data=None, attachment_name=None):
#     collection = db[TG_TO_SEND_COLLECTION]
#     email = {
#         "tg_id": tg_id,
#         "message": msg,
#         "sent": False,
#     }
#     if attachment_data:
#         email["attachment"] = {"data": attachment_data, "file_name": attachment_name}
#
#     collection.insert_one(email)
#
#
# # def test_tg_server():
# #     import os, pymongo
# #     from bson.binary import Binary
# #
# #     mongo_addr = os.getenv("MONGO_HOST", "localhost")
# #     mongo_port = os.getenv("MONGO_PORT", "27017")
# #     db_name = os.getenv("DB_NAME", "ai_hack")
# #
# #     mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
# #     print("Connecting to MongoDB " + mongo_full_addr)
# #     mongo_client = pymongo.MongoClient(mongo_full_addr)
# #     db = mongo_client[db_name]
# #
# #     #post_message(db, "me", "posted message")
# #
# #     # with open("presentation.pdf", "rb") as fd:
# #     #     data = Binary(fd.read())
# #     # post_message(db, "me", "msg with attachment", attachment_data=data, attachment_name="attached_file.pdf")
# #     #
# #     # tg = retrieve_new_tg_message(db)
# #     # print(tg)
# #     # mark_message_processed(db, tg, "ok")
# #
# #
# # if __name__ == "__main__":
# #     test_tg_server()