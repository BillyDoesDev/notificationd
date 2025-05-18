// set up websockets
const socket = io();
socket.on('connect', function () {
    console.log("Connected to socketio")
    // socket.emit('active', { data: 'Client connected to socketio' });
});