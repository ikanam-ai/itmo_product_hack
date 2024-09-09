import argparse
import json
import os
from datetime import datetime, timezone

CLIENTS_COLLECTION_NAME = "clients"
CLIENT_STATUS_NEW = "new"
CLIENT_STATUS_TIMEOUT = "timeout"
CLIENT_STATUS_SENT = "sent"
CLIENT_STATUS_REDIRECTED = "redirected"
CLIENT_STATUS_DONT_DISTURB = "dont_disturb"
CLIENT_STATUS_UNKNOWN = "unknown"


def create_new_client(
    db, name, company_name, product_of_interest, email=None, tg_id=None
):

    if name is None or company_name is None or product_of_interest is None:
        raise Exception(
            "To add a client we need name, company name and the products of interest"
        )

    products_to_add = []
    for product in product_of_interest.split(","):
        products_to_add.append(product.strip())

    collection = db[CLIENTS_COLLECTION_NAME]
    client_data = {
        "name": name,
        "company_name": company_name,
        "products_of_interest": products_to_add,
        "status": CLIENT_STATUS_NEW,
        "created": datetime.now(tz=timezone.utc),
    }

    if email:
        client_data["email"] = email
        if collection.count_documents({"email": email}) > 0:
            raise Exception(
                "Attempting to add a client with email we have in the DB. Can't add."
            )

    if tg_id:
        client_data["tg_id"] = tg_id
        if collection.count_documents({"tg_id": tg_id}) > 0:
            raise Exception(
                "Attempting to add a client with email we have in the DB. Can't add."
            )

    if not email and not tg_id:
        raise Exception(
            "For new client we need email or tg id set to be able to communicate"
        )

    collection.insert_one(client_data)


def get_clients(
    db, name=None, company_name=None, email=None, tg_id=None, status=None, no_msg=False
):
    query = {}
    if name:
        query["name"] = name
    if company_name:
        query["company_name"] = company_name
    if email:
        query["email"] = email
    if tg_id:
        query["tg_id"] = tg_id
    if status:
        query["status"] = status

    if len(query) == 0:
        raise Exception("Can't retrieve unspecified client")

    if no_msg:
        return db[CLIENTS_COLLECTION_NAME].find(query, {"messages": 0})

    return db[CLIENTS_COLLECTION_NAME].find(query)


def add_message(db, client, message, direction, msg_type):
    db[CLIENTS_COLLECTION_NAME].update_one(
        {"_id": client["_id"]},
        {
            "$push": {
                "messages": {
                    "content": message,
                    "type": msg_type,
                    "direction": direction,
                    "ts": datetime.now(tz=timezone.utc),
                }
            }
        },
    )


def mark_client_got_timeout(db, client, deadline):
    # add additional logic here
    db[CLIENTS_COLLECTION_NAME].update_one(
        {"_id": client["_id"]},
        {
            "$set": {
                "status": CLIENT_STATUS_TIMEOUT,
                "deadline": deadline,
                "updated": datetime.now(tz=timezone.utc),
            }
        },
    )


def mark_client_message_sent(db, client, msg_type):
    # add additional logic here
    db[CLIENTS_COLLECTION_NAME].update_one(
        {"_id": client["_id"]},
        {
            "$set": {
                "status": CLIENT_STATUS_SENT,
                "last_msg_type_sent": msg_type,
                "updated": datetime.now(tz=timezone.utc),
            }
        },
    )


def mark_client_redirected(db, client, other_client):
    # add additional logic here
    db[CLIENTS_COLLECTION_NAME].update_one(
        {"_id": client["_id"]},
        {
            "$set": {
                "status": CLIENT_STATUS_REDIRECTED,
                "to": other_client["_id"],
                "updated": datetime.now(tz=timezone.utc),
            }
        },
    )


def mark_client_do_not_disturb(db, client):
    # add additional logic here
    db[CLIENTS_COLLECTION_NAME].update_one(
        {"_id": client["_id"]},
        {
            "$set": {
                "status": CLIENT_STATUS_DONT_DISTURB,
                "updated": datetime.now(tz=timezone.utc),
            }
        },
    )


def mark_client_redirected(db, client, to):
    # add additional logic here
    db[CLIENTS_COLLECTION_NAME].update_one(
        {"_id": client["_id"]},
        {
            "$set": {
                "status": CLIENT_STATUS_REDIRECTED,
                "to": to,
                "updated": datetime.now(tz=timezone.utc),
            }
        },
    )


def mark_client_unknown_response(db, client, to):
    # add additional logic here
    db[CLIENTS_COLLECTION_NAME].update_one(
        {"_id": client["_id"]},
        {
            "$set": {
                "status": CLIENT_STATUS_UNKNOWN,
                "to": to,
                "updated": datetime.now(tz=timezone.utc),
            }
        },
    )


if __name__ == "__main__":
    import pymongo
    from bson import json_util

    parser = argparse.ArgumentParser(
        prog="ClientCLI", description="Client base command line utility"
    )
    parser.add_argument("cmd", choices=["add", "get"])
    parser.add_argument("--name", type=str, help="Client name")
    parser.add_argument("--company_name", type=str, help="Company name")
    parser.add_argument("--email", type=str, help="Client's email")
    parser.add_argument("--tg_id", type=str, help="Client's Telegram ID")
    parser.add_argument(
        "--products",
        type=str,
        help=" Client's products of interest (you can set a list in quotes",
    )
    parser.add_argument(
        "--status",
        type=str,
        help="Client's status",
        choices=[
            CLIENT_STATUS_NEW,
            CLIENT_STATUS_TIMEOUT,
            CLIENT_STATUS_SENT,
            CLIENT_STATUS_REDIRECTED,
            CLIENT_STATUS_DONT_DISTURB,
            CLIENT_STATUS_UNKNOWN,
        ],
    )
    parser.add_argument("--no_msg", action="store_true")

    args = parser.parse_args()

    mongo_addr = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    db_name = os.getenv("DB_NAME", "ai_hack")

    mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"

    print("Connecting to MongoDB " + mongo_full_addr)
    mongo_client = pymongo.MongoClient(mongo_full_addr)

    db = mongo_client[db_name]

    if args.cmd == "add":
        create_new_client(
            db, args.name, args.company_name, args.products, args.email, args.tg_id
        )
    elif args.cmd == "get":
        clients = get_clients(
            db,
            name=args.name,
            company_name=args.company_name,
            email=args.email,
            tg_id=args.tg_id,
            status=args.status,
            no_msg=args.no_msg,
        )
        clients = list(clients)
        if len(clients) == 0:
            print("Noting is found")
        else:
            print(json_util.dumps(clients, indent=2))
