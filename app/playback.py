import requests
from flask import request, jsonify, session
from app import app

# Global Constants
API_BASE_URL = "https://api.spotify.com/v1"

"""
This function just returns the header that will be used for every API call. 
It just saves time and space and makes each function look nicer.
"""
def get_headers():
    return {"Authorization": f"Bearer {session["access_token"]}"}

"""
This function is called by the javascript on the frontend. 
It sends a get request to retrieve all information about the users Spotify playback state if there is an active device.
The information is all sent back as a dictionary which is turned into a JSON file for the frontend.
This information is all used to display the UI of the player page
The shuffle state is converted to a lowercase string so it is easier for the frontend to work with.
Artist names is originally a list of names but this function just combines the names of the list into one string where they are separated by commas for convenience.
"""
@app.route("/get_playback", methods=["GET"])
def get_playback():
    playback_state = requests.get(API_BASE_URL + "/me/player", headers=get_headers())
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

"""
This function is called by the frontend to check if there is an active device before it calls the get playback function.
It sends a get request to Spotify's API to check if the current user has got Spotify open on any devices.
The response is converted to a boolean value by checking if any one device is active out of all of them.
"""
@app.route("/device", methods=["GET"])
def device():
    devices = requests.get(API_BASE_URL + "/me/player/devices", headers=get_headers())
    devices = devices.json()
    is_active = any(device["is_active"] for device in devices["devices"])
    return jsonify(
        {
            "is_active": is_active,
        }
    )

"""
The following functions are all used to send a post request to the Spotify API to do various different things.
They are all called by the frontend when the user presses a certain button on the player.
The functions attempt to do the action in the name and return either a success or failure response to the frontend.
"""
@app.route("/play", methods=["POST"])
def play():
    response = requests.put(API_BASE_URL + "/me/player/play", headers=get_headers())
    return response.json(), response.status_code


@app.route("/pause", methods=["POST"])
def pause():
    response = requests.put(API_BASE_URL + "/me/player/pause", headers=get_headers())
    return response.json(), response.status_code


@app.route("/next", methods=["POST"])
def next():
    response = requests.post(API_BASE_URL + "/me/player/next", headers=get_headers())
    return response.json, response.status_code


@app.route("/previous", methods=["POST"])
def previous():
    response = requests.post(
        API_BASE_URL + "/me/player/previous", headers=get_headers()
    )
    return response.json(), response.status_code

"""
Similar to the previous functions except this time a get is needed as well.
This function gets the previous shuffle value which is either a True or False value.
The previous state has the not boolean operation applied and a post request is sent with the new state.
So overall it will change the shuffle state to either on or off depending on what it was before.
The function will return the new shuffle state to the frontend so it can be displayed
"""
@app.route("/shuffle", methods=["GET", "POST"])
def shuffle():
    playback_state = requests.get(API_BASE_URL + "/me/player", headers=get_headers())
    playback_state = playback_state.json()
    new_shuffle_state = str(not playback_state["shuffle_state"]).lower()
    response = requests.put(
        API_BASE_URL + f"/me/player/shuffle?state={new_shuffle_state}",
        headers=get_headers(),
    )
    return jsonify({"shuffle_state": new_shuffle_state})

"""
For this function the value of repeat is stored in the frontend and doesnt need to be fetched from spotify.
As there are three values for repeat this cant be done with boolean operations.
Instead the function checks what the previous value for repeat was and cycles through the three.
It does this by adding one to the position in the list and modding it by three so that it loops back to the start after position three
Then it sends a post request to Spotify to update the repeat state and replace it with whatever the new repeat state is.
It returns the new state to the frontend so it can be displayed.
"""
@app.route("/repeat", methods=["POST"])
def repeat():
    states = ["off", "track", "context"]
    data = request.get_json()
    state = str(data["value"])
    if state in states:
        new_state = states[((states.index(state) + 1) % len(states))]
    response = requests.put(
        API_BASE_URL + f"/me/player/repeat?state={new_state}", headers=get_headers()
    )
    return jsonify({"repeat_state": new_state})

"""
Both of the following functions take the values from the sliders on the frontends after they are updated.
They send a post request to Spotify and update either the volume or playback position with the new value after converting it to an integer.
They return the new position to the frontend so it can be updated.
"""
@app.route("/volume", methods=["POST"])
def volume():
    data = request.get_json()
    position = int(data["value"])
    response = requests.put(
        API_BASE_URL + f"/me/player/volume?volume_percent={position}",
        headers=get_headers(),
    )
    return jsonify({"data": position})


@app.route("/playback", methods=["POST"])
def playback():
    data = request.get_json()
    position = int(data["value"])
    response = requests.put(
        API_BASE_URL + f"/me/player/seek?position_ms={position}", headers=get_headers()
    )
    return jsonify({"data": position})
