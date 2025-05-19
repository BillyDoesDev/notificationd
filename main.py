import pika
import os
import json
from pymongo.errors import PyMongoError
from flask_socketio import SocketIO, emit
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()

RABBITMQ_QUEUE=os.getenv("RABBITMQ_QUEUE")
RABBITMQ_EXCHANGE=os.getenv("RABBITMQ_EXCHANGE")
RABBITMQ_ROUTING_KEY=os.getenv("RABBITMQ_ROUTING_KEY")

channel.exchange_declare(
    exchange=RABBITMQ_EXCHANGE,
    exchange_type="direct",
    durable=True
)
channel.queue_declare(queue=RABBITMQ_QUEUE)

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://root:example@localhost:27017/notifications_db?authSource=admin"

CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")
mongo = PyMongo(app)

collection_name = "notifications"
db = mongo.db[collection_name]


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/users/<int:user_id>/notifications", methods=["GET"])
def get_user_notifications(user_id: int):
    try:
        docs = list(db.find({"user_id": user_id}, {"_id": 0}))
        if not docs:
            return jsonify(error=f"No notifications for user_id: {user_id} found."), 400

        return jsonify(data=docs), 200
    except PyMongoError as e:
        return jsonify(error=str(e)), 500


@app.route("/notifications", methods=["POST"])
def post_user_notifications():
    try:
        data = request.get_json()
        if not data:
            return jsonify(error="Empty payload."), 400

        try:
            payload = {
                "user_id": data["user_id"],
                "notification_type": data[
                    "notification_type"
                ],  # can be email, sms, in-app
                "content": data["content"],
                "status": "pending",  # can be pending, sent, failed
                "timestamp": str(datetime.now()),
            }
        except KeyError as e:
            return jsonify(error=str(e)), 400

        result = db.insert_one(payload)
        inserted_id = str(result.inserted_id)

        payload["_id"] = inserted_id

        # send over to rabbitmq
        channel.basic_publish(exchange=RABBITMQ_EXCHANGE, routing_key=RABBITMQ_ROUTING_KEY, body=json.dumps(payload))
        # hacky fix for in-app notifications, since it encounters race conditions, sometimes
        if payload["notification_type"] == "in-app": channel.basic_publish(exchange=RABBITMQ_EXCHANGE, routing_key=RABBITMQ_ROUTING_KEY, body=json.dumps(payload))

        return jsonify(message="Notification queued", id=inserted_id), 201

    except PyMongoError as e:
        return jsonify(error=str(e)), 500


# Handles socketio connections
@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("message", "Connected to WebSocket server")



if __name__ == "__main__":
    print("[Flask server starting...]")
    socketio.run(app, debug=True, host="0.0.0.0", port=5050)
