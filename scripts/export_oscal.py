import json, os, time, hashlib
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
EVID = OUT / "evidence"
TRACE = ROOT / "traceability" / "traceability.yaml"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_trace():
    return yaml.safe_load(TRACE.read_text(encoding="utf-8"))

def read_jsonl(path: Path):
    if not path.exists():
        return []
    out=[]
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out

def read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def export_release(release_id: str):
    rel_dir = OUT / "oscal" / release_id
    rel_dir.mkdir(parents=True, exist_ok=True)
    trace = load_trace()

    decision_log = EVID / "opa_decisions.jsonl"
    events_log = EVID / "events.jsonl"
    ci_dir = EVID / "ci_reports"
    mon_rollup = EVID / "monitoring" / "rollup.json"
    cd_dir = EVID / "cd_gates"

    resources = []
    def add_res(title: str, p: Path):
        if not p.exists():
            return
        resources.append({
            "uuid": hashlib.sha256(str(p).encode()).hexdigest()[:32],
            "title": title,
            "rlinks": [{
                "href": str(p.relative_to(ROOT)),
                "hashes": [{"algorithm":"sha-256","value": sha256_file(p)}]
            }]
        })

    add_res("OPA decision logs", decision_log)
    add_res("Workload events", events_log)
    add_res("Monitoring rollup", mon_rollup)

    if ci_dir.exists():
        for p in ci_dir.glob("*.json"):
            add_res(f"CI report {p.name}", p)
    if cd_dir.exists():
        for p in cd_dir.glob("*.json"):
            add_res(f"CD gate {p.name}", p)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    compdef = {
        "component-definition": {
            "uuid": hashlib.sha256(f"compdef:{release_id}".encode()).hexdigest()[:32],
            "metadata": {"title": f"EviID Component Definition ({release_id})", "last-modified": now},
            "components": [
                {"uuid": "identity-api", "type": "service", "title": "Identity API"},
                {"uuid": "opa-pdp", "type": "service", "title": "OPA PDP"},
                {"uuid": "collector", "type": "service", "title": "Evidence Collector"},
                {"uuid": "oscal-exporter", "type": "tool", "title": "OSCAL Exporter"}
            ],
            "back-matter": {"resources": resources}
        }
    }
    (rel_dir / "component-definition.json").write_text(json.dumps(compdef, indent=2), encoding="utf-8")

    ssp = {
        "system-security-plan": {
            "uuid": hashlib.sha256(f"ssp:{release_id}".encode()).hexdigest()[:32],
            "metadata": {"title": f"EviID SSP ({release_id})", "last-modified": now},
            "system-characteristics": {"system-name": "EviID Prototype", "description": "Research prototype for compliance-as-code evidence generation."},
            "import-profile": {"href": "profile://identity"},
            "back-matter": {"resources": resources}
        }
    }
    (rel_dir / "system-security-plan.json").write_text(json.dumps(ssp, indent=2), encoding="utf-8")

    decisions = read_jsonl(decision_log)
    del_dir = EVID / "deletions"
    has_del = del_dir.exists() and any(del_dir.glob("*.json"))

    roll = read_json(mon_rollup)
    missing_window_flag = False
    if roll and isinstance(roll.get("windows"), list):
        for w in roll["windows"]:
            if w.get("missing_core_controls"):
                missing_window_flag = True
                break

    cd_fail = False
    if cd_dir.exists():
        for p in cd_dir.glob(f"cd_gate_{release_id}_*.json"):
            j = read_json(p) or {}
            if j.get("ok") is False:
                cd_fail = True
                break

    ci_fail = False
    if ci_dir.exists():
        for p in ["opa_test.json","conftest.json"]:
            j = read_json(ci_dir / p) or {}
            if j and j.get("returncode", 0) != 0:
                ci_fail = True
                break

    findings=[]
    observations=[]
    required_controls = [c["cid"] for c in trace["controls"]]

    for cid in required_controls:
        ok = bool(decisions)
        if cid == "ID-RET-01":
            ok = ok and has_del
        if cid in ["ID-LOG-01","ID-PUR-01","ID-ACC-01"] and missing_window_flag:
            ok = False

        observations.append({
            "uuid": hashlib.sha256(f"obs:{release_id}:{cid}".encode()).hexdigest()[:32],
            "description": f"Evidence present={ok} for control {cid}",
            "subjects": [{"type":"control","title": cid}]
        })
        if not ok:
            findings.append({
                "uuid": hashlib.sha256(f"finding:{release_id}:{cid}".encode()).hexdigest()[:32],
                "title": f"Finding for {cid}",
                "description": "Evidence incomplete, missing, or stale (e.g., missing window summaries or required artifacts).",
                "target": {"type":"control","title": cid}
            })

    if ci_fail or cd_fail:
        findings.append({
            "uuid": hashlib.sha256(f"finding:{release_id}:CHANGE".encode()).hexdigest()[:32],
            "title": "Change-management gate failure",
            "description": f"CI/CD checks indicate non-compliant release conditions (ci_fail={ci_fail}, cd_fail={cd_fail}).",
            "target": {"type":"control","title": "CHANGE-MGMT"}
        })

    ar = {
        "assessment-results": {
            "uuid": hashlib.sha256(f"ar:{release_id}".encode()).hexdigest()[:32],
            "metadata": {"title": f"EviID Assessment Results ({release_id})", "last-modified": now},
            "results": [{
                "uuid": hashlib.sha256(f"result:{release_id}".encode()).hexdigest()[:32],
                "title": f"Release {release_id} assessment",
                "start": now,
                "observations": observations,
                "findings": findings
            }],
            "back-matter": {"resources": resources}
        }
    }
    (rel_dir / "assessment-results.json").write_text(json.dumps(ar, indent=2), encoding="utf-8")

    if findings:
        poam = {
            "plan-of-action-and-milestones": {
                "uuid": hashlib.sha256(f"poam:{release_id}".encode()).hexdigest()[:32],
                "metadata": {"title": f"EviID POA&M ({release_id})", "last-modified": now},
                "poam-items": [{
                    "uuid": f["uuid"], "title": f["title"], "description": f["description"],
                    "status": {"state": "open"}
                } for f in findings],
                "back-matter": {"resources": resources}
            }
        }
        (rel_dir / "poam.json").write_text(json.dumps(poam, indent=2), encoding="utf-8")

    return rel_dir

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=os.getenv("RELEASE_ID","r1"))
    args = ap.parse_args()
    d = export_release(args.release)
    print(f"Exported OSCAL for {args.release} -> {d}")
