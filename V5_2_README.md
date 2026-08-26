# AURIX TRADE V5.2

## Automated Testing, Monitoring & Backup/Recovery

This release strengthens operational resilience for the **demo/paper-trading** environment.

### Quick checks

```bash
python -m unittest discover -p 'test_*.py'
python preflight.py
```

`preflight.py` requires Railway environment variables such as `BOT_TOKEN`, so it may fail locally when secrets are intentionally absent. Never put those secrets in GitHub.

### Backup

```bash
python backup_db.py
```

### Restore

Stop the application first, then:

```bash
python restore_db.py backups/manual.db
```

### Monitoring

Set `AURIX_HEALTH_URL` to the public `/health` endpoint and run:

```bash
python monitor.py
```

### Production note

The SQLite file is not a durable multi-instance production database. Before any live-money service, migrate persistent financial/account records to an appropriate managed database with automated backups, access controls and recovery testing.

**Live execution: OFF. Real money: OFF. Paper trading: ON.**
