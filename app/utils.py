import requests
from flask import session, url_for
from app.database import get_db

API_BASE_URL = "https://api.spotify.com/v1"


def get_headers():
    return {"Authorization": f"Bearer {session["access_token"]}"}


def general_user_info():
    response = requests.get(API_BASE_URL + "/me", headers=get_headers())
    if response.status_code != 200:
        return None
    response = response.json()
    if response["images"] is not None:
        image_url = response["images"][0]["url"]
    else:
        image_url = url_for("static/icons/unknown_person.jpg")

    user_info = {
        "username": response["display_name"],
        "user_id": response["id"],
        "profile_image_url": image_url,
        "country": response["country"],
        "email": response["email"],
    }
    return user_info


def song_info(song):
    response = requests.get(API_BASE_URL + f"/tracks/{song}", headers=get_headers())
    if response.status_code != 200:
        return None
    else:
        info = response.json()
        name = info["name"]
        artists = []
        for i in info["artists"]:
            artists.append(i["name"])
        artist = ",".join(artists)
        album_art = info["album"]["images"][0]["url"]
        return {
            "track_id": song,
            "name": name,
            "artist": artist,
            "album_art": album_art,
        }


def user_list(room_id):
    db = get_db()
    users = db.execute(
        """
        SELECT users.username 
        FROM connections 
        JOIN users ON connections.user_id = users.spotify_id 
        WHERE connections.room_id = ? 
        ORDER BY connections.user_id ASC
        """,
        (room_id,),
    ).fetchall()
    users_list = []
    for i in users:
        users_list.append(i["username"])
    return users_list
