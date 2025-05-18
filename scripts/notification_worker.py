import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client as TwilioClient
from mailgun.client import Client as MailgunClient

load_dotenv()

# Configurations

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI") # for use with docker
# MONGO_URI = "mongodb://root:example@localhost:27017"
client = MongoClient(MONGO_URI)
mydb = client['notifications_db']
collection_name = "notifications"
db = mydb[collection_name]

# Email Configuration
MAILGUN_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
REGISTERED_RECEIVER_EMAIL = os.getenv("REGISTERED_RECEIVER_EMAIL")

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECEIVER_PHONE_NUMBER = os.getenv("RECEIVER_PHONE_NUMBER")


# Email Notification Handler
def send_email_notification(notification):
    try:
        message = notification['content']
        data = {
            "from": f"Mailgun Sandbox <postmaster@{MAILGUN_DOMAIN}>",
            "to": REGISTERED_RECEIVER_EMAIL,
            "subject": "e-mail notification demo.",
            "text": message,
            "o:tag": "Demo email",
        }

        # send email
        client = MailgunClient(auth=("api", MAILGUN_KEY))
        req = client.messages.create(data=data, domain=MAILGUN_DOMAIN)

        db.update_one(
            {"_id": notification['_id']},
            {"$set": {"status": "sent", "timestamp": datetime.now()}}
        )
        print("Email sent!")
        # print(req.json())

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        db.update_one(
            {"_id": notification['_id']},
            {"$set": {"status": "failed", "timestamp": datetime.now()}}
        )


# SMS Notification Handler
def send_sms_notification(notification):
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_AUTH_TOKEN)
        message = notification['content']

        req = client.messages.create(
          from_=TWILIO_PHONE_NUMBER,
          body=message,
          to=RECEIVER_PHONE_NUMBER
        )
        # print(req.sid)

        db.update_one(
            {"_id": notification['_id']},
            {"$set": {"status": "sent", "timestamp": datetime.now()}}
        )
        print("SMS sent!")

    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        db.update_one(
            {"_id": notification['_id']},
            {"$set": {"status": "failed", "timestamp": datetime.now()}}
        )

# Notification Dispatcher
def process_notifications():
    pending_notifications = db.find({"status": {"$in": ["pending", "failed"]}})

    for notification in pending_notifications:
        notification_type = notification.get("notification_type")
        print(f"processing {notification_type} notification...")

        if notification_type == "email":
            send_email_notification(notification)
        elif notification_type == "sms":
            send_sms_notification(notification)


if __name__ == "__main__":
    ## Scheduler Setup
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_notifications, 'interval', seconds=10)
    scheduler.start()

    print("Notification worker started with APScheduler...")
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

    # test stuff out, just in case
    # docs = list(db.find(
    #         {},
    #         {"_id": 0}
    #     ))
    # print(docs)
