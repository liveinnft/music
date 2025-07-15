import sqlite3
import os
from os import path

# Используем абсолютный путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'music.db')

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
        print(f"✅ База данных инициализирована: {DB_NAME}")
    else:
        print(f"📂 Используется существующая база данных: {DB_NAME}")

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
        raise e
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
        raise e
    finally:
        conn.close()

def get_songs_by_playlist(playlist_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.title, s.author, s.file_id, p.name AS playlist_name
        FROM songs s
        JOIN playlists p ON s.playlist_id = p.id
        WHERE s.playlist_id = ?
    """, (playlist_id,))
    songs = cur.fetchall()
    conn.close()
    return songs

def get_song_by_id(song_id):
    """Получает трек по ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
    song = cur.fetchone()
    conn.close()
    return song

# Функция для отладки
def debug_database():
    """Выводит содержимое базы данных для отладки"""
    print(f"🔍 Отладка базы данных: {DB_NAME}")
    print(f"Файл существует: {os.path.exists(DB_NAME)}")
    
    if os.path.exists(DB_NAME):
        print(f"Размер файла: {os.path.getsize(DB_NAME)} байт")
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Проверяем плейлисты
            cur.execute("SELECT COUNT(*) FROM playlists")
            playlist_count = cur.fetchone()[0]
            print(f"Количество плейлистов: {playlist_count}")
            
            if playlist_count > 0:
                cur.execute("SELECT * FROM playlists")
                playlists = cur.fetchall()
                print("Плейлисты:")
                for pl in playlists:
                    print(f"  - {pl['id']}: {pl['name']}")
            
            # Проверяем треки
            cur.execute("SELECT COUNT(*) FROM songs")
            song_count = cur.fetchone()[0]
            print(f"Количество треков: {song_count}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка при отладке: {e}")