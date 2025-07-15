#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для диагностики проблем с базой данных
"""

import sqlite3
import os
from database import get_playlists, get_db_connection

def check_database_file():
    """Проверяет существование файла базы данных"""
    print("🔍 Проверка файла базы данных:")
    
    # Проверяем в текущей директории
    current_dir = os.getcwd()
    print(f"Текущая директория: {current_dir}")
    
    db_files = []
    for file in os.listdir(current_dir):
        if file.endswith('.db'):
            db_files.append(file)
    
    print(f"Найденные .db файлы: {db_files}")
    
    # Проверяем конкретно music.db
    if os.path.exists('music.db'):
        size = os.path.getsize('music.db')
        print(f"✅ music.db существует, размер: {size} байт")
        return True
    else:
        print("❌ music.db не найдена")
        return False

def check_database_structure():
    """Проверяет структуру базы данных"""
    print("\n🔍 Проверка структуры базы данных:")
    
    try:
        conn = sqlite3.connect('music.db')
        cur = conn.cursor()
        
        # Проверяем таблицы
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print(f"Найденные таблицы: {[table[0] for table in tables]}")
        
        # Проверяем содержимое таблицы playlists
        cur.execute("SELECT COUNT(*) FROM playlists")
        playlist_count = cur.fetchone()[0]
        print(f"Количество плейлистов: {playlist_count}")
        
        if playlist_count > 0:
            cur.execute("SELECT * FROM playlists")
            playlists = cur.fetchall()
            print("Плейлисты в базе:")
            for playlist in playlists:
                print(f"  - ID: {playlist[0]}, Название: {playlist[1]}")
        
        # Проверяем содержимое таблицы songs
        cur.execute("SELECT COUNT(*) FROM songs")
        song_count = cur.fetchone()[0]
        print(f"Количество треков: {song_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке структуры: {e}")

def check_database_functions():
    """Проверяет функции из database.py"""
    print("\n🔍 Проверка функций database.py:")
    
    try:
        playlists = get_playlists()
        print(f"get_playlists() возвращает: {playlists}")
        print(f"Тип данных: {type(playlists)}")
        
        if playlists:
            print("Детали плейлистов:")
            for pl in playlists:
                print(f"  - {pl} (тип: {type(pl)})")
        
    except Exception as e:
        print(f"❌ Ошибка в get_playlists(): {e}")

def check_web_app_path():
    """Проверяет пути в веб-приложении"""
    print("\n🔍 Проверка путей в веб-приложении:")
    
    # Проверяем, где находится web_app
    web_app_dir = os.path.join(os.getcwd(), 'web_app')
    print(f"Директория web_app: {web_app_dir}")
    print(f"web_app существует: {os.path.exists(web_app_dir)}")
    
    # Проверяем, где ищет базу данных web_app
    if os.path.exists(web_app_dir):
        os.chdir(web_app_dir)
        print(f"Изменили директорию на: {os.getcwd()}")
        
        # Проверяем наличие music.db в директории web_app
        local_db = os.path.exists('music.db')
        parent_db = os.path.exists('../music.db')
        
        print(f"music.db в web_app/: {local_db}")
        print(f"music.db в родительской директории: {parent_db}")
        
        # Возвращаемся в исходную директорию
        os.chdir('..')

def fix_database_path():
    """Исправляет проблему с путями к базе данных"""
    print("\n🔧 Попытка исправить проблему с путями:")
    
    # Проверяем, где находится music.db
    root_db = os.path.exists('music.db')
    web_app_db = os.path.exists('web_app/music.db')
    
    if root_db and not web_app_db:
        print("База данных найдена в корне проекта")
        print("Возможно, проблема в том, что web_app ищет базу в своей директории")
        
        # Предлагаем решение
        print("\n💡 Решения:")
        print("1. Скопировать music.db в web_app/")
        print("2. Изменить путь в database.py на абсолютный")
        print("3. Запускать web_app из корневой директории")
        
        choice = input("\nВыберите решение (1-3) или нажмите Enter для пропуска: ")
        
        if choice == "1":
            import shutil
            shutil.copy('music.db', 'web_app/music.db')
            print("✅ music.db скопирована в web_app/")
        elif choice == "2":
            print("Нужно изменить DB_NAME в database.py на абсолютный путь")
        elif choice == "3":
            print("Запускайте 'python web_app/app.py' из корня проекта")

if __name__ == "__main__":
    print("🔧 Диагностика проблем с базой данных\n")
    
    check_database_file()
    check_database_structure()
    check_database_functions()
    check_web_app_path()
    fix_database_path()
    
    print("\n✅ Диагностика завершена")
