import os, tempfile, sqlite3, unittest

class V52OpsTests(unittest.TestCase):
    def test_backup_restore_roundtrip(self):
        from backup_db import backup
        from restore_db import restore
        with tempfile.TemporaryDirectory() as d:
            db=os.path.join(d,'aurix.db'); os.environ['AURIX_DB_PATH']=db
            c=sqlite3.connect(db); c.execute('create table t (id integer primary key, value text)'); c.execute("insert into t(value) values ('ok')"); c.commit(); c.close()
            b=os.path.join(d,'backup.db'); backup(b)
            c=sqlite3.connect(db); c.execute("update t set value='changed'"); c.commit(); c.close()
            restore(b)
            c=sqlite3.connect(db); self.assertEqual(c.execute('select value from t').fetchone()[0],'ok'); c.close()
            del os.environ['AURIX_DB_PATH']

    def test_monitor_missing_url_is_safe_noop(self):
        old=os.environ.pop('AURIX_HEALTH_URL',None)
        try:
            import subprocess, sys
            p=subprocess.run([sys.executable,'monitor.py'],capture_output=True,text=True)
            self.assertEqual(p.returncode,0)
        finally:
            if old is not None: os.environ['AURIX_HEALTH_URL']=old

if __name__=='__main__': unittest.main()
