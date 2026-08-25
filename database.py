import sqlite3
from datetime import datetime, timezone

DB_PATH="aurix.db"

def conn(): return sqlite3.connect(DB_PATH)
def now(): return datetime.now(timezone.utc).isoformat()

def init_db():
    c=conn(); x=c.cursor()
    x.execute("CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, balance REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL)")
    x.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL, kind TEXT NOT NULL, amount REAL NOT NULL, fee REAL NOT NULL DEFAULT 0, status TEXT NOT NULL, reference TEXT, created_at TEXT NOT NULL)")
    c.commit(); c.close()

def get_user(tid):
    c=conn(); r=c.execute("SELECT telegram_id,username,first_name,balance,created_at FROM users WHERE telegram_id=?",(tid,)).fetchone(); c.close(); return r

def create_user(tid,username,first_name):
    c=conn(); c.execute("INSERT OR IGNORE INTO users (telegram_id,username,first_name,created_at) VALUES (?,?,?,?)",(tid,username,first_name,now())); c.commit(); c.close()

def get_balance(tid):
    c=conn(); r=c.execute("SELECT balance FROM users WHERE telegram_id=?",(tid,)).fetchone(); c.close(); return r[0] if r else 0

def add_transaction(tid,kind,amount,fee=0,status="pending",reference=""):
    c=conn(); c.execute("INSERT INTO transactions (telegram_id,kind,amount,fee,status,reference,created_at) VALUES (?,?,?,?,?,?,?)",(tid,kind,amount,fee,status,reference,now())); c.commit(); c.close()

def get_admin_stats():
    c=conn()
    users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    dep,fees=c.execute("SELECT COALESCE(SUM(CASE WHEN kind='deposit' THEN amount ELSE 0 END),0),COALESCE(SUM(CASE WHEN kind='deposit' THEN fee ELSE 0 END),0) FROM transactions WHERE status='confirmed'").fetchone()
    pfees=c.execute("SELECT COALESCE(SUM(fee),0) FROM transactions WHERE kind='profit' AND status='confirmed'").fetchone()[0]
    wd=c.execute("SELECT COUNT(*) FROM transactions WHERE kind='withdrawal'").fetchone()[0]
    c.close()
    return {"users":users,"deposits":float(dep or 0),"deposit_fees":float(fees or 0),"profit_fees":float(pfees or 0),"withdrawals":wd}

def list_users(limit=20):
    c=conn(); rows=c.execute("SELECT telegram_id,username,balance FROM users ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall(); c.close()
    return [{"telegram_id":r[0],"username":r[1],"balance":float(r[2])} for r in rows]

def list_transactions(limit=30):
    c=conn(); rows=c.execute("SELECT id,telegram_id,kind,amount,fee,status FROM transactions ORDER BY id DESC LIMIT ?",(limit,)).fetchall(); c.close()
    return [{"id":r[0],"telegram_id":r[1],"kind":r[2],"amount":float(r[3]),"fee":float(r[4]),"status":r[5]} for r in rows]
