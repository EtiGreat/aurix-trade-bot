# AURIX TRADE V5.1 — Security Hardening

V5.1 adds a security/preflight layer before any future production integration.

## Guardrails
- Trading mode is limited to `DEMO` or `PAPER`.
- Live execution remains disabled.
- Real-money handling remains disabled.
- Missing `BOT_TOKEN` is treated as a startup/preflight failure.
- Secrets belong in Railway Variables, never in GitHub.
- `__pycache__/`, `.env`, and Python bytecode are ignored by Git.

## Preflight
Run:

```bash
python preflight.py
```

A successful result confirms the required environment guardrails are present.

## Important
This is a hardening layer, not a regulatory approval or a guarantee of security. Before handling customer funds, perform a professional security review, KYC/AML design, legal/regulatory assessment, penetration testing, and production incident-response planning.
