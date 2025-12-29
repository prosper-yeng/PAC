import json, os, argparse, uuid, time, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPL = ROOT / "workloads" / "wallet"

def load(name: str):
    return json.loads((TEMPL / name).read_text(encoding="utf-8"))

def extract_requested_claims(presentation_definition: dict) -> list[str]:
    claims=set()
    for d in presentation_definition.get("input_descriptors", []):
        for f in (d.get("constraints", {}) or {}).get("fields", []):
            for path in f.get("path", []):
                if "credentialSubject" in path:
                    claims.add(path.split(".")[-1].replace("]","").replace("[","").replace("\"",""))
    return sorted(claims)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=int(os.getenv("N","1000")))
    ap.add_argument("--seed", type=int, default=int(os.getenv("SEED","1337")))
    ap.add_argument("--out", default=os.getenv("OUT","out/workloads/wallet.jsonl"))
    args = ap.parse_args()

    random.seed(args.seed)
    auth = load("authorization_request.json")
    pd = auth["presentation_definition"]
    base_claims = extract_requested_claims(pd)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    roles = ["verifier_service", "compliance_service"]
    risk = ["low","med","high"]

    with out.open("w", encoding="utf-8") as f:
        for i in range(args.n):
            rid = str(uuid.uuid4())
            claims = base_claims[:]
            if i % 10 == 0:
                claims = claims + ["national_id"]
            req = {
                "protocol": "openid4vp",
                "vc_dm_version": "2.0",
                "purpose": "wallet_presentation",
                "requester_role": roles[i % len(roles)],
                "risk_tier": risk[i % len(risk)],
                "requested_claims": claims,
                "authorization_request": auth,
                "decision_id": rid,
                "ts": time.time()
            }
            f.write(json.dumps(req) + "\n")
    print(f"[wallet_gen] wrote {args.n} wallet requests -> {out}")

if __name__ == "__main__":
    main()
