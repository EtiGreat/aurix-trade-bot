#!/usr/bin/env python3
"""Restore an AURIX SQLite backup. Use only with the application stopped."""
import argparse, os, sqlite3, shutil, tempfile
from pathlib import Path


def restore(source):
    source=Path(source)
    db_path = os.getenv('AURIX_DB_PATH', 'aurix.db')
    if not source.exists(): raise SystemExit(f'Backup not found: {source}')
    check=sqlite3.connect(str(source))
    try:
        ok=check.execute('PRAGMA integrity_check').fetchone()[0]
        if ok != 'ok': raise SystemExit(f'Backup failed integrity check: {ok}')
    finally: check.close()
    target=Path(db_path); target.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.aurix-restore-', dir=str(target.parent)); os.close(fd)
    try:
        shutil.copy2(source,tmp)
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    print(f'RESTORED={target}')

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('source'); args=p.parse_args(); restore(args.source)
