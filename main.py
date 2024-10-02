import requests
import urllib.parse

import os
from dotenv import load_dotenv

from datetime import datetime
from flask import Flask, redirect, request, jsonify, session, render_template, url_for

load_dotenv()

# TODOS! Ranked by importance.
# TODO : Make a start on the custom jams page, research web sockets.
# TODO : Add a Spotify API class for the OAUTH and a config class for all this stuff.
# TODO : Label all this to prove i do actually know what im doing.
# TODO : Seperate stuff into modules and flask blueprints so this file isnt a complete mess.
# TODO : Update README.

# Constants. Yes, i should have used classes but no ones changing this code but me so i dont care.
# TODO: See if using classes gets me more marks.
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIET_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"


# App Page Routes


@app.route("/")
def index():
    return redirect("/login")


@app.route("/home")
def home():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    info = general_user_info()
    username = info["username"]
    profile_image_url = info["profile_image_url"]
    print(profile_image_url)

    return render_template(
        "home.html", username=username, profile_image_url=profile_image_url
    )


@app.route("/player")
def player():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    return render_template("player.html")


@app.route("/custom_jams")
def custom_jams():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    return render_template("custom_jams.html")


# OAuth Handling and Authentication


@app.route("/login")
def login():
    scope = "user-read-private user-read-email user-read-playback-state user-modify-playback-state"

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": REDIRECT_URI,
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)


