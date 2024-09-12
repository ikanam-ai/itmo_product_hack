import asyncio
import logging
import sys, os
from datetime import timezone, datetime
from os import getenv
import motor.motor_asyncio as motor

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import BufferedInputFile


TG_TO_SEND_COLLECTION = "send_tg"
TG_TO_RECV_COLLECTION = "recv_tg"

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

db = None
# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
bot = Bot(token=getenv("TG_BOT_API_HASH"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# Функция для записи сообщений в MongoDB
async def save_message(user_id, username, message, command=None):
    print("Received message:", message, "chat_id", user_id, "username", username, "command", command)
    new_tg = {
        "tg_id": user_id,
        "message": message,
        "username": username,
        "processed": False,
        "recv_ts": datetime.now(tz=timezone.utc)
    }

    if command:
        new_tg["command"] = command

    recv_collection = db[TG_TO_RECV_COLLECTION]
    await recv_collection.insert_one(new_tg)


async def send_tgs(recv_collection):
    tgs = recv_collection.find({"sent": False})
    async for tg in tgs:
        to_update = {"sent": True}
        try:
            dst = tg['tg_id']
            print(f"Sending TG to: {dst}")

            if "attachment" in tg:
                attachment = tg["attachment"]
                print("   Sending file", attachment["file_name"])
                file = BufferedInputFile(attachment["data"], filename=attachment["file_name"])
                await bot.send_document(dst, file)

            await bot.send_message(dst, tg["message"])
            to_update["status"] = "ok"
        except Exception as e:
            print("Got exception while sending " + str(e))
            to_update["status"] = "error: " + str(e)

        to_update["process_ts"] = datetime.now(tz=timezone.utc)
        await recv_collection.update_one({"_id": tg["_id"]},
                                         {"$set": to_update})


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    text = "Welcome to the bot!"
    await message.answer(text)
    await save_message(message.chat.id, message.chat.username, text, "/start")


@dp.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        await save_message(message.chat.id, message.chat.username, message.text)
    except Exception as e:
        print("Got exception in echo handler", e)


async def scheduler(delay: int, poll: int):
    print("Scheduler started")
    send_collection = db[TG_TO_SEND_COLLECTION]
    await asyncio.sleep(delay=delay)

    while True:
        # for chat_id in chat_ids:
        print("Scheduler Executed!")
        try:
            await send_tgs(send_collection)
        except Exception as e:
            print("Exception", e)
        print("go to sleep")
        await asyncio.sleep(delay=poll)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    global db
    print("Main started")
    mongo_addr = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    db_name = os.getenv("DB_NAME", "ai_hack")

    mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"

    db_client = motor.AsyncIOMotorClient(mongo_full_addr)
    db = db_client[db_name]

    task = asyncio.create_task(coro=scheduler(delay=8, poll=5))
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
