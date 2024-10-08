import os
import sys
import time
from datetime import datetime

import ai_utils
import client_utils
import email_utils
import pymongo
import tg_utils
from bson.binary import Binary

POLLING_INTERVAL = 5
PRESENTATION_PATH = "./presentation.pdf"
PRESENTATION_NAME = "presentation.pdf"
OUR_NAME = "Роман"
OUR_EMAIL = "ai-product@yandex.ru"


def send_email(db, client, subject, msg, attachment_data=None, attachment_name=None):
    email_utils.post_email(
        db,
        OUR_NAME,
        client["name"],
        OUR_EMAIL,
        client["email"],
        subject,
        plain_body=msg,
        attachment_data=attachment_data,
        attachment_name=attachment_name,
    )
    client_utils.add_message(db, client, msg, "out", "email")
    client_utils.mark_client_message_sent(db, client, "email")


def send_tg(db, client, msg, attachment_data=None, attachment_name=None):
    tg_utils.post_message(
        db,
        client["tg_id"],
        msg,
        attachment_data=attachment_data,
        attachment_name=attachment_name,
    )
    client_utils.add_message(db, client, msg, "out", "tg")
    client_utils.mark_client_message_sent(db, client, "tg")


def execute_action(db, client, message, msg_type, msg_cls, response_data):
    if msg_cls == ai_utils.TYPE_DND:
        print("Client asked to DND")
        client_utils.mark_client_do_not_disturb(db, client)
    elif msg_cls == ai_utils.TYPE_DEMO_REQ:
        print("Client asked for demo")
        if msg_type == "email":
            subject, msg = ai_utils.generate_demo_email(
                client["name"], client["company_name"], message
            )
            send_email(db, client, subject, msg)
        else:
            msg = ai_utils.generate_demo_tg(
                client["name"], client["company_name"], message
            )
            send_tg(db, client, msg)
    elif msg_cls == ai_utils.TYPE_PRESENTATION_REQ:
        print("Client asked for presentation")
        with open(PRESENTATION_PATH, "rb") as fd:
            data = Binary(fd.read())

        if msg_type == "email":
            subject, msg = ai_utils.get_response_from_date(response_data)
            send_email(
                db,
                client,
                subject,
                msg,
                attachment_data=data,
                attachment_name=PRESENTATION_NAME,
            )
        else:
            _, msg = ai_utils.get_response_from_date(response_data)
            send_tg(
                db, client, msg, attachment_data=data, attachment_name=PRESENTATION_NAME
            )
    elif msg_cls == ai_utils.TYPE_MORE_INFO_REQ:
        print("Client asked for more info")
        attachment_data, attachment_name = ai_utils.get_response_attachment(response_data)
        if msg_type == "email":
            subject, msg = ai_utils.get_response_from_date(response_data)
            send_email(db, client, subject, msg, attachment_data, attachment_name)
        else:
            _, msg = ai_utils.get_response_from_date(response_data)
            send_tg(db, client, msg, attachment_data, attachment_name)
    elif msg_cls == ai_utils.TYPE_TIMEOUT_REQ:
        timeout = ai_utils.get_timeout_from_msg(response_data)
        client_utils.mark_client_got_timeout(db, client, timeout)
    elif msg_cls == ai_utils.TYPE_REDIRECT_REQ:
        print("Automatic redirection is not implemented!!!!!!")
        if msg_type == "email":
            subject, msg = ai_utils.get_response_from_date(response_data)
            send_email(db, client, subject, msg)
        else:
            _, msg = ai_utils.get_response_from_date(response_data)
            send_tg(db, client, msg)
        client_utils.mark_client_redirected(db, client, ai_utils.get_contacts_from_data(response_data))
    elif msg_cls == ai_utils.TYPE_UNKNOWN_REQ:
        print("We have no Idea what the message is about. Manual processing?")
        client_utils.mark_client_unknown_response(db, client, "Unknown")


def main():
    mongo_addr = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    db_name = os.getenv("DB_NAME", "ai_hack")

    mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
    print("Connecting to MongoDB " + mongo_full_addr)
    mongo_client = pymongo.MongoClient(mongo_full_addr)
    db = mongo_client[db_name]

    while True:
        print("Waiting for mongo connection")
        try:
            db[client_utils.CLIENTS_COLLECTION_NAME].count_documents({})
            print("Connected")
            break
        except Exception as e:
            time.sleep(POLLING_INTERVAL)

    while True:
        for client in client_utils.get_clients(
            db, status=client_utils.CLIENT_STATUS_NEW
        ):
            print("Found new client " + str(client))
            sent_type = ""
            if "email" in client:
                subject, message = ai_utils.generate_incentive_email(
                    client["name"],
                    client["company_name"],
                    client["products_of_interest"],
                )
                send_email(db, client, subject, message)
                sent_type = "email"
            elif "tg_id" in client:
                message = ai_utils.generate_incentive_tg_mail(
                    client["name"],
                    client["company_name"],
                    client["products_of_interest"],
                )
                send_tg(db, client, message)
                sent_type = "tg"

            print(sent_type, "was posted")

        while True:
            email = email_utils.retrieve_new_email(db)
            if email is None:
                break

            print("Received email:", email)
            clients = list(client_utils.get_clients(db, email=email["from_email"]))
            if len(clients) == 0:
                print("Can't find client", email["from_email"])
                email_utils.mark_email_processed(db, email, "no client")
                continue

            client = clients[0]
            message = (
                email["html_part"] if "html_part" in email else email["plain_part"]
            )
            email_cls, response = ai_utils.classify_email(message, email["subject"])
            print("email class", email_cls)

            client_utils.add_message(db, client, message, "in", "email")
            email_utils.mark_email_processed(db, email, email_cls)

            execute_action(db, client, message, "email", email_cls, response)

        while True:
            tg_msg = tg_utils.retrieve_new_tg_message(db)
            if tg_msg is None:
                break

            print("Received tg_msg:", tg_msg)
            if "command" in tg_msg and tg_msg["command"] == "/start":
                print("Creating new client")
                client_utils.create_new_tg_client(db, tg_msg["tg_id"], tg_msg["username"])
                tg_utils.mark_message_processed(db, tg_msg, "ok")
            else:
                clients = list(client_utils.get_clients(db, tg_id=tg_msg["tg_id"]))
                if len(clients) == 0:
                    print("Can't find client", tg_msg["tg_id"])
                    tg_utils.mark_message_processed(db, tg_msg, "no client")
                    continue

                client = clients[0]
                message = tg_msg["message"]
                tg_cls, resp_data = ai_utils.classify_tg_message(message)
                print("tg message class", tg_cls)

                client_utils.add_message(db, client, message, "in", "tg")
                tg_utils.mark_message_processed(db, tg_msg, "ok")
                execute_action(db, client, message, "tg", tg_cls, resp_data)

        timeouted_clients = client_utils.get_clients(
            db, status=client_utils.CLIENT_STATUS_TIMEOUT
        )
        for client in timeouted_clients:
            if "deadline" in client and datetime.now() > client["deadline"]:
                print(
                    "Detected client with passed deadline. Let's remember him about us"
                )
                if "email" in client:
                    subject, msg = ai_utils.generate_reminder_email(
                        client["name"], client["company_name"]
                    )
                    send_email(db, client, subject, msg)
                elif "tg_id" in client:
                    msg = ai_utils.generate_reminder_tg(
                        client["name"], client["company_name"]
                    )
                    send_tg(db, client, msg)

        time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
