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
# Настраиваем CORS для работы с GitHub Pages
CORS(app, origins=['https://yourusername.github.io', 'http://localhost:*'])

# Токен бота (лучше использовать переменные окружения)
BOT_TOKEN = os.environ.get('BOT_TOKEN', "7755566426:AAFh-P-7ZrjLtww5WDibYyFkjXJPS4Py1r4")

# Инициализируем базу данных
init_db()

@app.route("/")
def home():
    return jsonify({
        "message": "Music Bot API", 
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "playlists": "/api/playlists",
            "playlist": "/api/playlist/<id>",
            "song": "/api/song/<id>",
            "health": "/api/health"
        }
    })

@app.route("/api/playlists", methods=['GET'])
def api_playlists():
    """Получить все плейлисты"""
    try:
        playlists = get_playlists()
        return jsonify({
            "success": True,
            "playlists": [dict(pl) for pl in playlists],
            "count": len(playlists)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/playlist/<int:playlist_id>", methods=['GET'])
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
            "playlist_id": playlist_id,
            "playlist_name": songs[0]["playlist_name"],
            "songs": [dict(song) for song in songs],
            "count": len(songs)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/song/<int:song_id>", methods=['GET'])
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
        
        try:
            response = requests.get(file_info_url, timeout=10)
            response.raise_for_status()
            
            file_info = response.json()
            if file_info.get('ok'):
                file_path = file_info['result']['file_path']
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                
                return jsonify({
                    "success": True,
                    "url": file_url,
                    "title": song['title'],
                    "author": song['author'],
                    "song_id": song_id,
                    "playlist_id": song['playlist_id']
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Telegram API ошибка: {file_info.get('description', 'Неизвестная ошибка')}"
                }), 500
                
        except requests.exceptions.RequestException as e:
            return jsonify({
                "success": False,
                "error": f"Ошибка соединения с Telegram API: {str(e)}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/health", methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    try:
        # Проверяем подключение к базе данных
        playlists = get_playlists()
        
        # Проверяем доступность Telegram API
        telegram_ok = False
        telegram_error = ""
        try:
            test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                telegram_ok = data.get('ok', False)
            else:
                telegram_error = f"HTTP {response.status_code}"
        except Exception as e:
            telegram_error = str(e)
        
        # Подсчитываем общее количество треков
        total_songs = 0
        for playlist in playlists:
            songs = get_songs_by_playlist(playlist['id'])
            total_songs += len(songs)
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "database": "OK",
            "telegram_api": "OK" if telegram_ok else f"ERROR: {telegram_error}",
            "statistics": {
                "playlists_count": len(playlists),
                "total_songs": total_songs
            },
            "bot_token_set": bool(BOT_TOKEN),
            "timestamp": str(int(time.time()) if 'time' in globals() else 0)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "unhealthy"
        }), 500

@app.route("/api/stats", methods=['GET'])
def api_stats():
    """Получить статистику"""
    try:
        playlists = get_playlists()
        stats = {
            "playlists": [],
            "total_songs": 0
        }
        
        for playlist in playlists:
            songs = get_songs_by_playlist(playlist['id'])
            playlist_info = {
                "id": playlist['id'],
                "name": playlist['name'],
                "songs_count": len(songs)
            }
            stats["playlists"].append(playlist_info)
            stats["total_songs"] += len(songs)
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Обработчик ошибок
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint не найден",
        "code": 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Внутренняя ошибка сервера",
        "code": 500
    }), 500

if __name__ == "__main__":
    import time
    app.run(debug=True, host='0.0.0.0', port=5000)