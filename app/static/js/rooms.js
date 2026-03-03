var socket = io.connect('http://' + window.location.hostname + ':' + location.port);

// Join the room
socket.emit('join_room', { room_id: roomId });

// Listen for updated queue
socket.on("update_queue", function(queue) {
    const queueList = document.getElementById('queue-list');
    queueList.innerHTML = '';

    if (queue.length === 0) {
        const li = document.createElement('li');
        li.textContent = "No songs in the queue yet!";
        li.style.fontStyle = "italic";
        queueList.appendChild(li);
        return;
    }

    queue.forEach(function(track) {
        const li = document.createElement('li');
        li.classList.add("track-item");

        li.innerHTML = `
            <div class="track-details">
                <img src="${track.album_art}" alt="Album Art" class="album-art" />
                <div class="track-info">
                    <div class="track-name">${track.name}</div>
                    <div class="track-artist">${track.artist}</div>
                </div>
                <div class="track-position">#${track.position}</div>
            </div>
        `;

        queueList.appendChild(li);
    });
});

// Add track to queue
document.getElementById('add-track-btn').addEventListener('click', function() {
    const trackId = document.getElementById('track-id-input').value;
    if (trackId.trim()) {
        socket.emit('add_track', { room_id: roomId, track_id: trackId });
        document.getElementById('track-id-input').value = '';
    }
});

socket.on("room_deleted", function(data) {
    alert("This room has been deleted.");
    window.location.href = "/custom_jams";
});

socket.on("play_track", function(data) {
    const trackId = data.track_id;

    fetch("https://api.spotify.com/v1/me/player/play", {
        method: "PUT",
        headers: {
            "Authorization": "Bearer " + accessToken,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            uris: [`spotify:track:${trackId}`]
        })
    }).then(response => {
        if (!response.ok) {
            console.error("Playback failed:", response.statusText);
        }
    });
});

document.getElementById("play-next-btn").addEventListener("click", function() {
    socket.emit("play_next", { room_id: roomId });
});

// Show play button only for room creator
if (currentUserId === roomCreatorId) {
    const playButton = document.getElementById("play-next-btn");
    if (playButton) {
        playButton.style.display = "inline-block";
    }
}

const chatInput = document.getElementById("chat-input");
const sendMessageBtn = document.getElementById("send-message-btn");
const chatMessages = document.getElementById("chat-messages");

// Emit message on button click
sendMessageBtn.addEventListener("click", function () {
    const message = chatInput.value.trim();
    if (message) {
        socket.emit("send_message", {
            room_id: roomId,
            message: message
        });
        chatInput.value = "";
    }
});

// Listen for new messages
socket.on("receive_message", function (data) {
    const li = document.createElement("li");
    li.textContent = `${data.username}: ${data.message}`;
    chatMessages.appendChild(li);
});

socket.on("load_messages", function (messages) {
    messages.forEach(data => {
        const li = document.createElement("li");
        li.textContent = `${data.username}: ${data.message}`;
        chatMessages.appendChild(li);
    });
});

socket.on("user_list", function (data) {
    const userListElement = document.getElementById("user-list");
    userListElement.innerHTML = "";  // Clear existing list

    data.users.forEach(username => {
        const li = document.createElement("li");
        li.textContent = username;
        userListElement.appendChild(li);
    });
});

document.getElementById("leave-room-btn").addEventListener("click", () => {
    socket.emit("leave_room", { room_id: roomId });

    window.location.href = "/custom_jams";
});