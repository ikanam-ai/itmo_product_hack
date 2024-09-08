from datetime import datetime
from pymongo import MongoClient
import os

# Подключение к MongoDB
mongo_addr = os.getenv("MONGO_HOST", "localhost")
mongo_port = os.getenv("MONGO_PORT", "27017")
db_name = os.getenv("DB_NAME", "ai_hack")
mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
mongo_client = MongoClient(mongo_full_addr)
db = mongo_client[db_name]

# Получение новых сообщений Telegram из базы данных
def retrieve_new_tg_message(db):
    collection = db["tg_messages"]
    return collection.find_one({"processed": False})

# Пометка сообщения как обработанного
def mark_message_processed(db, msg, status):
    collection = db["tg_messages"]
    collection.update_one({"_id": msg["_id"]}, {"$set": {"processed": True, "process_status": status, "updated": datetime.now()}})

# Отправка сообщения Telegram пользователю
def post_message(db, tg_id, msg, attachment_data=None, attachment_name=None):
    message = {
        "tg_id": tg_id,
        "msg": msg,
        "attachment_data": attachment_data,
        "attachment_name": attachment_name,
        "created": datetime.now(),
        "processed": False
    }
    collection = db["tg_messages"]
    collection.insert_one(message)