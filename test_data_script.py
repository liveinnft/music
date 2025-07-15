#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания тестовых данных в базе данных
"""

from database import init_db, add_playlist, add_song, get_playlists
import sqlite3

def create_test_playlists():
    """Создает тестовые плейлисты"""
    print("🎵 Создание тестовых плейлистов...")
    
    # Инициализируем базу данных
    init_db()
    
    # Создаем тестовые плейлисты
    test_playlists = [
        "Любимые треки",
        "Рок музыка", 
        "Электронная музыка",
        "Классика",
        "Джаз"
    ]
    
    for playlist_name in test_playlists:
        try:
            add_playlist(playlist_name)
            print(f"✅ Плейлист '{playlist_name}' создан")
        except Exception as e:
            print(f"❌ Ошибка при создании плейлиста '{playlist_name}': {e}")
    
    # Добавляем тестовые треки (с фиктивными file_id)
    test_songs = [
        ("Bohemian Rhapsody", "Queen", "test_file_id_1", 1),
        ("Stairway to Heaven", "Led Zeppelin", "test_file_id_2", 1),
        ("Hotel California", "Eagles", "test_file_id_3", 1),
        
        ("Smells Like Teen Spirit", "Nirvana", "test_file_id_4", 2),
        ("Back in Black", "AC/DC", "test_file_id_5", 2),
        ("Sweet Child O' Mine", "Guns N' Roses", "test_file_id_6", 2),
        
        ("One More Time", "Daft Punk", "test_file_id_7", 3),
        ("Levels", "Avicii", "test_file_id_8", 3),
        ("Titanium", "David Guetta", "test_file_id_9", 3),
        
        ("Symphony No. 9", "Beethoven", "test_file_id_10", 4),
        ("Canon in D", "Pachelbel", "test_file_id_11", 4),
        
        ("Take Five", "Dave Brubeck", "test_file_id_12", 5),
        ("So What", "Miles Davis", "test_file_id_13", 5),
    ]
    
    print("\n🎶 Добавление тестовых треков...")
    for title, author, file_id, playlist_id in test_songs:
        try:
            add_song(title, author, file_id, playlist_id)
            print(f"✅ Трек '{title}' добавлен")
        except Exception as e:
            print(f"❌ Ошибка при добавлении трека '{title}': {e}")

def show_current_data():
    """Показывает текущие данные в базе"""
    print("\n📊 Текущие данные в базе:")
    
    playlists = get_playlists()
    if not playlists:
        print("❌ Нет плейлистов в базе данных")
        return
    
    for playlist in playlists:
        print(f"\n🎧 Плейлист: {playlist['name']} (ID: {playlist['id']})")
        
        # Получаем треки для этого плейлиста
        conn = sqlite3.connect('music.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM songs WHERE playlist_id = ?", (playlist['id'],))
        songs = cur.fetchall()
        conn.close()
        
        if songs:
            for song in songs:
                print(f"  • {song['title']} - {song['author']}")
        else:
            print("  (нет треков)")

def clear_database():
    """Очищает базу данных"""
    response = input("\n⚠️  Вы уверены, что хотите очистить базу данных? (y/N): ")
    if response.lower() != 'y':
        print("Операция отменена")
        return
    
    try:
        conn = sqlite3.connect('music.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM songs")
        cur.execute("DELETE FROM playlists")
        conn.commit()
        conn.close()
        print("✅ База данных очищена")
    except Exception as e:
        print(f"❌ Ошибка при очистке базы данных: {e}")

if __name__ == "__main__":
    print("🎵 Управление тестовыми данными для музыкального бота\n")
    
    while True:
        print("\nВыберите действие:")
        print("1. Создать тестовые плейлисты и треки")
        print("2. Показать текущие данные")
        print("3. Очистить базу данных")
        print("4. Выйти")
        
        choice = input("\nВведите номер действия: ").strip()
        
        if choice == "1":
            create_test_playlists()
        elif choice == "2":
            show_current_data()
        elif choice == "3":
            clear_database()
        elif choice == "4":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
