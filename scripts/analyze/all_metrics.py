import json, hashlib
from pathlib import Path
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
TRACE = ROOT / "traceability" / "traceability.yaml"

def read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    (OUT / "paper" / "tables").mkdir(parents=True, exist_ok=True)
    (OUT / "metrics").mkdir(parents=True, exist_ok=True)

    trace = yaml.safe_load(TRACE.read_text(encoding="utf-8"))
    controls = trace["controls"]
    cid_to_cat = {c["cid"]: c.get("category","(unknown)") for c in controls}

    rel_dirs = sorted((OUT / "oscal").glob("r*/"))

    rows=[]
    for rel_dir in rel_dirs:
        ar = read_json(rel_dir / "assessment-results.json")
        if not ar:
            continue
        findings = ar["assessment-results"]["results"][0].get("findings", [])
        missing = {f.get("target", {}).get("title") for f in findings if isinstance(f, dict)}
        for c in controls:
            cid = c["cid"]
            ok = cid not in missing
            rows.append({"release": rel_dir.name, "control": cid, "category": cid_to_cat[cid], "ok": ok})

    df = pd.DataFrame(rows)
    if not df.empty:
        cov = df.groupby("release").agg(controls_total=("control","count"), controls_ok=("ok","sum")).reset_index()
        cov["coverage_pct"] = (cov["controls_ok"]/cov["controls_total"]*100.0).round(2)
        cov.to_csv(OUT / "metrics" / "rq1_coverage.csv", index=False)
        (OUT / "paper" / "tables" / "rq1_coverage.tex").write_text(cov.to_latex(index=False, float_format="%.2f"), encoding="utf-8")

        cat = df.groupby(["release","category"]).agg(controls_total=("control","count"), controls_ok=("ok","sum")).reset_index()
        cat["coverage_pct"] = (cat["controls_ok"]/cat["controls_total"]*100.0).round(2)
        cat.to_csv(OUT / "metrics" / "rq1_category_coverage.csv", index=False)

        pivot = cat.pivot(index="release", columns="category", values="coverage_pct").fillna(0.0).round(2)
        (OUT / "paper" / "tables" / "rq1_category_coverage.tex").write_text(pivot.to_latex(float_format="%.2f"), encoding="utf-8")

    roll = read_json(OUT / "evidence" / "monitoring" / "rollup.json")
    if roll and isinstance(roll.get("windows"), list):
        st = []
        for w in roll["windows"]:
            st.append({
                "window_start": w.get("window_start"),
                "window_end": w.get("window_end"),
                "missing_core_controls": len(w.get("missing_core_controls", [])),
                "allow_count": w.get("allow_count", 0),
                "deny_count": w.get("deny_count", 0)
            })
        pd.DataFrame(st).to_csv(OUT / "metrics" / "rq1_staleness.csv", index=False)

    deltas=[]
    prev_bundle=None
    prev_findings=None
    for rel_dir in rel_dirs:
        ar = read_json(rel_dir / "assessment-results.json") or {}
        findings = (ar.get("assessment-results", {}).get("results", [{}])[0].get("findings", [])) or []
        poam = read_json(rel_dir / "poam.json")
        poam_count = len((poam or {}).get("plan-of-action-and-milestones", {}).get("poam-items", []) or [])
        btar = ROOT / "bundle" / "bundle.tar.gz"
        bundle_digest = sha256_file(btar) if btar.exists() else None
        deltas.append({
            "release": rel_dir.name,
            "bundle_digest": bundle_digest,
            "findings_count": len(findings),
            "poam_count": poam_count,
            "bundle_changed": (prev_bundle is not None and bundle_digest != prev_bundle),
            "findings_changed": (prev_findings is not None and len(findings) != prev_findings)
        })
        prev_bundle=bundle_digest
        prev_findings=len(findings)

    if deltas:
        dd = pd.DataFrame(deltas)
        dd.to_csv(OUT / "metrics" / "delta_summary.csv", index=False)
        (OUT / "paper" / "tables" / "delta_summary.tex").write_text(dd.to_latex(index=False), encoding="utf-8")

    print("Enhanced analysis complete -> out/metrics and out/paper/tables")

if __name__ == "__main__":
    main()
