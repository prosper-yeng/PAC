import argparse, tarfile, json, time, shutil, hashlib
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

HIGH_ADDON = r'''
# High complexity add-on: deny high risk unless compliance_service
high_risk_deny {
  input.request.risk_tier == "high"
  input.request.requester_role != "compliance_service"
}

allow {
  # preserve existing allow rules AND add this guard
  not high_risk_deny
}
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--complexity", choices=["low","med","high"], default="med")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    bundle_dir = root / "bundle"
    bundle_dir.mkdir(exist_ok=True)

    authz_src = (root / "policies/rego/authz.rego").read_text(encoding="utf-8")

    if args.complexity == "low":
        min_set = '{"given_name","family_name","birthdate"}'
        addon = ""
    elif args.complexity == "med":
        min_set = '{"given_name","family_name","birthdate","age_over_18"}'
        addon = ""
    else:
        min_set = '{"given_name","family_name","birthdate","age_over_18"}'
        addon = HIGH_ADDON

    authz_src = authz_src.replace(
        'min_allowed_claims = {"given_name","family_name","birthdate","age_over_18"}',
        f"min_allowed_claims = {min_set}  # complexity={args.complexity}"
    ) + "\n" + addon + "\n"

    tmp = root / ".tmp_bundle"
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "policies").mkdir(parents=True)

    (tmp / "policies" / "authz.rego").write_text(authz_src, encoding="utf-8")
    (tmp / "policies" / "data.rego").write_text((root / "policies/rego/data.rego").read_text(encoding="utf-8"), encoding="utf-8")

    manifest = {"revision": f"{int(time.time())}", "roots": ["compliance"]}
    (tmp / ".manifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    out_tar = bundle_dir / "bundle.tar.gz"
    with tarfile.open(out_tar, "w:gz") as tar:
        tar.add(tmp / ".manifest", arcname=".manifest")
        tar.add(tmp / "policies", arcname="policies")

    digest = sha256_file(out_tar)
    (bundle_dir / "bundle.sha256").write_text(digest + "  bundle.tar.gz\n", encoding="utf-8")
    print(f"Built bundle: {out_tar} sha256={digest}")

if __name__ == "__main__":
    main()
