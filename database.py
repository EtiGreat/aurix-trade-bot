import sqlite3
from datetime import datetime, timezone
from config import DATABASE_URL

DB_PATH = "aurix.db"

def conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            amount REAL NOT NULL,
            fee REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            reference TEXT,
            created_at TEXT NOT NULL
        )
    """)
    c.commit()
    c.close()

def now():
    return datetime.now(timezone.utc).isoformat()

def get_user(telegram_id):
    c = conn()
    row = c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    c.close()
    return row

def create_user(telegram_id, username, first_name):
    c = conn()
    c.execute(
        "INSERT OR IGNORE INTO users "
        "(telegram_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
        (telegram_id, username, first_name, now())
    )
    c.commit()
    c.close()

def get_balance(telegram_id):
    c = conn()
    row = c.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    c.close()
    return row[0] if row else 0

def add_transaction(telegram_id, kind, amount, fee=0, status="pending", reference=""):
    c = conn()
    c.execute(
        "INSERT INTO transactions "
        "(telegram_id, kind, amount, fee, status, reference, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (telegram_id, kind, amount, fee, status, reference, now())
    )
    c.commit()
    c.close()
