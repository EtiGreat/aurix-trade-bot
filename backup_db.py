#!/usr/bin/env python3
"""Create a consistent SQLite backup for AURIX TRADE demo data."""
import argparse, os, sqlite3, shutil
from datetime import datetime, timezone
from pathlib import Path


def backup(destination=None):
    db_path = os.getenv('AURIX_DB_PATH', 'aurix.db')
    if not os.path.exists(db_path):
        raise SystemExit(f'Database not found: {db_path}')
    if destination is None:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        destination = os.path.join('backups', f'aurix-{stamp}.db')
    dest = Path(destination); dest.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(db_path)
    try:
        dst = sqlite3.connect(str(dest))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    print(f'BACKUP_CREATED={dest}')
    return str(dest)

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('destination', nargs='?')
    backup(p.parse_args().destination)
