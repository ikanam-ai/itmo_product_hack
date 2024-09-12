TG_TO_SEND_COLLECTION = "send_tg"
TG_TO_RECV_COLLECTION = "recv_tg"


def retrieve_new_tg_message(db):
    collection = db[TG_TO_RECV_COLLECTION]
    return collection.find_one({"processed": False})


def mark_message_processed(db, msg, process_status):
    collection = db[TG_TO_RECV_COLLECTION]
    collection.update_one(
        {"_id": msg["_id"]},
        {"$set": {"processed": True, "process_status": process_status}},
    )


def post_message(db, tg_id, msg, attachment_data=None, attachment_name=None):
    collection = db[TG_TO_SEND_COLLECTION]
    email = {
        "tg_id": tg_id,
        "message": msg,
        "sent": False,
    }
    if attachment_data:
        email["attachment"] = {"data": attachment_data, "file_name": attachment_name}

    collection.insert_one(email)


# def test_tg_server():
#     import os, pymongo
#     from bson.binary import Binary
#
#     mongo_addr = os.getenv("MONGO_HOST", "localhost")
#     mongo_port = os.getenv("MONGO_PORT", "27017")
#     db_name = os.getenv("DB_NAME", "ai_hack")
#
#     mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
#     print("Connecting to MongoDB " + mongo_full_addr)
#     mongo_client = pymongo.MongoClient(mongo_full_addr)
#     db = mongo_client[db_name]
#
#     #post_message(db, 5253488934, "posted message")
#
#     with open("presentation.pdf", "rb") as fd:
#         data = Binary(fd.read())
#     post_message(db, 5253488934, "msg with attachment", attachment_data=data, attachment_name="attached_file.pdf")
#     #
#     # tg = retrieve_new_tg_message(db)
#     # print(tg)
#     # mark_message_processed(db, tg, "ok")
#
#
# if __name__ == "__main__":
#     test_tg_server()
