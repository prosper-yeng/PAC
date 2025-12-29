import asyncio, time, os, json
import httpx
from pathlib import Path
import numpy as np
import pandas as pd

API = os.getenv("API_URL","http://localhost:8080")
N = int(os.getenv("N","5000"))
CONC = int(os.getenv("CONC","50"))
SEED = int(os.getenv("SEED","1337"))
WORKLOAD = os.getenv("WORKLOAD","wallet")  # wallet or onboarding
USE_MIDV500 = os.getenv("USE_MIDV500","0") == "1"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "metrics"
OUT.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(SEED)

MIDV_INDEX = ROOT / "data" / "midv500_index.jsonl"
MIDV_ROOT = ROOT / "data" / "midv500"

def read_jsonl(path: Path):
    if not path.exists():
        return []
    out=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out

def wallet_template():
    templ_dir = ROOT / "workloads" / "wallet"
    auth = json.loads((templ_dir / "authorization_request.json").read_text(encoding="utf-8"))
    pd = auth.get("presentation_definition", {})
    claims=set()
    for d in pd.get("input_descriptors", []):
        for f in (d.get("constraints", {}) or {}).get("fields", []):
            for path in f.get("path", []):
                if "credentialSubject" in path:
                    claims.add(path.split(".")[-1].replace("]","").replace("[","").replace("\"",""))
    base_claims = sorted(claims) or ["ageOver18"]
    return auth, base_claims

AUTH_REQ, BASE_CLAIMS = wallet_template()

def make_wallet_payload():
    role = "verifier_service"
    risk_tier = ["low","med","high"][int(rng.integers(0,3))]
    claims = BASE_CLAIMS[:]
    if int(rng.integers(0,10)) == 0:
        claims = claims + ["national_id"]

    return {
        "protocol": "openid4vp",
        "vc_dm_version": "2.0",
        "requester_role": role,
        "purpose": "wallet_presentation",
        "retention_days": int(rng.integers(1,4)),
        "risk_tier": risk_tier,
        "requested_claims": claims,
        "authorization_request": AUTH_REQ
    }, "/wallet/verify"

def make_onboarding_payload(doc=None):
    if doc is None:
        doc = {
            "doc_source": "synthetic",
            "doc_path": f"synthetic_{int(rng.integers(0,10**9))}.mp4",
            "doc_bytes": int(rng.integers(10_000, 5_000_000)),
            "doc_sha256": f"synthetic-{int(rng.integers(0,10**9))}"
        }
    return {
        "requester_role": "onboarding_service",
        "purpose": "onboarding",
        "retention_days": int(rng.integers(15,45)),
        "risk_tier": ["low","med","high"][int(rng.integers(0,3))],
        "requested_claims": ["given_name","family_name","birthdate"],
        "doc_source": doc["doc_source"],
        "doc_path": doc["doc_path"],
        "doc_bytes": doc["doc_bytes"],
        "doc_sha256": doc["doc_sha256"],
    }, "/onboarding/process"

def build_queue_items():
    if WORKLOAD == "wallet":
        return [make_wallet_payload() for _ in range(N)]
    else:
        if USE_MIDV500:
            docs = read_jsonl(MIDV_INDEX)
            if not docs and MIDV_ROOT.exists():
                docs = [{"doc_source":"MIDV-500","doc_path":str(p.relative_to(MIDV_ROOT)), "doc_bytes":p.stat().st_size, "doc_sha256":"(run midv500_ingest for sha256)"} 
                        for p in sorted(MIDV_ROOT.rglob("*")) if p.is_file()]
            if docs:
                return [make_onboarding_payload(docs[i % len(docs)]) for i in range(N)]
        return [make_onboarding_payload(None) for _ in range(N)]

async def worker(client: httpx.AsyncClient, q: asyncio.Queue, results: list):
    while True:
        item = await q.get()
        if item is None:
            q.task_done()
            return
        payload, path = item
        t0 = time.perf_counter()
        try:
            resp = await client.post(API + path, json=payload, timeout=15.0)
            status = resp.status_code
            data = resp.json()
            allow = data.get("allow", None)
        except Exception:
            status = 0
            allow = None
        t1 = time.perf_counter()
        results.append(((t1-t0)*1000.0, status, allow))
        q.task_done()

async def main():
    q = asyncio.Queue()
    results = []
    items = build_queue_items()
    async with httpx.AsyncClient() as client:
        workers = [asyncio.create_task(worker(client, q, results)) for _ in range(CONC)]
        for it in items:
            q.put_nowait(it)
        for _ in range(CONC):
            q.put_nowait(None)
        await q.join()
        for w in workers:
            await w

    df = pd.DataFrame(results, columns=["lat_ms","status","allow"])
    out_path = OUT / f"load_{WORKLOAD}_N{N}_C{CONC}_midv{int(USE_MIDV500)}.csv"
    df.to_csv(out_path, index=False)
    summ = {
        "workload": WORKLOAD,
        "use_midv500": USE_MIDV500,
        "N": N, "CONC": CONC,
        "p50_ms": float(df["lat_ms"].quantile(0.5)),
        "p95_ms": float(df["lat_ms"].quantile(0.95)),
        "p99_ms": float(df["lat_ms"].quantile(0.99)),
        "mean_ms": float(df["lat_ms"].mean()),
        "ok_rate": float((df["status"]==200).mean())
    }
    (OUT / f"summary_{WORKLOAD}_N{N}_C{CONC}_midv{int(USE_MIDV500)}.json").write_text(json.dumps(summ, indent=2), encoding="utf-8")
    print(json.dumps(summ, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
