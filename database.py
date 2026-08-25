import sqlite3
from datetime import datetime, timezone
DB_PATH="aurix.db"
def conn(): return sqlite3.connect(DB_PATH)
def now(): return datetime.now(timezone.utc).isoformat()
def init_db():
    c=conn(); x=c.cursor()
    x.execute("CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, balance REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL)")
    x.execute("CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL, kind TEXT NOT NULL, amount REAL NOT NULL, fee REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending', reference TEXT UNIQUE, created_at TEXT NOT NULL, updated_at TEXT)")
    c.commit(); c.close()
def get_user(tid):
    c=conn(); r=c.execute("SELECT telegram_id FROM users WHERE telegram_id=?",(tid,)).fetchone(); c.close(); return r
def create_user(tid,username,first_name):
    c=conn(); c.execute("INSERT OR IGNORE INTO users (telegram_id,username,first_name,created_at) VALUES (?,?,?,?)",(tid,username,first_name,now())); c.commit(); c.close()
def get_balance(tid):
    c=conn(); r=c.execute("SELECT balance FROM users WHERE telegram_id=?",(tid,)).fetchone(); c.close(); return r[0] if r else 0
def create_request(tid,kind,amount,fee,reference):
    c=conn(); c.execute("INSERT INTO requests (telegram_id,kind,amount,fee,status,reference,created_at) VALUES (?,?,?,?,?,?,?)",(tid,kind,amount,fee,"pending",reference,now())); c.commit(); c.close(); return reference
def get_requests(status="pending",kind=None):
    c=conn()
    q="SELECT id,telegram_id,kind,amount,fee,status,reference,created_at FROM requests WHERE status=?"
    args=[status]
    if kind: q+=" AND kind=?"; args.append(kind)
    rows=c.execute(q+" ORDER BY id DESC",args).fetchall(); c.close()
    keys=["id","telegram_id","kind","amount","fee","status","reference","created_at"]
    return [dict(zip(keys,r)) for r in rows]
def update_request(rid,status):
    c=conn(); row=c.execute("SELECT id,telegram_id,kind,amount,fee,reference FROM requests WHERE id=? AND status='pending'",(rid,)).fetchone()
    if not row: c.close(); return None
    c.execute("UPDATE requests SET status=?,updated_at=? WHERE id=?",(status,now(),rid)); c.commit(); c.close()
    return {"id":row[0],"telegram_id":row[1],"kind":row[2],"amount":row[3],"fee":row[4],"reference":row[5]}
