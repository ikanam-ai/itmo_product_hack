import imaplib
import json
import os
import smtplib
import ssl
import sys
import time
import traceback
from datetime import datetime, timezone
from email import message_from_bytes
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from email.header import decode_header

import pymongo

# email structure:
# optional html_part
# optional plain_part
# optional attachment { data, file_name }
# subject
# from
# to
# from_email
# to_email
# for outgoing emails
#   sent
#   status
#   process_ts
# for incoming emails
#   processed
#   recv_ts

POLLING_INTERVAL = 5
EMAIL_CREDENTIALS_COLLECTION = "email_accounts"
EMAIL_TO_SEND_COLLECTION = "send_email"
EMAIL_TO_RECV_COLLECTION = "recv_email"


def send_email(email, smtp_client):
    message = MIMEMultipart()

    content_set = False
    if email.get("html_part", None):
        message.attach(MIMEText(email["html_part"], "html"))
        content_set = True
    if email.get("plain_part", None):
        message.attach(MIMEText(email["plain_part"], "plain"))
        content_set = True

    if not content_set:
        raise Exception("Error: message has no content. " + str(email))

    if "attachment" in email:
        attachment = email["attachment"]
        fname = attachment["file_name"]

        attachment_part = MIMEApplication(attachment["data"], Name=fname)
        attachment_part["Content-Disposition"] = 'attachment; filename="%s"' % fname
        message.attach(attachment_part)

    message["Subject"] = email["subject"]
    message["From"] = formataddr((email["from"], email["from_email"]))
    message["To"] = formataddr((email["to"], email["to_email"]))

    print(f"Sending email to {email['to']}, subject: {email['subject']}'")
    smtp_client.sendmail(email["from_email"], email["to_email"], message.as_string())


def send_emails(account, db):
    print("Sending emails for account " + account["name"])
    collection = db[EMAIL_TO_SEND_COLLECTION]

    emails = list(collection.find({"sent": False}))
    print(f"Emails to send: {len(emails)}")

    if len(emails) == 0:
        return

    with smtplib.SMTP_SSL(
        account["smtp_server"],
        account["smtp_port"],
        context=ssl.create_default_context(),
    ) as smtp_client:

        smtp_client.login(account["login"], account["password"])
        for email in emails:
            to_update = {"sent": True}

            try:
                send_email(email, smtp_client)
                to_update["status"] = "ok"
            except Exception as e:
                to_update["status"] = "error: " + str(e)
                print(
                    "Error: failed to send email with exception "
                    + str(e)
                    + " email id "
                    + str(email["_id"])
                )

            to_update["process_ts"] = datetime.now(tz=timezone.utc)
            collection.update_one({"_id": email["_id"]}, {"$set": to_update})


def process_header(s):
    if s.startswith('=?'):
        print("Encoded", s)
        s = decode_header(s)[0][0].decode()
        print("Decoded name", s)
        return s
    return s


def receive_emails(account, db, mailbox="inbox"):
    print("Receiving emails for account " + account["name"])
    collection = db[EMAIL_TO_RECV_COLLECTION]

    with imaplib.IMAP4_SSL(
        host=account["imap_server"], port=account["imap_port"]
    ) as imap_client:
        imap_client.login(account["login"], account["password"])

        imap_client.select(mailbox)

        status, data = imap_client.search(None, "ALL")
        mail_ids = []
        for block in data:
            mail_ids += block.split()

        print(f"Found {len(mail_ids)} new emails")

        for m_id in mail_ids:
            status, data = imap_client.fetch(m_id, "(RFC822)")
            for response_part in data:
                if not isinstance(response_part, tuple):
                    continue

                message = message_from_bytes(response_part[1])
                from_addr = parseaddr(message["From"])
                from_name = process_header(from_addr[0])
                to_addr = parseaddr(message["To"])
                to_name = process_header(to_addr[0])
                subject = process_header(message["Subject"])
                new_email = {
                    "processed": False,
                    "recv_ts": datetime.now(tz=timezone.utc),
                    "from": from_name,
                    "from_email": from_addr[1],
                    "to": to_name,
                    "to_email": to_addr[1],
                    "subject": subject,
                }
                if message.is_multipart():
                    html_content = ""
                    plain_content = ""
                    attachment = None

                    for part in message.get_payload():
                        part_type = part.get_content_type()
                        if part_type == "text/plain":
                            plain_content += part.get_payload()
                        elif part_type == "text/html":
                            html_content += part.get_payload()
                        elif part_type == "application/octet-stream":
                            attachment = {
                                "data": part.get_payload(decode=True),
                                "file_name": part.get_filename(),
                            }
                        else:
                            print("Warning: Unknown content type: " + str(part_type))

                    if html_content:
                        new_email["html_part"] = html_content
                    if plain_content:
                        new_email["plain_part"] = plain_content
                    if attachment:
                        new_email["attachment"] = attachment
                else:
                    new_email["plain_part"] = message.get_payload()

                try:
                    collection.insert_one(new_email)
                    # delete email in the mailbox
                    imap_client.store(m_id, "+FLAGS", "\\Deleted")

                except Exception as e:
                    print("Error while inserting new email: " + str(e))


def main():
    mongo_addr = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    db_name = os.getenv("DB_NAME", "ai_hack")

    mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"

    print("Connecting to MongoDB " + mongo_full_addr)
    mongo_client = pymongo.MongoClient(mongo_full_addr)

    db = mongo_client[db_name]

    while True:
        try:
            print("Retrieving email accounts")
            accounts = list(db[EMAIL_CREDENTIALS_COLLECTION].find())
            if len(accounts) != 0:
                break
        except Exception as e:
            print("Error while retrieving accounts: " + str(e))

        print("Error: Can't find accounts try later")
        time.sleep(2)
        continue

    print(f"Running on {len(accounts)} email accounts")

    while True:
        # let's work with one account only
        account = accounts[0]

        try:
            receive_emails(account, db, mailbox="inbox")
            send_emails(account, db)
        except Exception as e:
            print(
                "Error: got exception in the main "
                + str(e)
                + "\nTrace:\n"
                + str(traceback.format_exc())
            )

        print("Going into sleep for " + str(POLLING_INTERVAL) + " seconds")
        time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
