import sqlite3
from datetime import datetime, timezone

DB_PATH = "aurix.db"

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def now():
    return datetime.now(timezone.utc).isoformat()

def init_db():
    c = conn(); x = c.cursor()
    x.execute("""CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        balance REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
        referral_code TEXT, referred_by INTEGER
    )""")
    x.execute("""CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL,
        kind TEXT NOT NULL, amount REAL NOT NULL, fee REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending', reference TEXT UNIQUE,
        created_at TEXT NOT NULL, updated_at TEXT
    )""")
    x.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL,
        kind TEXT NOT NULL, amount REAL NOT NULL, fee REAL NOT NULL DEFAULT 0,
        reference TEXT, note TEXT, created_at TEXT NOT NULL
    )""")
    # Safe migration for V3 databases.
    cols = {r[1] for r in x.execute("PRAGMA table_info(users)").fetchall()}
    if "referral_code" not in cols:
        x.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
    if "referred_by" not in cols:
        x.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
    c.commit(); c.close()

def get_user(tid):
    c=conn(); r=c.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)).fetchone(); c.close(); return dict(r) if r else None

def create_user(tid, username, first_name, referred_by=None):
    code = f"AURIX-{tid}"
    c=conn(); c.execute("INSERT OR IGNORE INTO users (telegram_id,username,first_name,created_at,referral_code,referred_by) VALUES (?,?,?,?,?,?)", (tid,username,first_name,now(),code,referred_by)); c.commit(); c.close()

def get_balance(tid):
    u=get_user(tid); return u["balance"] if u else 0

def adjust_balance(tid, delta):
    c=conn(); c.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?", (delta,tid)); c.commit(); c.close()

def create_request(tid,kind,amount,fee,reference):
    c=conn(); c.execute("INSERT INTO requests (telegram_id,kind,amount,fee,status,reference,created_at) VALUES (?,?,?,?,?,?,?)", (tid,kind,amount,fee,"pending",reference,now())); c.commit(); c.close(); return reference

def get_request(rid):
    c=conn(); r=c.execute("SELECT * FROM requests WHERE id=?",(rid,)).fetchone(); c.close(); return dict(r) if r else None

def get_requests(status="pending",kind=None):
    c=conn(); q="SELECT * FROM requests WHERE status=?"; args=[status]
    if kind: q += " AND kind=?"; args.append(kind)
    rows=c.execute(q+" ORDER BY id DESC",args).fetchall(); c.close(); return [dict(r) for r in rows]

def update_request(rid,status):
    c=conn(); row=c.execute("SELECT * FROM requests WHERE id=? AND status='pending'",(rid,)).fetchone()
    if not row: c.close(); return None
    c.execute("UPDATE requests SET status=?,updated_at=? WHERE id=?",(status,now(),rid)); c.commit(); c.close(); return dict(row)

def add_transaction(tid,kind,amount,fee=0,reference=None,note=""):
    c=conn(); c.execute("INSERT INTO transactions (telegram_id,kind,amount,fee,reference,note,created_at) VALUES (?,?,?,?,?,?,?)",(tid,kind,amount,fee,reference,note,now())); c.commit(); c.close()

def get_transactions(tid,limit=15):
    c=conn(); rows=c.execute("SELECT * FROM transactions WHERE telegram_id=? ORDER BY id DESC LIMIT ?",(tid,limit)).fetchall(); c.close(); return [dict(r) for r in rows]

def get_stats():
    c=conn(); users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]; pending=c.execute("SELECT COUNT(*) FROM requests WHERE status='pending'").fetchone()[0]; volume=c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE kind IN ('deposit','withdrawal')").fetchone()[0]; c.close(); return users,pending,volume
