from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import logging
from database import *
init_db()

# Логирование
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.error(f"Ошибка при создании плейлиста: {e}")
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

# --- Main function ---
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