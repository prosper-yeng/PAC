import argparse, json, hashlib
from pathlib import Path

VIDEO_EXTS = {".mp4",".avi",".mov",".mkv",".webm",".mpg",".mpeg",".m4v"}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/midv500", help="Path to MIDV-500 directory")
    ap.add_argument("--out", default="data/midv500_index.jsonl", help="Output JSONL index")
    args = ap.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not root.exists():
        out.write_text("", encoding="utf-8")
        print(f"[midv_ingest] {root} does not exist; wrote empty index at {out}")
        return

    vids = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    vids.sort()

    with out.open("w", encoding="utf-8") as f:
        for p in vids:
            rel = p.relative_to(root)
            rec = {
                "doc_source": "MIDV-500",
                "doc_path": str(rel),
                "doc_bytes": p.stat().st_size,
                "doc_sha256": sha256_file(p)
            }
            f.write(json.dumps(rec) + "\n")
    print(f"[midv_ingest] indexed {len(vids)} videos -> {out}")

if __name__ == "__main__":
    main()
