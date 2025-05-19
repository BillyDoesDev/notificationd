// set up websockets
const socket = io("http://localhost:5051/");

socket.on("connect", () => {
    console.log("WebSocket connected");
});

const alertDiv = document.querySelector(".alert-success");
let prev_id = ""
socket.on("notification", (data) => {
    console.log("got in-app notification");
    console.log(data);

    if (data["id"] != prev_id) { // ie, you truly have a new message
        if (alertDiv) {
            alertDiv.textContent = data["message"]
            alertDiv.classList.add("show");
    
            setTimeout(() => {
                alertDiv.classList.remove("show");
            }, 4500); // 500ms fadeIn + 4000ms delay

            prev_id = data["id"]
        }
    }
});


async function fetchNotifications() {
    const userId = document.getElementById('userId').value;
    try {
        const response = await fetch(`/users/${userId}/notifications`);
        const data = await response.json();
        const notificationsDiv = document.getElementById('notifications');
        notificationsDiv.innerHTML = `<h3>Notifications for User ${userId}:</h3>`;
        if (data.data) {
            data.data.forEach(notif => {
                notificationsDiv.innerHTML += `<p>${notif.content} - <b>Status: ${notif.status}, Mode: ${notif.notification_type}</b></p>`;
            });
        } else {
            notificationsDiv.innerHTML += `<p>No notifications found.</p>`;
        }
    } catch (err) {
        console.error('Error fetching notifications:', err);
        notificationsDiv.innerHTML += `<p>Server Error.</p>`;
    }
}

async function sendNotification() {
    const userId = document.getElementById('userIdSend').value;
    const type = document.getElementById('type').value;
    const content = document.getElementById('content').value;

    try {
        const response = await fetch('/notifications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: Number(userId),
                notification_type: type,
                content: content
            })
        });

        const result = await response.json();
        console.log('Notification sent:', result);
    } catch (err) {
        console.error('Error sending notification:', err);
    }
}
