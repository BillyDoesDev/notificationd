// set up websockets
const socket = io();

socket.on("connect", () => {
    console.log("WebSocket connected");
});

socket.on("notification", (data) => {
    console.log("got in-app notification");
    console.log(data);
});


socket.on("check-in-app", (data) => {
    console.log("[requesting app notif now]");
    socket.emit('request-notif', data);
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
                notificationsDiv.innerHTML += `<p>${notif.content} - Status: ${notif.status}</p>`;
            });
        } else {
            notificationsDiv.innerHTML += `<p>No notifications found.</p>`;
        }
    } catch (err) {
        console.error('Error fetching notifications:', err);
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
