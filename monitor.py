#!/usr/bin/env python3
"""Lightweight operational monitor for Railway or local checks."""
import json, os, sys, time, urllib.request

url=os.getenv('AURIX_HEALTH_URL')
if not url:
    print('AURIX_HEALTH_URL is not set; monitor skipped.')
    raise SystemExit(0)
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        body=json.loads(r.read().decode())
        if r.status != 200 or body.get('status') != 'ok': raise RuntimeError(f'health={body}')
    print('HEALTHY', url, body)
except Exception as e:
    print(f'UNHEALTHY {url}: {e}', file=sys.stderr)
    raise SystemExit(1)
