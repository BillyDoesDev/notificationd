# $~ notificationd

A system to send notifications to users.

<hr>
This submission underlines the following (the striked out ones are not covered):

**Notification Service:**<br>
**Objective:**
Build a system to send notifications to users.

**Requirements**
1. API Endpoints:
    - Send a Notification (POST /notifications)
    - Get User Notifications (GET /users/{id}/notifications)
2. Notification Types:<br>
    - Email, SMS, and in-app notifications.
3. Bonus Points:<br>
    - ~~Use a queue (e.g., RabbitMQ, Kafka) for processing notifications.~~
    - Add retries for failed notifications.

**Deliverables**
1. A Git repository link containing:
    - Source code.
    - README with setup instructions and any assumptions made.
2. ~~(Optional) Link to the deployed application~~ or API documentation (if implemented).
<hr>

## Setup

- Make sure you have [Docker](https://www.docker.com/) installed and running on your system.
- Clone this repository and `cd` into it:
    ```sh
    git clone https://github.com/BillyDoesDev/notificationd.git
    cd notificationd
    ```

- If you haven't already, create an account on [MailGun](https://www.mailgun.com/). This will be used to create and send emails.
    - Follow their [welcome guide](https://app.mailgun.com/welcome-guide) to set up your account, and obtain your API keys, and configure your test email. Save these for later.

- Now, create an account on [Twilio](https://www.twilio.com/en-us). This handles SMS notifications.
    - Obtain a virtual phone number and your auth token from [their dashboard](https://console.twilio.com/us1/develop/sms/try-it-out/send-an-sms), and save these for later.

- Create a `.env` file in the current directory. Its contents should have the following. Replace the fields as required.
> [!IMPORTANT]
> Keep the `MONGO_URI` as is.
    
    ```sh
    MAILGUN_API_KEY="xxx"
    MAILGUN_DOMAIN="xxx.mailgun.org"
    REGISTERED_RECEIVER_EMAIL="John Doe <johndoe@email.com>"

    TWILIO_SID="xxx"
    TWILIO_AUTH_TOKEN="xxx"
    TWILIO_PHONE_NUMBER="+1xxx"
    RECEIVER_PHONE_NUMBER="xxx"

    MONGO_URI="mongodb://root:example@mongo:27017/notifications_db?authSource=admin"
    ```

## Execution and API details

- Inside the project directory, run:
    ```sh
    docker compose up --build -d
    ```
- This will start the docker container. Optionally, to view the logs of the web server, run:
    ```sh
    docker compose logs -f flask-server
    ```
- The API endpoints are live at `localhost:5050`. You can head over there in your browser to try out a web client for the API.

- To access a GUI to the database, you can head over to `http://localhost:8081` to access the `mongo-express` dashboard for the MongoDB database.

- To shut the server down, simply run:
    ```sh
    docker compose down
    ```
> [!Tip]
> If you do not make any changes to the files, to run this next time, you can simply do:
> ```sh
> docker compose up -d
> ```
> This does not rebuild the containers each time.

---

### API Documentation

The following endpoints are available:

1. **Post a new notification**

    Sends a request for a new notification to be sent.

    * **URL**

        `/notifications`

    * **Method:**

        `POST`
    
    *  **URL Params**

        **Required:**
        
        None

    * **Data Params**

        ```json
        {
            "user_id": 4,
            "notification_type": "in-app",
            "content": "hello, world!"
        }
        ```

        The `user_id` key can be any integer, denoting some user id in a real system.<br>
        The `notification_type` key can be either `in-app` | `sms` | `email`.<br>
        The `content` key is the message you want to send in your notification.

    * **Success Response:**

        * **Code:** 201 <br />
            **Content:**
            ```json
            {"message": "Notification queued", "id": "6829ce9ed71d22a7cfbf86db"}
            ```

            The `id` key refers to the unique `ObjectID` of the notification as stored in the MongoDB. Queries on this notification may be performed using this.
    
    * **Error Response:**

        * **Code:** 500 <br />


    * **Sample Call:**

        ```sh
          curl -X POST 'http://localhost:5050/notifications' \
          -H 'Content-Type: application/json' \
          --data-raw '{"user_id":4,"notification_type":"in-app","content":"hello, world!"}'
        ```

    ---

2. **Get Notifications**

    Returns notifications for a certain user id.

    * **URL**

        `/users/:id/notifications`

    * **Method:**

        `GET`
    
    *  **URL Params**

        **Required:**
        
        `id=[integer]`

    * **Data Params**

        None

    * **Success Response:**

        * **Code:** 200 <br />
            **Content:**
            ```json
            {"data": [
                {
                    "user_id": 4,
                    "notification_type": "email",
                    "content": "message content",
                    "status": "sent",
                    "timestamp": {
                        "$date": "2025-05-18T09:20:09.362Z"
                    }
                },
                ...
            ]}
            ```

            The `status` key can have values `pending` | `sent` | `failed`. In case a notification hasn't been sent yet, it will be retried after every 10s.<br>
            The `timestamp` key shows the UNIX timestamp of the last notification status.
    
    * **Error Response:**

        * **Code:** 400 <br />
            **Content:** `{"error": "No notifications for user_id found."}`


    * **Sample Call:**

        ```sh
         curl 'http://localhost:5050/users/4/notifications' 
        ```

---


## Tech Stack Details

- This app runs in a `python-flask` server, and uses `MongoDB` to store user notifications. The entire setup is dockerised, to provide a seamless deployment experience, and also to allow room for scalability.
- In-app updates are managed via `websockets`, using `socket.io`, on both the client and the server.
- SMS and Email updates are handled via a [`notification-worker`](https://github.com/BillyDoesDev/notificationd/blob/main/scripts/notification_worker.py) process, which uses `apscheduler` to poll notifications every `10s`, and send them as required.
- `MailGun` and `Twilio` are used to send email and SMS updates, respectively.


> [!TIP]
> [Note that this is completely optional] If you prefer having `socket.io.js` fully offline, you can get it using:
> ```sh
> curl -O https://raw.githubusercontent.com/BillyDoesDev/blueberry/refs/heads/main/> static/socket.io.js
> ```
> And then simply link that to your `index.html` 


## License

This project is open source, under the MIT License.

```
MIT License

Copyright (c) 2025 BillyDoesDev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

```
