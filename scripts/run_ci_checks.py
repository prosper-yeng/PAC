import os, json, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "evidence" / "ci_reports"
OUT.mkdir(parents=True, exist_ok=True)

def run(cmd, capture=True):
    return subprocess.run(cmd, cwd=ROOT, capture_output=capture, text=True)

def dc():
    return ["docker", "compose"]

def is_running(service: str) -> bool:
    p = run(dc() + ["ps", "--status", "running", "--services"])
    if p.returncode != 0:
        return False
    return service in set((p.stdout or "").split())

def opa_test():
    ts = time.time()
    # NOTE: the OPA image entrypoint is already 'opa', so use subcommand 'test' (not 'opa test').
    if is_running("opa"):
        p = run(dc() + ["exec", "-T", "opa", "opa", "test", "/policies/rego", "/policies/tests", "-v"])
    else:
        p = run(dc() + ["run", "--rm", "opa", "test", "/policies/rego", "/policies/tests", "-v"])

    rec = {"tool": "opa test", "returncode": p.returncode, "stdout": p.stdout or "", "stderr": p.stderr or "", "ts": ts}
    (OUT / "opa_test.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return p.returncode

def conftest():
    ts = time.time()
    # If a conftest service exists, run it there; otherwise mark as skipped.
    if is_running("conftest"):
        p = run(dc() + ["exec", "-T", "conftest", "conftest", "test", "/work/configs", "-p", "/work/policies"])
        rec = {"tool": "conftest", "returncode": p.returncode, "stdout": p.stdout or "", "stderr": p.stderr or "", "ts": ts}
        (OUT / "conftest.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return p.returncode

    rec = {"tool": "conftest", "returncode": 0, "stdout": "[{\"skipped\": true}]\n", "stderr": "", "ts": ts}
    (OUT / "conftest.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return 0

def main():
    rc1 = opa_test()
    rc2 = conftest()
    if rc1 != 0:
        raise SystemExit(rc1)
    if rc2 != 0:
        raise SystemExit(rc2)

if __name__ == "__main__":
    main()
