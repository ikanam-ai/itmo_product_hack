from telethon import TelegramClient, events
import motor.motor_asyncio as motor
import pymongo
import asyncio, os
from datetime import datetime, timezone, timedelta

# Use your own values from my.telegram.org
api_id = 123456
api_hash = 'hash'

TG_TO_SEND_COLLECTION = "send_tg"
TG_TO_RECV_COLLECTION = "recv_tg"

# tgm structure:
# message
# optional attachment { data, file_name }
# tg_id
# for outgoing tgs
#   sent
#   status
#   process_ts
# for incoming tgs
#   processed
#   recv_ts


client = TelegramClient('anon', api_id, api_hash)


async def post_message(db, message):
    recv_collection = db[TG_TO_RECV_COLLECTION]
    new_tg = {
        "processed": False,
        "recv_ts": datetime.now(tz=timezone.utc),
        "tg_id": message.sender.username,
        "message": message.text
    }
    await recv_collection.insert_one(new_tg)


@client.on(events.NewMessage)
async def new_message_event_handler(event):
    print("new message:", event.raw_text, ", from ", event.message.sender.username)
    await post_message(event.client.db, event.message)


async def send_tgs(recv_collection):
    tgs = recv_collection.find({"sent": False})
    async for tg in tgs:
        to_update = {"sent": True}
        try:
            dst = tg['tg_id']
            print(f"Sending TG to: {dst}")

            if "attachment" in tg:
                print("   Sending file", attachment["file_name"])
                attachment = tg["attachment"]
                f_path = "/tmp/" + attachment["file_name"]
                with open(f_path, "wb") as fd:
                    fd.write(attachment["data"])
                await client.send_file(dst, file=f_path)
                os.unlink(f_path)

            await client.send_message(dst, tg["message"])
            to_update["status"] = "ok"
        except Exception as e:
            print("Got exception while sending " + str(e))
            to_update["status"] = "error: " + str(e)

        to_update["process_ts"] = datetime.now(tz=timezone.utc)
        recv_collection.update_one({"_id": tg["_id"]},
                                   {"$set": to_update})


async def main():
    mongo_addr = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    db_name = os.getenv("DB_NAME", "ai_hack")

    mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"

    db_client = motor.AsyncIOMotorClient(mongo_full_addr)
    db = db_client[db_name]
    client.db = db
    recv_collection = db[TG_TO_RECV_COLLECTION]

    print("Main started")

    cursor = recv_collection.find().sort("_id", pymongo.DESCENDING).limit(1)
    last_tg = await cursor.to_list(1)
    # if len(last_tg) > 0:
    #     last_ts = last_tg[0]["recv_ts"]
    # else:
    last_ts = datetime.now(tz=timezone.utc)

    print("Last recv ts", last_ts)
    new_messages = []
    async for dialog in client.iter_dialogs():
        dialog_messages = []
        async for message in client.iter_messages(dialog.id):
            if message.date < last_ts:
                break
            # skip ours messages
            if message.sender_id != dialog.id:
                continue
            dialog_messages.append(message)
        new_messages.extend(dialog_messages[::-1])

    for msg in new_messages:
        print("Posting old message", msg.text)
        await post_message(db, msg)

    send_collection = db[TG_TO_SEND_COLLECTION]
    print("Going into DB polling mode")
    while True:
        await send_tgs(send_collection)
        await asyncio.sleep(1)


client.start()
client.loop.run_until_complete(main())
