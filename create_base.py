import sqlite3
import os

def create_database():
    # Получаем директорию скрипта
    dirname = os.path.dirname(__file__)
    if dirname:
        os.chdir(dirname)

    db_path = "ats_database.db"

    try:
        # Проверяем, существует ли уже база данных
        if os.path.exists(db_path):
            print("БД уже существует.")
            return

        # Создаем новую базу данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Создаем таблицу абонентов (структура соответствует основной программе)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT,
                subscriber_type TEXT CHECK(subscriber_type IN ('частный', 'организация')),
                subscription_debt TEXT DEFAULT 'Нет',
                damage_debt TEXT DEFAULT 'Нет',
                tariff TEXT DEFAULT 'Базовый'
            )
        ''')

        # Создаем таблицу пользователей для авторизации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        ''')

        # Добавляем администратора по умолчанию
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES ('admin', 'admin123', 'admin')
        ''')

        # Добавляем обычного пользователя
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES ('user', 'user123', 'user')
        ''')

        conn.commit()
        print("База данных успешно создана!")
        print("Учетные записи:")
        print("Администратор - логин: admin, пароль: admin123")
        print("Пользователь - логин: user, пароль: user123")

    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
