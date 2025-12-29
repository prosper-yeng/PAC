import json, time, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
EVID = OUT / "evidence"
CDDIR = EVID / "cd_gates"
CDDIR.mkdir(parents=True, exist_ok=True)

def read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def main():
    release = os.getenv("RELEASE_ID","r1")
    env = os.getenv("ENVIRONMENT_ID","dev")

    bundle_sha = (ROOT / "bundle" / "bundle.sha256").read_text(encoding="utf-8").strip() if (ROOT / "bundle" / "bundle.sha256").exists() else None
    ci_opa = read_json(EVID / "ci_reports" / "opa_test.json")
    ci_conf = read_json(EVID / "ci_reports" / "conftest.json")

    ok = True
    reasons = []
    if not bundle_sha:
        ok = False
        reasons.append("missing_bundle_sha256")
    if ci_opa and ci_opa.get("returncode", 0) != 0:
        ok = False
        reasons.append("opa_tests_failed")
    if ci_conf and ci_conf.get("returncode", 0) != 0:
        ok = False
        reasons.append("conftest_failed")

    gate = {
        "type": "cd_gate",
        "release_id": release,
        "environment_id": env,
        "ok": ok,
        "reasons": reasons,
        "bundle_sha256": bundle_sha,
        "ts": time.time()
    }
    p = CDDIR / f"cd_gate_{release}_{int(time.time())}.json"
    p.write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(f"CD gate {release}: ok={ok} reasons={reasons}")

if __name__ == "__main__":
    main()
