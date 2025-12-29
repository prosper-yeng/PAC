import os, sys, time, json, subprocess
from pathlib import Path

from scripts.experiments.common import ensure_dirs, write_meta

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"

def run(cmd, env=None):
    e=os.environ.copy()
    if env: e.update(env)
    subprocess.check_call(cmd, cwd=ROOT, env=e)

def trigger_deletion_evidence(release_id):
    ddir = OUT / "evidence" / "deletions"
    ddir.mkdir(parents=True, exist_ok=True)
    p = ddir / f"deletion_{release_id}_{int(time.time())}.json"
    p.write_text(json.dumps({"type":"deletion_job","release_id":release_id,"ts":time.time(),"ok":True}), encoding="utf-8")

def export_oscal(release_id):
    run([sys.executable,"scripts/export_oscal.py","--release",release_id])

def load_workloads(seed, n=2000, conc=50):
    env = {"SEED": str(seed), "N": str(n), "CONC": str(conc)}
    run([sys.executable,"scripts/loadgen.py"], env={**env, "WORKLOAD":"onboarding"})
    run([sys.executable,"scripts/loadgen.py"], env={**env, "WORKLOAD":"wallet"})

def summarize_windows():
    run([sys.executable,"scripts/monitoring/window_summarizer.py"], env={"WINDOW_SEC":"60"})

def main():
    ensure_dirs()
    seed = int(os.getenv("SEED","1337"))
    use_midv = os.getenv("USE_MIDV500","0") == "1"
    write_meta({"rq":"rq1","seed":seed,"use_midv500":use_midv,"ts":time.time(), "window_sec":60})

    run([sys.executable,"scripts/run_ci_checks.py"])

    releases = ["r1","r2","r3","r4"]
    for i, rel in enumerate(releases):
        if rel == "r2":
            run([sys.executable,"scripts/build_bundle.py","--complexity", os.getenv("POLICY_COMPLEXITY","med")])
            run(["docker","compose","restart","opa"])
            time.sleep(2)

        run(["docker","compose","up","-d","--no-deps","--build","identity-api"], env={"RELEASE_ID": rel})
        time.sleep(2)

        load_workloads(seed + i*10, n=2000, conc=50)

        if rel in ["r1","r2"]:
            trigger_deletion_evidence(rel)

        summarize_windows()
        run([sys.executable,"scripts/cd_gate.py"], env={"RELEASE_ID": rel, "ENVIRONMENT_ID": os.getenv("ENVIRONMENT_ID","dev")})
        export_oscal(rel)

        (OUT / "delta" / f"{rel}_delta.json").write_text(json.dumps({"release":rel,"ts":time.time()}, indent=2), encoding="utf-8")

        if rel == "r4":
            wdir = OUT / "evidence" / "monitoring" / "windows"
            ws = sorted(wdir.glob("window_*.json")) if wdir.exists() else []
            if ws:
                ws[0].unlink()

    print("RQ1 complete.")
if __name__ == "__main__":
    main()
