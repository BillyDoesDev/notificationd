import os
from pymongo.errors import PyMongoError
from flask_socketio import SocketIO, emit
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from bson import json_util
from bson.objectid import ObjectId
import json

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
# app.config["MONGO_URI"] = "mongodb://root:example@localhost:27017/notifications_db?authSource=admin"

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
                "timestamp": datetime.now(),
            }
        except KeyError as e:
            return jsonify(error=str(e)), 400

        result = db.insert_one(payload)
        inserted_id = str(result.inserted_id)

        return jsonify(message="Notification queued", id=inserted_id), 201

    except PyMongoError as e:
        return jsonify(error=str(e)), 500


# Handles socketio connections
@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("message", "Connected to WebSocket server")


@socketio.on("request-notif")
def _handle_in_app(notification):
    try:
        db.update_one(
            {"_id": ObjectId(notification["_id"]["$oid"])},
            {"$set": {"status": "sent", "timestamp": datetime.now()}},
        )

        emit("notification", {"message": notification["content"]})
        print("In-app notification sent!")
    except Exception as e:
        print(f"Failed to in-app notification: {str(e)}")
        db.update_one(
            {"_id": ObjectId(notification["_id"]["$oid"])},
            {"$set": {"status": "failed", "timestamp": datetime.now()}},
        )

def process_in_app_notifications():
    pending_notifications = db.find(
        {"status": {"$in": ["pending", "failed"]}, "notification_type": "in-app"}
    )

    for notification in pending_notifications:
        socketio.emit("check-in-app", json.loads(json_util.dumps(notification)))
        print("requesting to process in app notifications...")


if __name__ == "__main__":
    # start scheduler for in-app notifications
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_in_app_notifications, "interval", seconds=10)
    scheduler.start()
    print("Scheduling in-app notifications with APScheduler...")

    print("[Flask server starting...]")
    socketio.run(app, debug=True, host="0.0.0.0", port=5050, allow_unsafe_werkzeug=True)
