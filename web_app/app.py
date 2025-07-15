import sys
import os
from flask import Flask, render_template, request, jsonify
import sqlite3

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import init_db, get_playlists, get_songs_by_playlist

app = Flask(__name__)
init_db()

@app.route("/")
def index():
    playlists = get_playlists()
    return render_template("index.html", playlists=playlists)

@app.route("/playlist/<int:playlist_id>")
def playlist(playlist_id):
    songs = get_songs_by_playlist(playlist_id)
    if not songs:
        return "В этом плейлисте пока нет треков."
    playlist_name = songs[0]["playlist_name"]
    return render_template("playlist.html", songs=songs, playlist_name=playlist_name)

@app.route("/song/<int:song_id>")
def song(song_id):
    conn = sqlite3.connect("music.db")
    cur = conn.cursor()
    cur.execute("SELECT file_id FROM songs WHERE id = ?", (song_id,))
    result = cur.fetchone()
    conn.close()
    if not result:
        return jsonify({"error": "Трек не найден"}), 404
    return jsonify({"url": f"https://api.telegram.org/file/bot <7755566426:AAFh-P-7ZrjLtww5WDibYyFkjXJPS4Py1r4>/{result['file_id']}"})

if __name__ == "__main__":
    app.run(debug=True)