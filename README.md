# 📦 Проект: Telegram-бот с веб-интерфейсом для управления музыкальными плейлистами

---

## 🌐 О проекте

Проект представляет собой **Telegram-бота**, который позволяет пользователям:
- Загружать аудиофайлы (`.mp3`, `.ogg` и голосовые сообщения).
- Добавлять их в **музыкальные плейлисты**.
- Просматривать, управлять и воспроизводить треки как **в чате Telegram**, так и через **веб-интерфейс на сайте**.

Все данные хранятся в **SQLite базе данных (`music.db`)**. Для веб-части используется **Flask**, а для бота — **python-telegram-bot**.

---

## 🧱 Структура проекта

```
music_bot/
├── bot.py                      ← Логика Telegram-бота
├── database.py                 ← Работа с SQLite БД
└── web_app/
    ├── app.py                  ← Flask-сервер
    ├── templates/
    │   ├── index.html          ← Главная страница сайта
    │   └── playlist.html       ← Страница с плейлистом
    └── static/                 ← Статические файлы (если потребуются)
```

---

## 🛠 Технологии и зависимости

### ✅ Python-библиотеки:

- `python-telegram-bot==22.2` – для работы с Telegram API.
- `flask` – микрофреймворк для создания веб-приложения.
- `gunicorn` – сервер WSGI для запуска приложения.
- `pytz` – для корректной работы с временными зонами (используется библиотекой APScheduler).

### ✅ HTML/CSS/JS:

- Bootstrap 5 – фронтенд-библиотека для красивого интерфейса.
- JavaScript – логика проигрывания аудио на клиенте.

---

## 📂 Файлы проекта

---

## 🔹 `bot.py` — логика Telegram-бота

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import logging
from database import *
init_db()

