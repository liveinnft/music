from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import sqlite3
import os
import sys

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database import init_db, get_playlists, get_songs_by_playlist, get_song_by_id

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Токен бота (в продакшене лучше использовать переменные окружения)
BOT_TOKEN = "7755566426:AAFh-P-7ZrjLtww5WDibYyFkjXJPS4Py1r4"

# Инициализируем базу данных
init_db()

@app.route("/")
def home():
    return {"message": "Music Bot API", "status": "running"}

@app.route("/api/playlists")
def api_playlists():
    """Получить все плейлисты"""
    try:
        playlists = get_playlists()
        return jsonify({
            "success": True,
            "playlists": [dict(pl) for pl in playlists]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/playlist/<int:playlist_id>")
def api_playlist(playlist_id):
    """Получить треки плейлиста"""
    try:
        songs = get_songs_by_playlist(playlist_id)
        if not songs:
            return jsonify({
                "success": False,
                "error": "Плейлист не найден или пуст"
            }), 404
        
        return jsonify({
            "success": True,
            "playlist_name": songs[0]["playlist_name"],
            "songs": [dict(song) for song in songs]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/song/<int:song_id>")
def api_song(song_id):
    """Получить ссылку на файл песни"""
    try:
        song = get_song_by_id(song_id)
        if not song:
            return jsonify({
                "success": False,
                "error": "Трек не найден"
            }), 404
        
        file_id = song['file_id']
        
        # Получаем информацию о файле из Telegram API
        file_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        response = requests.get(file_info_url)
        
        if response.status_code == 200:
            file_info = response.json()
            if file_info.get('ok'):
                file_path = file_info['result']['file_path']
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                
                return jsonify({
                    "success": True,
                    "url": file_url,
                    "title": song['title'],
                    "author": song['author']
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Не удалось получить информацию о файле"
                }), 500
        else:
            return jsonify({
                "success": False,
                "error": "Ошибка при обращении к Telegram API"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/health")
def health_check():
    """Проверка работоспособности API"""
    try:
        # Проверяем подключение к базе данных
        playlists = get_playlists()
        
        # Проверяем доступность Telegram API
        test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(test_url, timeout=5)
        telegram_ok = response.status_code == 200
        
        return jsonify({
            "success": True,
            "database": "OK",
            "telegram_api": "OK" if telegram_ok else "ERROR",
            "playlists_count": len(playlists)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)