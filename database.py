import sqlite3
from os import path

DB_NAME = 'music.db'

def init_db():
    if not path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        cur.execute('''
            CREATE TABLE songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                author TEXT,
                file_id TEXT,
                playlist_id INTEGER,
                FOREIGN KEY(playlist_id) REFERENCES playlists(id)
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована.")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Чтобы получать строки как словари
    return conn

def get_playlists():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM playlists")
    playlists = cur.fetchall()
    conn.close()
    return playlists

def add_playlist(name):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
        conn.commit()
        print(f"[+] Плейлист '{name}' создан.")
    except sqlite3.IntegrityError as e:
        print(f"[!] Ошибка создания плейлиста: {e}")
    finally:
        conn.close()

def add_song(title, author, file_id, playlist_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO songs (title, author, file_id, playlist_id) VALUES (?, ?, ?, ?)",
            (title, author, file_id, playlist_id)
        )
        conn.commit()
        print(f"[+] Трек '{title}' добавлен в плейлист ID={playlist_id}.")
    except Exception as e:
        print(f"[!] Ошибка при добавлении трека: {e}")
    finally:
        conn.close()

def get_songs_by_playlist(playlist_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.title, s.author, p.name AS playlist_name
        FROM songs s
        JOIN playlists p ON s.playlist_id = p.id
        WHERE s.playlist_id = ?
    """, (playlist_id,))
    songs = cur.fetchall()
    conn.close()
    return songs