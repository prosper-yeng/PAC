import json, time, math, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
EVID = OUT / "evidence"
OPA_LOG = EVID / "opa_decisions.jsonl"
EVENTS = EVID / "events.jsonl"
DEL_DIR = EVID / "deletions"

WINDOW_SEC = int(os.getenv("WINDOW_SEC", "60"))
REQUIRED_LOG_FIELDS = {"control_id","policy_bundle_digest","release_id","environment_id","decision_id","timestamp"}

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

def extract_ts_event(e: dict):
    t = e.get("ts")
    if isinstance(t, (int,float)):
        return float(t)
    return time.time()

def controls_for_endpoint(endpoint: str):
    base = {"ID-LOG-01","ID-PUR-01","ID-ACC-01"}
    if endpoint == "wallet/verify":
        base.add("ID-MIN-01")
    if endpoint == "onboarding/process":
        base.add("ID-RET-01")
    return base

def main():
    windows_dir = EVID / "monitoring" / "windows"
    windows_dir.mkdir(parents=True, exist_ok=True)

    opa = read_jsonl(OPA_LOG)
    evs = read_jsonl(EVENTS)

    if not opa and not evs:
        (windows_dir / "window_empty.json").write_text(json.dumps({"window_sec": WINDOW_SEC, "note":"no evidence"}, indent=2), encoding="utf-8")
        return

    ts_list=[extract_ts_event(e) for e in evs] if evs else [time.time()]
    tmin, tmax = min(ts_list), max(ts_list)

    start = math.floor(tmin / WINDOW_SEC) * WINDOW_SEC
    end = math.ceil((tmax + 1) / WINDOW_SEC) * WINDOW_SEC
    if end == start:
        end = start + WINDOW_SEC

    windows={}
    for wstart in range(int(start), int(end), WINDOW_SEC):
        windows[wstart] = {
            "window_start": wstart,
            "window_end": wstart + WINDOW_SEC,
            "controls_seen": {cid: 0 for cid in ["ID-LOG-01","ID-PUR-01","ID-MIN-01","ID-RET-01","ID-ACC-01"]},
            "allow_count": 0,
            "deny_count": 0,
            "lat_ms_p50": None,
            "lat_ms_p95": None,
            "log_schema_ok": 0,
            "log_schema_bad": 0,
            "deletion_events": 0
        }

    lat_by_w = {k: [] for k in windows.keys()}

    for e in evs:
        t = extract_ts_event(e)
        wstart = int(math.floor(t / WINDOW_SEC) * WINDOW_SEC)
        if wstart not in windows:
            continue

        allow = e.get("allow")
        if allow is True:
            windows[wstart]["allow_count"] += 1
        elif allow is False:
            windows[wstart]["deny_count"] += 1

        et = e.get("type","")
        endpoint = "wallet/verify" if "wallet" in et else "onboarding/process" if "onboarding" in et else None
        if endpoint:
            for cid in controls_for_endpoint(endpoint):
                windows[wstart]["controls_seen"][cid] += 1

        dur = e.get("duration_ms")
        if isinstance(dur, (int,float)):
            lat_by_w[wstart].append(float(dur))

    # Best-effort logging schema checks from OPA logs (OPA log shape varies)
    for e in opa:
        t = time.time()
        wstart = int(math.floor(t / WINDOW_SEC) * WINDOW_SEC)
        if wstart not in windows:
            wstart = sorted(windows.keys())[-1]
        inp = e.get("input")
        if isinstance(inp, dict):
            req = inp.get("request", {})
            fields = set(req.get("log_fields", []) or [])
            if REQUIRED_LOG_FIELDS.issubset(fields):
                windows[wstart]["log_schema_ok"] += 1
            else:
                windows[wstart]["log_schema_bad"] += 1

    if DEL_DIR.exists():
        for p in DEL_DIR.glob("*.json"):
            m = p.stat().st_mtime
            wstart = int(math.floor(m / WINDOW_SEC) * WINDOW_SEC)
            if wstart in windows:
                windows[wstart]["deletion_events"] += 1

    try:
        import numpy as np
        for wstart, arr in lat_by_w.items():
            if arr:
                a = np.array(arr)
                windows[wstart]["lat_ms_p50"] = float(np.quantile(a, 0.5))
                windows[wstart]["lat_ms_p95"] = float(np.quantile(a, 0.95))
    except Exception:
        pass

    rollup = {"window_sec": WINDOW_SEC, "windows": []}
    for wstart in sorted(windows.keys()):
        w = windows[wstart]
        missing = [cid for cid, c in w["controls_seen"].items() if c == 0 and cid in ["ID-LOG-01","ID-PUR-01","ID-ACC-01"]]
        w["missing_core_controls"] = missing
        (windows_dir / f"window_{wstart}.json").write_text(json.dumps(w, indent=2), encoding="utf-8")
        rollup["windows"].append(w)

    (windows_dir.parent / "rollup.json").write_text(json.dumps(rollup, indent=2), encoding="utf-8")
    print(f"Wrote {len(windows)} window summaries to {windows_dir}")

if __name__ == "__main__":
    main()
