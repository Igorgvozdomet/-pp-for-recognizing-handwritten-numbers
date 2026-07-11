import sqlite3
from config import DB_NAME

def init_db():
    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                login TEXT,
                pass TEXT)""")
    db.commit()
    db.close()

def register_user(login, password):
    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()
    
    # Проверяем, есть ли уже такой логин
    cur.execute(f"SELECT * FROM users WHERE login='{login}'")
    if cur.fetchone() is not None:
        db.close()
        return False  # пользователь уже существует
    
    cur.execute(f"INSERT INTO users VALUES(NULL, '{login}', '{password}')")
    db.commit()
    db.close()
    return True  # успешно зарегистрирован

def check_user(login, password):
    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()
    cur.execute(f"SELECT * FROM users WHERE login='{login}' AND pass='{password}'")
    result = cur.fetchone()
    db.close()
    return result is not None
