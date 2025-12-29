import sys
import json, hashlib
from pathlib import Path
from scripts.experiments.common import ensure_dirs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ensure_dirs()

    # Hash verification for one latest release directory found
    rels = sorted([p for p in (OUT / "oscal").glob("r*/")])
    if not rels:
        raise SystemExit("No OSCAL outputs found. Run exp_rq1 first.")
    rel_dir = rels[-1]
    ar = json.loads((rel_dir / "assessment-results.json").read_text(encoding="utf-8"))
    resources = ar["assessment-results"]["back-matter"]["resources"]

    ok=0; bad=0; details=[]
    for res in resources:
        for rl in res.get("rlinks", []):
            href = rl.get("href")
            expected = rl.get("hashes", [{}])[0].get("value")
            if not href or not expected:
                continue
            p = ROOT / href
            if not p.exists():
                bad += 1
                details.append({"href": href, "status":"missing"})
                continue
            got = sha256_file(p)
            if got == expected:
                ok += 1
                details.append({"href": href, "status":"ok"})
            else:
                bad += 1
                details.append({"href": href, "status":"hash_mismatch", "expected": expected, "got": got})

    (OUT / "metrics" / "rq2_hash_verification.json").write_text(json.dumps({"release":rel_dir.name,"ok":ok,"bad":bad,"details":details}, indent=2), encoding="utf-8")

    consistency = {"releases": []}
    for rd in (OUT / "oscal").glob("r*/"):
        consistency["releases"].append({
            "release": rd.name,
            "has_compdef": (rd / "component-definition.json").exists(),
            "has_ssp": (rd / "system-security-plan.json").exists(),
            "has_ar": (rd / "assessment-results.json").exists(),
            "has_poam": (rd / "poam.json").exists()
        })
    (OUT / "metrics" / "rq2_oscal_consistency.json").write_text(json.dumps(consistency, indent=2), encoding="utf-8")
    print("RQ2 complete.")
if __name__ == "__main__":
    main()
