#!/usr/bin/env python

import os
import sys
import threading
import pika
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import notification_worker as notif
import json
from bson.objectid import ObjectId


load_dotenv()
RABBITMQ_QUEUE=os.getenv("RABBITMQ_QUEUE")
RABBITMQ_EXCHANGE=os.getenv("RABBITMQ_EXCHANGE")
RABBITMQ_ROUTING_KEY=os.getenv("RABBITMQ_ROUTING_KEY")

RETRY_QUEUE = f"{RABBITMQ_QUEUE}.retry"
RETRY_DELAY_MS = int(os.getenv("RETRY_DELAY_MS", 10000))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    return "WebSocket server running."


def setup_queues(channel):
    # Retry queue with TTL and DLX back to main queue
    args = {
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": RABBITMQ_QUEUE,
        "x-message-ttl": RETRY_DELAY_MS,
    }
    channel.queue_declare(queue=RETRY_QUEUE, durable=True, arguments=args)
    # channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.queue_bind(exchange=RABBITMQ_EXCHANGE, queue=RABBITMQ_QUEUE)


def rabbitmq_consumer():
    def callback(ch, method, properties, body):
        message = json.loads(body.decode())
        _id = message["_id"]
        notification_type = message["notification_type"]
        retry_count = message.get("retry_count", 0)

        print(f" [*] Received message of _id: {_id} | {notification_type}")
        
        # # update database entry
        # # handle sending notif
        try:
            if notification_type == "email": notif.send_email_notification(notification=message)
            elif notification_type == "sms": notif.send_sms_notification(notification=message)
            else:
                # try:
                    notif.db.update_one(
                        {"_id": ObjectId(message["_id"])},
                        {"$set": {"status": "sent", "timestamp": datetime.now()}},
                    )

                    socketio.emit("notification", {"message": message["content"]})
                    print("In-app notification sent!")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            print(f"[*] Failed to send {_id}: {e}")

            retry_count += 1
            if retry_count > MAX_RETRIES:
                notif.db.update_one(
                    {"_id": ObjectId(message["_id"])},
                    {"$set": {"status": "failed", "timestamp": datetime.now()}},
                )
                print(f"[*] Max retries exceeded for {_id}. Marking as failed.")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Update retry count and republish to retry queue
            message["retry_count"] = retry_count
            ch.basic_ack(delivery_tag=method.delivery_tag)

            ch.basic_publish(
                exchange=RABBITMQ_EXCHANGE,
                routing_key=RABBITMQ_ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            print(f"[*] Retry scheduled for {_id} in {RETRY_DELAY_MS}ms")


    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()

    setup_queues(channel)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=False)

    print(" [*] Waiting for messages.")
    channel.start_consuming()


def main():
    threading.Thread(target=rabbitmq_consumer, daemon=True).start()
    socketio.run(app, debug=True, host="0.0.0.0", port=5051, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
