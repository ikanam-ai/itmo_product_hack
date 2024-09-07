import os, sys
import pymongo
from bson.binary import Binary

EMAIL_TO_SEND_COLLECTION = "send_email"
EMAIL_TO_RECV_COLLECTION = "recv_email"


def post_email(db, from_name, to_name, from_email, to_email, subject, plain_body=None, html_body=None,
               attachment_data=None, attachment_name="no_name"):

    collection = db[EMAIL_TO_SEND_COLLECTION]
    email = {
        "subject": subject,
        "from": from_name,
        "to": to_name,
        "from_email": from_email,
        "to_email": to_email,
        "sent": False
    }
    if plain_body:
        email["plain_part"] = plain_body
    if html_body:
        email["html_part"] = html_body
    if attachment_data:
        email["attachment"] = {
            "data": attachment_data,
            "file_name": attachment_name
        }

    if not plain_body and not html_body:
        raise Exception("Email must have some body")

    collection.insert_one(email)


def retrieve_new_email(db):
    collection = db[EMAIL_TO_RECV_COLLECTION]
    return collection.find_one({"processed": False})


def mark_email_processed(db, email):
    collection = db[EMAIL_TO_RECV_COLLECTION]
    collection.update_one({"_id": email["_id"]},
                          {"$set": {"processed": True}})


def main():
    mongo_addr = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    db_name = os.getenv("DB_NAME", "ai_hack")

    mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
    print("Connecting to MongoDB " + mongo_full_addr)
    mongo_client = pymongo.MongoClient(mongo_full_addr)
    db = mongo_client[db_name]

    # post_email(db, "me", "him", "dmitry.v.zhelobanov@yandex.ru", "dmitry.v.zhelobanov@yandex.ru", "plain_post",
    #            plain_body="plain body")
    post_email(db, "me", "him", "dmitry.v.zhelobanov@yandex.ru", "dmitry.v.zhelobanov@yandex.ru", "html_post",
               html_body="<b>html body</b>")

    # with open(".env", "rb") as fd:
    #     data = Binary(fd.read())
    # post_email(db, "me", "him", "dmitry.v.zhelobanov@yandex.ru", "dmitry.v.zhelobanov@yandex.ru", "attachment_post",
    #            html_body="<b>html body</b>", attachment_data=data, attachment_name="attached_file")

    # email = retrieve_new_email(db)
    # print(email)
    # mark_email_processed(db, email)


if __name__ == "__main__":
    sys.exit(main())
