import requests
import urllib.parse
from flask import session, redirect, request, jsonify
from app import app
from app.utils import general_user_info
from app.database import get_db
from datetime import datetime
import os

# Global Constants
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

"""
This function is run everytime a user opens the web app or tries to open a page without an access token. 
It redirects to Spotify's authentication page and sends them my client id which I was assigned after applying to run a web app with their API. 
I also send them the scope, this lets the user know what control they are giving the app of their spotify account and they can choose to accept or decline when logging in.
Finally I send the redirect uri which tells Spotify's authentication page what to send their data back to.
"""
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

"""
This function is called when the user is redirected to the redirect uri, which is /callback. 
The function requests an access token and a refresh token from Spotify, as long as there have been no problems with the login.
It then stores the access token, refresh token and the time it expires at, within the flask session.
Next it calls the general user info function from the utils file to request the users info from Spotify's API.
The users spotify id, username and email are stored in the database.
Finally the user is redirected to the home page.
"""
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
    else:
        return jsonify({"error": "Missing authorization code"})

    response = requests.post(TOKEN_URL, data=req_body)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch token", "text": response.text})

    token_info = response.json()

    if "access_token" not in token_info:
        return jsonify({"error": "No access token in response"})

    session["access_token"] = token_info["access_token"]
    session["refresh_token"] = token_info["refresh_token"]
    session["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]

    user_info = general_user_info()
    if user_info == None:
        return redirect("/login")
    spotify_id = user_info["user_id"]
    username = user_info["username"]
    email = user_info["email"]

    session["spotify_id"] = spotify_id

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE spotify_id = ?", (spotify_id,)
    ).fetchone()

    if user is None:
        db.execute(
            "INSERT INTO users (spotify_id, username, email) VALUES (?, ?, ?)",
            (spotify_id, username, email),
        )
        db.commit()

    return redirect("/home")
