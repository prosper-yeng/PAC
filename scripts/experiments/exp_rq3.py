import os, sys, time, json, subprocess
from pathlib import Path

import pandas as pd

from scripts.experiments.common import ensure_dirs, write_meta

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"

def run(cmd, env=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    subprocess.check_call(cmd, cwd=ROOT, env=e)

def find_wallet_summary(n: int, conc: int) -> Path:
    candidates = [
        OUT / "metrics" / f"summary_wallet_N{n}_C{conc}_midv0.json",
        OUT / "metrics" / f"summary_wallet_N{n}_C{conc}_midv1.json",
        OUT / "metrics" / f"summary_wallet_N{n}_C{conc}.json",  # legacy
    ]
    existing = [p for p in candidates if p.exists()]
    if existing:
        # pick newest if multiple
        return sorted(existing, key=lambda p: p.stat().st_mtime, reverse=True)[0]

    avail = sorted((OUT / "metrics").glob("summary_wallet_*.json"))
    raise FileNotFoundError(
        f"Could not find wallet summary for N={n}, CONC={conc}. "
        f"Looked for: {candidates}. Available: {avail}"
    )

def main():
    ensure_dirs()

    seed = int(os.getenv("SEED", "1337"))
    n = int(os.getenv("N", "5000"))
    conc = int(os.getenv("CONC", "50"))
    policy_complexity = os.getenv("POLICY_COMPLEXITY", "med")

    write_meta({
        "rq": "rq3",
        "seed": seed,
        "N": n,
        "CONC": conc,
        "policy_complexity": policy_complexity,
        "ts": time.time()
    })

    # Ensure bundle exists and OPA reloads it
    run([sys.executable, "scripts/build_bundle.py", "--complexity", policy_complexity])
    run(["docker", "compose", "restart", "opa"])
    time.sleep(2)

    modes = [("baseline", "1"), ("enforced", "0")]
    rows = []

    for mode, bypass in modes:
        # Restart identity-api with appropriate bypass
        run(
            ["docker", "compose", "up", "-d", "--no-deps", "--build", "identity-api"],
            env={"BASELINE_BYPASS": bypass, "RELEASE_ID": "rq3"}
        )
        time.sleep(2)

        # Run wallet workload
        env = {"SEED": str(seed), "N": str(n), "CONC": str(conc), "WORKLOAD": "wallet"}
        run([sys.executable, "scripts/loadgen.py"], env=env)

        sp = find_wallet_summary(n, conc)
        summ = json.loads(sp.read_text(encoding="utf-8"))
        summ["mode"] = mode
        rows.append(summ)

    df = pd.DataFrame(rows)
    (OUT / "metrics").mkdir(parents=True, exist_ok=True)
    (OUT / "metrics" / "rq3_latency.csv").write_text(df.to_csv(index=False), encoding="utf-8")

    # Evidence volume (very simple proxy)
    evid = OUT / "evidence"

    def sz(p: Path) -> int:
        return int(p.stat().st_size) if p.exists() else 0

    vol_rows = [
        {"metric": "N", "value": n},
        {"metric": "CONC", "value": conc},
        {"metric": "opa_decisions_bytes", "value": sz(evid / "opa_decisions.jsonl")},
        {"metric": "events_bytes", "value": sz(evid / "events.jsonl")},
    ]
    vol_df = pd.DataFrame(vol_rows)
    (OUT / "metrics" / "rq3_evidence_volume.csv").write_text(vol_df.to_csv(index=False), encoding="utf-8")

    print("RQ3 complete.")

if __name__ == "__main__":
    main()
