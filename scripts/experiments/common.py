from pathlib import Path
import json, hashlib, time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"

def ensure_dirs():
    (OUT / "metrics").mkdir(parents=True, exist_ok=True)
    (OUT / "oscal").mkdir(parents=True, exist_ok=True)
    (OUT / "delta").mkdir(parents=True, exist_ok=True)
    (OUT / "paper" / "tables").mkdir(parents=True, exist_ok=True)
    (OUT / "paper" / "figures").mkdir(parents=True, exist_ok=True)
    (OUT / "metadata").mkdir(parents=True, exist_ok=True)
    (OUT / "evidence").mkdir(parents=True, exist_ok=True)

def write_meta(meta: dict):
    (OUT / "metadata" / "experiment_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()
