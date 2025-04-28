# db.py
import sqlite3
import time

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY,
    username  TEXT,
    credits   INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS reserved_numbers (
    user_id      INTEGER,
    phone_number TEXT,
    session_file TEXT,
    timestamp    INTEGER
)
''')

conn.commit()

def add_user(user_id, username):
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username)
    )
    conn.commit()

def get_credits(user_id):
    cursor.execute('SELECT credits FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def add_credit(user_id, amount):
    cursor.execute(
        'UPDATE users SET credits = credits + ? WHERE user_id = ?',
        (amount, user_id)
    )
    conn.commit()

def remove_credit(user_id, amount):
    cursor.execute(
        'UPDATE users SET credits = credits - ? WHERE user_id = ?',
        (amount, user_id)
    )
    conn.commit()

def reserve_number(user_id, phone_number, session_file):
    cursor.execute('''
        INSERT INTO reserved_numbers (user_id, phone_number, session_file, timestamp) 
        VALUES (?, ?, ?, ?)
    ''', (user_id, phone_number, session_file, int(time.time())))
    conn.commit()

def get_reserved_number(user_id):
    cursor.execute('''
        SELECT phone_number, session_file, timestamp 
          FROM reserved_numbers 
         WHERE user_id = ?
    ''', (user_id,))
    return cursor.fetchone()

def free_expired_reservations(timeout):
    now = int(time.time())
    cursor.execute(
        'DELETE FROM reserved_numbers WHERE ? - timestamp > ?',
        (now, timeout)
    )
    conn.commit()

def release_number(user_id):
    cursor.execute('DELETE FROM reserved_numbers WHERE user_id = ?', (user_id,))
    conn.commit()

def is_number_reserved(phone_number):
    cursor.execute(
        'SELECT 1 FROM reserved_numbers WHERE phone_number = ?',
        (phone_number,)
    )
    return cursor.fetchone() is not None
