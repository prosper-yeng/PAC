from fastapi import FastAPI
from pydantic import BaseModel, Field
import os, time, uuid, requests

OPA_URL = os.getenv("OPA_URL", "http://localhost:8181")
COLLECTOR_URL = os.getenv("COLLECTOR_URL", "http://localhost:8081")
RELEASE_ID = os.getenv("RELEASE_ID", "r1")
ENVIRONMENT_ID = os.getenv("ENVIRONMENT_ID", "dev")
BASELINE_BYPASS = os.getenv("BASELINE_BYPASS", "0") == "1"

REQUIRED_LOG_FIELDS = ["control_id","policy_bundle_digest","release_id","environment_id","decision_id","timestamp"]

app = FastAPI(title="EviID Identity API")

class OnboardingReq(BaseModel):
    requester_role: str = "onboarding_service"
    purpose: str = "onboarding"
    retention_days: int = 30
    risk_tier: str = "med"
    requested_claims: list[str] = Field(default_factory=lambda: ["given_name","family_name","birthdate"])
    doc_source: str | None = None
    doc_path: str | None = None
    doc_bytes: int | None = None
    doc_sha256: str | None = None

class WalletReq(BaseModel):
    requester_role: str = "verifier_service"
    purpose: str = "wallet_presentation"
    retention_days: int = 1
    risk_tier: str = "low"
    requested_claims: list[str] = Field(default_factory=lambda: ["ageOver18"])
    protocol: str = "openid4vp"
    vc_dm_version: str = "2.0"
    authorization_request: dict | None = None

@app.get("/health")
def health():
    return {"ok": True, "release": RELEASE_ID, "env": ENVIRONMENT_ID, "baseline_bypass": BASELINE_BYPASS}

def opa_allow(input_obj: dict) -> bool:
    url = f"{OPA_URL}/v1/data/compliance/authz/allow"
    r = requests.post(url, json={"input": input_obj}, timeout=10)
    r.raise_for_status()
    return bool(r.json().get("result", False))

def emit_event(event: dict):
    try:
        requests.post(f"{COLLECTOR_URL}/event", json=event, timeout=3)
    except Exception:
        pass

def envelope(endpoint: str, req: dict) -> dict:
    return {
        "request": {
            "endpoint": endpoint,
            "purpose": req.get("purpose"),
            "requester_role": req.get("requester_role"),
            "retention_days": req.get("retention_days"),
            "requested_claims": req.get("requested_claims", []),
            "risk_tier": req.get("risk_tier","med"),
            "log_fields": REQUIRED_LOG_FIELDS,
            "release_id": RELEASE_ID,
            "environment_id": ENVIRONMENT_ID,
            "protocol": req.get("protocol"),
            "vc_dm_version": req.get("vc_dm_version"),
            "doc_source": req.get("doc_source"),
            "doc_path": req.get("doc_path"),
            "doc_bytes": req.get("doc_bytes"),
            "doc_sha256": req.get("doc_sha256"),
        }
    }

@app.post("/onboarding/process")
def onboarding(r: OnboardingReq):
    start = time.perf_counter()
    decision_id = str(uuid.uuid4())
    inp = envelope("onboarding/process", r.model_dump())
    allow = True if BASELINE_BYPASS else opa_allow(inp)
    dur_ms = (time.perf_counter() - start) * 1000.0
    emit_event({"type":"onboarding_decision","decision_id":decision_id,"allow":allow,"duration_ms":dur_ms,
                "release_id":RELEASE_ID,"environment_id":ENVIRONMENT_ID,"ts":time.time(),
                "doc_source": r.doc_source})
    return {"decision_id": decision_id, "allow": allow, "duration_ms": dur_ms}

@app.post("/wallet/verify")
def wallet(r: WalletReq):
    start = time.perf_counter()
    decision_id = str(uuid.uuid4())
    inp = envelope("wallet/verify", r.model_dump())
    allow = True if BASELINE_BYPASS else opa_allow(inp)
    dur_ms = (time.perf_counter() - start) * 1000.0
    emit_event({"type":"wallet_decision","decision_id":decision_id,"allow":allow,"duration_ms":dur_ms,
                "release_id":RELEASE_ID,"environment_id":ENVIRONMENT_ID,"ts":time.time(),
                "protocol": r.protocol, "vc_dm_version": r.vc_dm_version})
    return {"decision_id": decision_id, "allow": allow, "duration_ms": dur_ms}