@app.route("/callback")
def callback():
    if "error" in request.args:
        return jsonify({"error": request.args["error"]})

    if "code" in request.args:
        req_body = {
            "code": request.args["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

    response = requests.post(TOKEN_URL, data=req_body)
    token_info = response.json()

    session["access_token"] = token_info["access_token"]
    session["refresh_token"] = token_info["refresh_token"]
    session["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]

    return redirect("/home")


@app.route("/refresh_token")
def refresh_token():
    if "refresh_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session["access_token"] = new_token_info["access_token"]
        session["expires_at"] = (
            datetime.now().timestamp() + new_token_info["expires_in"]
        )

        return redirect("/home")


def general_user_info():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.get(API_BASE_URL + "/me", headers=headers)
    if response.status_code != 200:
        return redirect("/login")

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
    }
    return user_info


# Handling Player Requests


@app.route("/get_playback_state", methods=["GET"])
def get_playback_state():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    playback_state = requests.get(API_BASE_URL + "/me/player", headers=headers)
    if playback_state.status_code != 200:
        return jsonify(
            {"status": playback_state.status_code, "message": playback_state.text}
        )
    playback_state = playback_state.json()
    is_active = playback_state["device"]["is_active"]
    progress_ms = playback_state["progress_ms"]
    duration_ms = playback_state["item"]["duration_ms"]
    is_playing = playback_state["is_playing"]
    album_image_url = playback_state["item"]["album"]["images"][0]["url"]
    track_name = playback_state["item"]["name"]
    artist_names = playback_state["item"]["artists"]
    repeat_state = playback_state["repeat_state"]
    shuffle_state = str(playback_state["shuffle_state"]).lower()
    volume = playback_state["device"]["volume_percent"]
    artist_name = ""
    for i in range(len(artist_names)):
        item = artist_names[i]["name"]
        artist_name += item + ", "
    artist_name = artist_name.rstrip(", ")

    return jsonify(
        {
            "is_active": is_active,
            "progress_ms": progress_ms,
            "duration_ms": duration_ms,
            "is_playing": is_playing,
            "image_url": album_image_url,
            "title": track_name,
            "artist": artist_name,
            "repeat_state": repeat_state,
            "shuffle_state": shuffle_state,
            "volume": volume,
        }
    )


@app.route("/check_device", methods=["GET"])
def check_device():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    devices = requests.get(API_BASE_URL + "/me/player/devices", headers=headers)
    if devices.status_code != 200 and devices.status_code != 204:
        return jsonify({"status": devices.status_code, "message": devices.text})
    devices = devices.json()
    is_active = any(device["is_active"] for device in devices["devices"])
    return jsonify(
        {
            "is_active": is_active,
        }
    )


@app.route("/play_playback", methods=["POST"])
def play_playback():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    play = requests.put(API_BASE_URL + "/me/player/play", headers=headers)
    if play.status_code != 200 and play.status_code != 204:
        try:
            details = play.json()
        except requests.exceptions.JSONDecodeError:
            details = {"error": "No JSON response"}

        return (
            jsonify({"error": "Failed to start playback", "details": details}),
            play.status_code,
        )

    return jsonify({"message": "Playback started"}), 200


@app.route("/pause_playback", methods=["POST"])
def pause_playback():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    pause = requests.put(API_BASE_URL + "/me/player/pause", headers=headers)
    if pause.status_code != 200 and pause.status_code != 204:
        try:
            details = pause.json()
        except requests.exceptions.JSONDecodeError:
            details = {"error": "No JSON response"}

        return (
            jsonify({"error": "Failed to pause playback", "details": details}),
            pause.status_code,
        )

    return jsonify({"message": "Playback paused"}), 200


@app.route("/next_track", methods=["POST"])
def next_track():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    next = requests.post(API_BASE_URL + "/me/player/next", headers=headers)
    if next.status_code != 204:
        try:
            details = next.json()
        except requests.exceptions.JSONDecodeError:
            details = {"error": "No JSON response"}
        return (
            jsonify({"error": "Failed to pause playback", "details": details}),
            next.status_code,
        )
    return jsonify({"message": "Next track"}), 200


@app.route("/previous_track", methods=["POST"])
def previous_track():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    previous = requests.post(API_BASE_URL + "/me/player/previous", headers=headers)
    if previous.status_code != 204:
        try:
            details = previous.json()
        except requests.exceptions.JSONDecodeError:
            details = {"error": "No JSON response"}
            return (
                jsonify({"error": "Failed to pause playback", "details": details}),
                previous.status_code,
            )
    return jsonify({"message": "Next track"}), 200


@app.route("/toggle_shuffle", methods=["GET", "POST"])
def toggle_shuffle():
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    playback_state = requests.get(API_BASE_URL + "/me/player", headers=headers)
    if playback_state.status_code != 200:
        return jsonify({"error": playback_state.text})

    playback_state = playback_state.json()
    current_shuffle_state = playback_state["shuffle_state"]
    new_shuffle_state = not current_shuffle_state
    new_shuffle_state = str(new_shuffle_state).lower()
    toggle = requests.put(
        API_BASE_URL + f"/me/player/shuffle?state={new_shuffle_state}", headers=headers
    )

    if toggle.status_code != 200:
        return jsonify({"error": toggle.text})

    return jsonify({"shuffle_state": new_shuffle_state})


@app.route("/toggle_repeat", methods=["POST"])
def toggle_repeat():
    states = ["off", "track", "context"]
    data = request.get_json()
    state = str(data["value"])
    if state in states:
        new_state = states[((states.index(state) + 1) % len(states))]
    else:
        return jsonify({"error": "state invalid"})

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    toggle = requests.put(
        API_BASE_URL + f"/me/player/repeat?state={new_state}", headers=headers
    )
    if toggle.status_code != 200:
        return jsonify({"error": toggle.text})
    return jsonify({"repeat_state": new_state})


@app.route("/update_volume_position", methods=["POST"])
def update_volume_position():
    data = request.get_json()
    volume_percent = int(data["value"])
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    volume = requests.put(
        API_BASE_URL + f"/me/player/volume?volume_percent={volume_percent}",
        headers=headers,
    )
    if volume.status_code != 200 and volume.status_code != 204:
        return jsonify({"error": volume.text})

    return jsonify({"data": volume_percent})


@app.route("/update_playback_position", methods=["POST"])
def update_playback_position():
    data = request.get_json()
    position = int(data["value"])
    headers = headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.put(
        API_BASE_URL + f"/me/player/seek?position_ms={position}", headers=headers
    )
    if response.status_code != 200 and response.status_code != 204:
        return jsonify({"error": response.text})

    return jsonify({"data": position})


# Local host the app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
