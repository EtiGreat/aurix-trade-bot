from security import validate_runtime

report = validate_runtime()
if not report.ok:
    print("AURIX V5.1 PREFLIGHT: FAILED")
    for issue in report.issues:
        print(f"- {issue}")
    raise SystemExit(1)

print("AURIX V5.1 PREFLIGHT: PASSED")
print("Trading mode: DEMO/PAPER only")
print("Live execution: disabled")
print("Real money: disabled")
