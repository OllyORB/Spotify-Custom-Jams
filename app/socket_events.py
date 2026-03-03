from flask_socketio import emit, join_room
from app import socketio
from app.database import get_db
from app.utils import general_user_info
from app.utils import song_info
from app.utils import user_list

"""
This function is called when a user wants to create a room .
It takes the users id and then room name and adds them to the database.
The user ID is needed so that the creator of the room can be identified later.
Finally it calls the update rooms function so that the new room shows on the frontend.
"""


@socketio.on("create_room")
def create_room(data):
    db = get_db()
    user_info = general_user_info()
    try:
        db.execute(
            "INSERT INTO rooms (name, created_by) VALUES (?, ?)",
            (data["room_name"], user_info["user_id"]),
        )
        db.commit()
        return update_rooms()
    except:
        emit("error", {"message": "Room already exists"})


"""
This function calls the database so it can get the id name and creator of all the rooms and send them to the frontend.
These are needed so the rooms can be displayed in a list for the user.
"""


@socketio.on("get_rooms")
def update_rooms():
    db = get_db()
    rooms = db.execute("SELECT id, name, created_by FROM rooms").fetchall()
    emit(
        "update_rooms",
        [
            {"id": room["id"], "name": room["name"], "created_by": room["created_by"]}
            for room in rooms
        ],
        broadcast=True,
    )


"""
This function is called when a user wants to join a room.
"""


@socketio.on("join_room")
def join_rooms(data):
    db = get_db()
    user_info = general_user_info()
    user_id = user_info["user_id"]
    username = user_info["username"]
    room_id = data.get("room_id")
    room = db.execute("SELECT name FROM rooms WHERE id = ?", (room_id,)).fetchone()
    room_name = room["name"]
    db.execute("DELETE FROM connections WHERE user_id = ?", (user_id,))
    db.execute(
        "INSERT INTO connections (user_id, room_id) VALUES (?, ?)", (user_id, room_id)
    )
    db.commit()
    room_id = str(room_id)
    emit(
        "joined_room", {"room_id": room_id, "room_name": room_name, "user_id": user_id}
    )
    join_room(room_id)
    update_queue(room_id)
    messages = db.execute(
        """
        SELECT messages.content, users.username 
        FROM messages 
        JOIN users ON messages.user_id = users.spotify_id 
        WHERE messages.room_id = ? 
        ORDER BY messages.id ASC
        """,
        (room_id,),
    ).fetchall()
    message_list = []
    for i in messages:
        message_list.append({"message": i["content"], "username": i["username"]})
    emit("load_messages", message_list)
    emit(
        "receive_message",
        {"username": "System", "message": f"{username} has joined the room."},
    )
    users_list = user_list(room_id)
    emit("user_list", {"users": users_list})


@socketio.on("leave_room")
def leave_room(data):
    db = get_db()
    user_info = general_user_info()
    user_id = user_info["user_id"]
    username = user_info["username"]
    room_id = data.get("room_id")
    db.execute("DELETE FROM connections WHERE user_id = ?", (user_id,))
    db.commit()
    users_list = user_list(room_id)
    emit(
        "receive_message",
        {"username": "System", "message": f"{username} has left the room."},
    )
    emit("user_list", {"users": users_list})


@socketio.on("delete_room")
def delete_room(data):
    db = get_db()
    room_id = data["room_id"]
    user = general_user_info()
    user = user["user_id"]
    creator = db.execute(
        "SELECT created_by FROM rooms WHERE id = ?", (room_id,)
    ).fetchone()
    if creator["created_by"] == user and creator is not None:
        emit("room_deleted", {"room_id": room_id}, room=str(room_id))
        db.execute("DELETE FROM queue WHERE room_id = ?", (room_id,))
        db.execute("DELETE FROM connections WHERE room_id = ?", (room_id,))
        db.execute("DELETE FROM messages WHERE room_id = ?", (room_id,))
        db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        db.commit()
    update_rooms()


@socketio.on("update_queue")
def update_queue(room_id):
    db = get_db()
    room_id = str(room_id)
    queue = db.execute(
        "SELECT track_id, position FROM queue WHERE room_id = ?", (room_id,)
    ).fetchall()
    if not queue:
        return emit("update_queue", [], room=room_id)
    else:
        songs = []
        for song in queue:
            info = song_info(song["track_id"])
            if info is not None:
                info["position"] = song["position"]
                songs.append(info)
            else:
                return emit("update_queue", [], room=room_id)
        emit("update_queue", songs, room=room_id)


@socketio.on("add_track")
def add_track(data):
    db = get_db()
    room_id = data["room_id"]
    track_id = data["track_id"]
    info = song_info(track_id)
    user = general_user_info()
    if user is not None:
        added_by = user["user_id"]
    else:
        added_by = None

    if not info:
        return update_queue(room_id)
    else:
        position = db.execute(
            "SELECT MAX(position) FROM queue WHERE room_id = ?", (room_id,)
        ).fetchone()
        position = position[0]
        if position is None:
            position = 0
        else:
            position = int(position) + 1
        db.execute(
            "INSERT INTO queue (room_id, added_by, track_id, position) VALUES (?, ?, ?, ?)",
            (room_id, added_by, track_id, position),
        )
        db.commit()
        return update_queue(room_id)


@socketio.on("play_next")
def play_next(data):
    db = get_db()
    room_id = data["room_id"]
    user = general_user_info()
    user = user["user_id"]
    creator = db.execute(
        "SELECT created_by FROM rooms WHERE id = ?", (room_id,)
    ).fetchone()
    if creator["created_by"] == user and creator is not None:
        track = db.execute(
            "SELECT * FROM queue WHERE room_id = ? ORDER BY position ASC LIMIT 1",
            (room_id,),
        ).fetchone()
        if track != None:
            position = track["position"]
            db.execute(
                "DELETE FROM queue WHERE room_id = ? AND position = ?",
                (room_id, position),
            )
            db.commit()
            track_info = song_info(track["track_id"])
            emit(
                "play_track",
                {
                    "track_id": track_info["track_id"],
                    "name": track_info["name"],
                    "artist": track_info["artist"],
                },
                room=str(room_id),
            )
    update_queue(room_id)


@socketio.on("send_message")
def send_message(data):
    db = get_db()
    user_info = general_user_info()
    room_id = data["room_id"]
    message = data["message"]
    user_id = user_info["user_id"]
    username = user_info["username"]
    db.execute(
        "INSERT INTO messages (room_id, user_id, content) VALUES (?, ? ,?)",
        (room_id, user_id, message),
    )
    db.commit()
    emit(
        "receive_message",
        {"username": username, "message": message},
        room_id=str(room_id),
    )
