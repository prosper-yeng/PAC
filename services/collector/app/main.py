from fastapi import FastAPI, Request
from pathlib import Path
import time, hashlib

app = FastAPI(title="EviID Evidence Collector")

OUT = Path("/app/out")
EVID = OUT / "evidence"
EVID.mkdir(parents=True, exist_ok=True)
OPA_LOG = EVID / "opa_decisions.jsonl"
EVENTS = EVID / "events.jsonl"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

@app.get("/health")
def health():
    return {"ok": True, "ts": time.time()}

# OPA decision logs POST to the service base URL
@app.post("/")
@app.post("/v1/data")
async def opa_decision_log(req: Request):
    payload = await req.body()
    line = payload.decode("utf-8").strip()
    with OPA_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return {"received": True, "sha256": sha256_bytes(payload)}

@app.post("/event")
async def event(req: Request):
    payload = await req.body()
    line = payload.decode("utf-8").strip()
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return {"received": True, "sha256": sha256_bytes(payload)}
