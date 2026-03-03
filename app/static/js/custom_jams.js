var socket = io.connect('http://' + window.location.hostname + ':' + location.port);

socket.emit('get_rooms')
// Listen for room updates from the server
socket.on('update_rooms', function(rooms) {
    console.log(rooms)
    var roomsList = document.getElementById('room-list-ul');
    roomsList.innerHTML = '';
    rooms.forEach(function(room) {
        var li = document.createElement('li');
        li.textContent = room.name;
        li.onclick = function() {
            joinRoom(room.id);
        };
    
        // Show delete button if current user is the room creator
        if (room.created_by === currentUserId) {
            var deleteBtn = document.createElement('button');
            deleteBtn.textContent = "Delete";
            deleteBtn.onclick = function(e) {
                e.stopPropagation(); // Prevents triggering the joinRoom function
                socket.emit("delete_room", { room_id: room.id });
            };
            li.appendChild(deleteBtn);
        }
    
        roomsList.appendChild(li);
    })
});

// Create room button functionality
document.getElementById('create-room-btn').addEventListener('click', function() {
    var roomName = document.getElementById('room-name').value;
    if (roomName.trim()) {
        socket.emit('create_room', {'room_name': roomName});
        document.getElementById('room-name').value = '';
    }
});

// Function to join a room
function joinRoom(room_id) {
    socket.emit('join_room', {'room_id': room_id});
}

socket.on("joined_room", function(data) {
    window.location.href = `/room/${data.room_id}`;
});
