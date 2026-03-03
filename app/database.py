import sqlite3
from flask import g

DATABASE = "custom_jams.db"

"""
This function gets the database so it can be used to run SQL queries.
Flask's g variable is used so that a new connection isn't needed everytime the database is used.
"""
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

"""
This function closes the database when the app is shutdown.
"""
def close_connection(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

"""
This function is used to create the database.
It creates each table in an individual function and commits them all together if there are no issues.
The first table is the user table which is used to store information about each user that has connected a spotify account.
Next is the rooms table which stores information about rooms created in the custom jams page. It takes a foreign key from the users table for created_by
The messages table stores the messages that are sent in each room. It has two foreign keys from the user table's id and the rooms table's id.
The queue table stores the songs added to each room's queue. It also has a foreign key from the user's id column and room's id column.
Lastly the connection table stores which users are in each room currently. It also has a foreign key from the user's id column and room's id column.
"""
def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spotify_id TEXT NOT NULL UNIQUE,
                username TEXT,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                user_id INTEGER,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                added_by INTEGER NOT NULL,
                track_id TEXT NOT NULL,
                position INTEGER,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_playing BOOLEAN DEFAULT 0,
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                FOREIGN KEY (added_by) REFERENCES users(id)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            room_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
            """
        )
        db.commit()
