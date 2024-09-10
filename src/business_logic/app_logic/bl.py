import os, sys, time
import pymongo
import client_utils
import tg_utils
import email_utils
import ai_utils
from bson.binary import Binary
from datetime import datetime


POLLING_INTERVAL = 5
PRESENTATION_PATH = "./presentation.pdf"
PRESENTATION_NAME = "presentation.pdf"
OUR_NAME = "Rudolf The Advertiser"
OUR_EMAIL = "dmitry.v.zhelobanov@yandex.ru"


def send_email(db, client, subject, msg, attachment_data=None, attachment_name=None):
    email_utils.post_email(db, OUR_NAME, client["name"], OUR_EMAIL, client["email"], subject,
                           html_body=msg, attachment_data=attachment_data, attachment_name=attachment_name)
    client_utils.add_message(db, client, msg, "out", "email")
    client_utils.mark_client_message_sent(db, client, "email")


def send_tg(db, client, msg, attachment_data=None, attachment_name=None):
    # Отсылаем сообщение пользователю ТГ
    tg_utils.post_message(db, client["tg_id"], msg, attachment_data=attachment_data, attachment_name=attachment_name)
    # Обновление БД с новым сообщением
    client_utils.add_message(db, client, msg, "out", "tg")
    # Пометка, что сообщение отправлено
    client_utils.mark_client_message_sent(db, client, "tg")


def execute_action(db, client, message, msg_type, msg_cls):
    # Пользователь попросил не беспокоить
    if msg_cls == ai_utils.TYPE_DND:
        print("Client asked to DND")
        client_utils.mark_client_do_not_disturb(db, client)

    # Пользователь попросил демо (письмо с данными для входа в демо)
    elif msg_cls == ai_utils.TYPE_DEMO_REQ:
        print("Client asked for demo")
        if msg_type == "email":
            subject, msg = ai_utils.generate_demo_email(client["name"], client["company_name"], message)
            send_email(db, client, subject, msg)
        else:
            msg = ai_utils.generate_demo_tg(client["name"], client["company_name"], message)
            send_tg(db, client, msg)
    elif msg_cls == ai_utils.TYPE_PRESENTATION_REQ:
        print("Client asked for presentation")
        with open(PRESENTATION_PATH, "rb") as fd:
            data = Binary(fd.read())

        if msg_type == "email":
            subject, msg = ai_utils.generate_presentation_email(client["name"], client["company_name"], message,)
            send_email(db, client, subject, msg, attachment_data=data, attachment_name=PRESENTATION_NAME)
        else:
            msg = ai_utils.generate_presentation_tg(client["name"], client["company_name"], message,)
            send_tg(db, client, msg, attachment_data=data, attachment_name=PRESENTATION_NAME)
    elif msg_cls == ai_utils.TYPE_MORE_INFO_REQ:
        print("Client asked for more info")
        if msg_type == "email":
            subject, msg = ai_utils.generate_more_info_email(client["name"], client["company_name"], message)
            send_email(db, client, subject, msg)
        else:
            msg = ai_utils.generate_more_info_tg(client["name"], client["company_name"], message)
            send_tg(db, client, msg)
    elif msg_cls == ai_utils.TYPE_TIMEOUT_REQ:
        timeout = ai_utils.get_timeout_from_msg(message)
        client_utils.mark_client_got_timeout(db, client, timeout)
    elif msg_cls == ai_utils.TYPE_REDIRECT_REQ:
        print("Automatic redirection is not implemented")
    elif msg_cls == ai_utils.TYPE_UNKNOWN_REQ:
        print("We have no Idea what the message is about. Manual processing?")


def main():
    mongo_addr = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    db_name = os.getenv("DB_NAME", "ai_hack")

    mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
    print("Connecting to MongoDB " + mongo_full_addr)
    mongo_client = pymongo.MongoClient(mongo_full_addr)
    db = mongo_client[db_name]


    # Подключение к БД
    while True:
        print("Waiting for mongo connection")
        try:
            db[client_utils.CLIENTS_COLLECTION_NAME].count_documents({})
            print("Connected")
            break
        except Exception as e:
            time.sleep(POLLING_INTERVAL)


    # Цикл для отправки инициативного письма каждому новому клиенту
    while True:
        for client in client_utils.get_clients(db, status=client_utils.CLIENT_STATUS_NEW):
            print("Found new client " + str(client))
            sent_type = ""
            if "email" in client:
                subject, message = ai_utils.generate_incentive_email(client["name"], client["company_name"],
                                                                     client["products_of_interest"])
                send_email(db, client, subject, message)
                sent_type = "email"
            elif "tg_id" in client:
                # ____Тут еще надо слать tg_id, чтобы мы написали конкретному пользователю____
                message = ai_utils.generate_incentive_tg_mail(client["name"], client["company_name"],
                                                              client["products_of_interest"])
                send_tg(db, client, message)
                sent_type = "tg"

            print(sent_type, "was posted")

        while True:
            email = email_utils.retrieve_new_email(db)
            if email is None:
                break

            print("Received email:", email)
            client = client_utils.get_clients(db, email=email["from_email"])
            if len(client) == 0:
                print("Can't find client")
                email_utils.mark_email_processed(db, email, "no client")

            message = email["html_part"] if "html_part" in email else email["plain_part"]
            email_cls = ai_utils.classify_email(message, email["subject"])
            print("email class", email_cls)

            client_utils.add_message(db, client, message, "in", "email")
            email_utils.mark_email_processed(db, email, email_cls)

            execute_action(db, client, message, "email", email_cls)

        # Цикл получения ответа от пользователя
        while True:
            # Получение сообщения от пользователя
            # ___Должен вернуть from - id___
            tg_msg = tg_utils.retrieve_new_tg_message(db)
            if tg_msg is None:
                break

            print("Received tg_msg:", tg_msg)
            # Ищем клиента, который отправил сообщение
            client = client_utils.get_clients(db, tg_id=tg_msg["from"])
            if len(client) == 0:
                print("Can't find client")
                # ___Тут еще логика с received или post, по идее в received надо заносить___
                tg_utils.mark_message_processed(db, tg_msg, "no client")

            # Если клиент существует, то достаем его content
            message = tg_msg["content"]
            # Логика с классификацией сообщения
            tg_cls = ai_utils.classify_tg_message(message)
            print("tg message class", tg_cls) # Выводим класс сообщения

            # Обновляем БД, сообщение получено
            client_utils.add_message(db, client, message, "in", "tg")
            # Отмечаем, что выполнено
            tg_utils.mark_message_processed(db, tg_msg, "ok")

            # Логика с действием (что делать дальше)
            execute_action(db, client, message, "tg", tg_cls)

        #___Добавил bd как первый параметр___
        timeoted_clients = client_utils.get_clients(db, status=client_utils.CLIENT_STATUS_TIMEOUT)
        for client in timeoted_clients:
            if "deadline" in client and datetime.now() < client["deadline"]:
                print("Detected client with passed deadline. Let's remember him about us")
                if "email" in client:
                    subject, msg = ai_utils.generate_reminder_email(client["name"], client["company_name"])
                    send_email(db, client, subject, msg)
                # Логика с созданием письма позже
                elif "tg_id" in client:
                    msg = ai_utils.generate_reminder_tg(client["name"], client["company_name"])
                    send_tg(db, client, msg)

        time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())