# Логирование
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне аудиофайл, чтобы добавить его в плейлист.")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = update.message.audio or update.message.voice
    if not audio:
        await update.message.reply_text("Пришли аудиофайл или голосовое сообщение.")
        return

    user_data = context.user_data
    user_data['file_id'] = audio.file_id
    user_data['title'] = audio.title or "Без названия"
    user_data['author'] = audio.performer or "Неизвестный"

    playlists = get_playlists()
    keyboard = [
        [InlineKeyboardButton(pl['name'], callback_data=f"select_playlist_{pl['id']}")] for pl in playlists
    ]
    keyboard.append([InlineKeyboardButton("Создать новый плейлист", callback_data="new_playlist")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери плейлист:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_data = context.user_data

    if data.startswith("select_playlist_"):
        playlist_id = int(data.split("_")[2])
        title = user_data.get('title')
        author = user_data.get('author')
        file_id = user_data.get('file_id')

        if not all([title, author, file_id]):
            await query.edit_message_text("Ошибка: недостаточно информации о треке.")
            return

        add_song(title, author, file_id, playlist_id)
        await query.edit_message_text(f"Трек '{title}' добавлен в плейлист!")
        user_data.clear()

    elif data == "new_playlist":
        await query.edit_message_text("Введите название нового плейлиста:")
        user_data['action'] = 'create_playlist'

async def create_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    if user_data.get('action') == 'create_playlist':
        name = update.message.text.strip()
        try:
            add_playlist(name)
            await update.message.reply_text(f"Плейлист '{name}' создан!")
        except Exception as e:
            await update.message.reply_text("Ошибка при создании плейлиста.")
        user_data.pop('action')

async def show_all_songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    playlists = get_playlists()
    if not playlists:
        await update.message.reply_text("Нет доступных плейлистов.")
        return

    keyboard = [
        [InlineKeyboardButton(pl['name'], callback_data=f"view_playlist_{pl['id']}")] for pl in playlists
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери плейлист для просмотра:", reply_markup=reply_markup)

async def view_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    playlist_id = int(data.split("_")[2])

    songs = get_songs_by_playlist(playlist_id)
    if not songs:
        await query.edit_message_text("В этом плейлисте пока нет треков.")
        return

    playlist_name = songs[0]['playlist_name']
    text = f"🎧 Плейлист: {playlist_name}\n\n"
    for song in songs:
        text += f"{song['title']} - {song['author']}\n"

    keyboard = [
        [InlineKeyboardButton(f"{song['title']} - {song['author']}", callback_data=f"play_song_{song['id']}")]
        for song in songs
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    song_id = int(query.data.split("_")[2])

    conn = sqlite3.connect('music.db')
    cur = conn.cursor()
    cur.execute("SELECT file_id FROM songs WHERE id = ?", (song_id,))
    result = cur.fetchone()
    conn.close()

    if result and result['file_id']:
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=result['file_id'])
    else:
        await query.edit_message_text("Трек не найден.")

if __name__ == '__main__':
    application = ApplicationBuilder().token("7755566426:AAFh-P-7ZrjLtww5WDibYyFkjXJPS4Py1r4").build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, handle_audio))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler('songs', show_all_songs))
    application.add_handler(CallbackQueryHandler(view_playlist, pattern=r"^view_playlist_\d+$"))
    application.add_handler(CallbackQueryHandler(play_song, pattern=r"^play_song_\d+$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, create_playlist))

    print("Bot started...")
    application.run_polling()
```

---

## 🔹 `database.py` — работа с базой данных

```python
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
```

---

## 🔹 `web_app/app.py` — Flask-сервер

```python
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
    return jsonify({"url": f"https://api.telegram.org/file/bot<YOUR_BOT_TOKEN>/{result['file_id']}"})

if __name__ == "__main__":
    app.run(debug=True)
```

---

## 🔹 `web_app/templates/index.html` — главная страница сайта

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Музыкальный плейлист</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
        }
        .playlist-card {
            cursor: pointer;
            transition: transform 0.2s;
        }
        .playlist-card:hover {
            transform: scale(1.02);
        }
    </style>
</head>
<body>
    <div class="container py-5">
        <h1 class="text-center mb-4">Плейлисты</h1>
        <div class="row row-cols-1 row-cols-md-2 g-4">
            {% for pl in playlists %}
                <div class="col">
                    <div class="card playlist-card shadow-sm">
                        <div class="card-body d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h5 class="card-title">{{ pl['name'] }}</h5>
                            </div>
                            <a href="/playlist/{{ pl['id'] }}" class="btn btn-outline-success ms-2">▶</a>
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
```

---

## 🔹 `web_app/templates/playlist.html` — страница с треками

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{ playlist_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
        }
        .song-card {
            cursor: pointer;
            transition: transform 0.2s;
        }
        .song-card:hover {
            transform: scale(1.02);
        }
    </style>
</head>
<body>
    <div class="container py-5">
        <h1 class="text-center mb-4">{{ playlist_name }}</h1>
        <div class="row row-cols-1 row-cols-md-2 g-4">
            {% for song in songs %}
                <div class="col">
                    <div class="card song-card shadow-sm">
                        <div class="card-body d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h5 class="card-title">{{ song.title }}</h5>
                                <p class="card-text text-muted">{{ song.author }}</p>
                            </div>
                            <button onclick="playSong('{{ song.id }}')" class="btn btn-outline-success ms-2">
                                ▶
                            </button>
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>
        <div class="mt-4">
            <audio id="player" controls style="width: 100%; max-width: 600px;"></audio>
        </div>
    </div>
    <script>
        const player = document.getElementById('player');
        async function playSong(songId) {
            try {
                const response = await fetch(`/song/${songId}`);
                if (!response.ok) throw new Error("Ошибка загрузки трека");
                const data = await response.json();
                player.src = data.url;
                player.play();
            } catch (error) {
                alert("Не удалось воспроизвести трек.");
                console.error(error);
            }
        }

        window.onload = () => {
            const firstButton = document.querySelector('.song-card button');
            if (firstButton && firstButton.hasAttribute('onclick')) {
                const songId = firstButton.getAttribute('onclick').match(/'([^']+)'/)[1];
                playSong(songId);
            }
        };
    </script>
</body>
</html>
```

---

## 🔹 `requirements.txt` — зависимости

```
python-telegram-bot==22.2
flask
gunicorn
pytz
```

---

## 🔍 Возможные проблемы и их решение

| Проблема | Причина | Как исправить |
|----------|---------|---------------|
| Нет таблиц в БД | База не инициализирована | Убедитесь, что вызывается `init_db()` |
| Не отображаются плейлисты | Ошибки в шаблонах | Используйте `{{ pl['name'] }}`, а не `{{ pl[1] }}` |
| Не отображаются треки | Ошибки в обращении к данным | Используйте `{{ song.title }}`, а не `{{ song[1] }}` |
| Ошибка: `sqlite3.OperationalError: no such table: playlists` | Таблицы не созданы | Вызовите `init_db()` при запуске |
| Ошибка: `ModuleNotFoundError: No module named 'database'` | Неправильный путь | Используйте `sys.path.append(...)` или перенесите файл в нужную папку |
| Аудио не воспроизводится | Неверный URL | Убедитесь, что в `/song/<song_id>` возвращается правильный `file_id` |

---

## 🚀 Как запустить проект

### 🔹 Шаг 1: Создание виртуального окружения

```bash
cd C:\Users\Вячеслав\PythonProjects\music
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### 🔹 Шаг 2: Запуск бота

```bash
python bot.py
```

---

### 🔹 Шаг 3: Запуск веб-приложения

```bash
cd web_app
python app.py
```

---

### 🔹 Шаг 4: Перейти на сайт

Откройте в браузере:

```
http://localhost:5000
```

---

## 🎵 Что умеет бот

| Команда / действие | Что происходит |
|--------------------|----------------|
| `/start`           | Приветствие и инструкция |
| Отправка аудиофайла | Предлагает выбрать плейлист |
| Выбор плейлиста    | Добавляет трек в БД |
| `/songs`           | Отображает список плейлистов |
| Клик по плейлисту  | Открывает страницу с треками |
| Клик по треку      | Воспроизводит аудио |

---

## 🖥 Что умеет сайт

| URL | Что делает |
|------|------------|
| `/` | Отображает все плейлисты |
| `/playlist/<id>` | Отображает треки выбранного плейлиста |
| `/song/<id>` | Возвращает ссылку на аудио из Telegram по `file_id` |

---

## ⚠️ Важно!

- В файле `app.py` замените `<YOUR_BOT_TOKEN>` на реальный токен телеграм-бота.
- Все файлы должны быть в правильных папках.
- Убедитесь, что `music.db` находится в корне проекта.
- Не используйте `song[0]`, `song[1]` — это старый стиль. Используйте `song['id']`, `song['title']`.

---

## 🧩 Архитектура

| Компонент | Описание |
|-----------|----------|
| `bot.py` | Обрабатывает команды и взаимодействует с пользователем в Telegram |
| `database.py` | Хранит данные о плейлистах и треках в SQLite |
| `web_app/app.py` | Серверная часть сайта, подключённая к БД |
| `templates/*` | Шаблоны HTML-страниц |
| `requirements.txt` | Зависимости для установки |

---

## 🔄 Возможные улучшения

- Добавить автопроигрывание следующего трека.
- Реализовать удаление/редактирование треков и плейлистов.
- Поддержка нескольких пользователей.
- Добавить пагинацию при большом количестве треков.
- Сделать веб-интерфейс более дружелюбным (например, использовать JS-рендеринг).

---

## 🧪 Проверка работоспособности

1. Запустите бота.
2. Отправьте аудиофайл.
3. Выберите или создайте плейлист.
4. Зайдите на сайт и проверьте наличие плейлиста и треков.
5. Нажмите на кнопку ▶ — должно воспроизвестись аудио.

---

## 🧾 Замечания по передаче проекта

Когда ты будешь передавать проект другому разработчику, **обязательно**:

- Убедись, что он имеет доступ к `music.db`.
- Передай `requirements.txt` и инструкции по установке.
- Укажи, где взять токен бота.
- Объясни, как работает логика добавления треков.
- Расскажи, как можно расширить функционал (добавление, удаление, редактирование).

---

Если ты хочешь, я могу подготовить:
- Документацию в формате PDF или Markdown.
- README.md для GitHub.
- Скрипт для автоматической установки.
- Схему БД в виде диаграммы.

