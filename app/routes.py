from flask import render_template, redirect, session
from app import app
from app.utils import general_user_info
from datetime import datetime
from app.database import get_db

"""
This sends the user directly to the login page after opening the app.
"""


@app.route("/")
def index():
    return redirect("/login")


"""
This function provides information for the frontend so that the home page can be loaded.
It also checks that the user has logged in and has a valid access token.
If the user isn't logged in or has an invalid access token it will redirect them to login or refresh the token.
The function general user info from utils is ran to collect the users information to be displayed on the page.
Username and profile image are extracted from info so that they can be displayed on the homepage.
The html template is rendered with the necessary data.
"""


@app.route("/home")
def home():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    info = general_user_info()
    if not info:
        return redirect("/login")

    username = info["username"]
    profile_image_url = info["profile_image_url"]

    return render_template(
        "home.html", username=username, profile_image_url=profile_image_url
    )


"""
This function loads the player page.
It checks the user is properly authenticated and then renders the page.
"""


@app.route("/player")
def player():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    return render_template("player.html")


"""
This function renders the custom jams page.
It runs the general user info function to get the users id.
It checks authentication then renders the custom jams page, providing the frontend with the users id so rooms can be joined.
"""


@app.route("/custom_jams")
def custom_jams():
    user_id = general_user_info()
    user_id = user_id["user_id"]
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    return render_template("custom_jams.html", current_user_id=user_id)


"""
This function renders the about page, it also checks the users authentication before it renders it.
"""


@app.route("/about")
def about():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    return render_template("about.html")


"""
This function is used to render all rooms. The url is dependent on what room_id is passed in from the frontend.
It gets the current users id using the general user info function from utils and grabs info about the room it is rendering from the database.
It checks authentication then renders the page for the given room and sends the data it has collected to the frontend so it can sort out room permissions.
It also sends the users access token so that music can be played for all users simultaneously on the frontend using one js command.
"""


@app.route("/room/<room_id>")
def room(room_id):
    db = get_db()
    user = general_user_info()
    user_id = user["user_id"]
    room = db.execute(
        "SELECT created_by, name FROM rooms WHERE id = ?", (room_id,)
    ).fetchone()
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh_token")

    return render_template(
        "room.html",
        room_id=room_id,
        room_name=room["name"],
        user_id=user_id,
        room_creator_id=room["created_by"],
        access_token=session["access_token"],
    )
