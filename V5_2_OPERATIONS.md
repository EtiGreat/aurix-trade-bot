# AURIX TRADE V5.2 — Testing, Monitoring & Backup/Recovery

V5.2 improves operational resilience while keeping **live execution and real-money handling OFF**.

## Automated tests
Run from the repository root:

```bash
python -m unittest discover -p 'test_*.py'
```

If `pytest` is installed, this also works:

```bash
pytest -q
```

## Health monitoring
Railway exposes `/health` through the existing web server. Set `AURIX_HEALTH_URL` locally or in a monitoring job to the public HTTPS health URL, for example:

`https://YOUR-RAILWAY-DOMAIN/health`

Then run:

```bash
python monitor.py
```

A successful check prints `HEALTHY` and exits 0; failures exit 1.

## Backups
Create a consistent SQLite backup:

```bash
python backup_db.py
```

or specify a destination:

```bash
python backup_db.py backups/manual.db
```

Backups should be stored outside the Git repository and protected as operational data. Do **not** commit `aurix.db` or backups to GitHub.

## Recovery
Stop the application before restoring:

```bash
python restore_db.py backups/manual.db
```

The restore validates SQLite integrity before atomically replacing the database file.

## Railway note
Railway deployments are not a substitute for database backups. For production-like operation, use an external persistent database/storage strategy rather than relying on the container filesystem for durable records.

## Recovery drill
At least once before any future live-money consideration:

1. Create a backup.
2. Verify the backup with `restore_db.py` in an isolated test directory.
3. Run the automated tests.
4. Verify `/health`.
5. Record the recovery result in the operational log.

## Safety boundary
- Paper/demo trading: ON
- Live execution: OFF
- Real-money deposits: OFF
- Real-money withdrawals: OFF
- Customer fund custody: OFF
