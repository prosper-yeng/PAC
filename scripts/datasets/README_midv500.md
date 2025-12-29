# MIDV-500 workload (public dataset)

This package supports a **document-centric onboarding** workload driven by MIDV-500:
- Paper: arXiv:1807.05786
- Dataset distribution is maintained by the authors (download separately).

## 1) Download MIDV-500
Obtain MIDV-500 from the dataset's official distribution referenced in the paper.
Place the dataset under:

```
data/midv500/
```

## 2) Build the index (deterministic)
```
python scripts/datasets/midv500_ingest.py --root data/midv500 --out data/midv500_index.jsonl
```

## 3) Run the onboarding workload with MIDV-500
```
USE_MIDV500=1 make exp_rq1
```

The workload generator:
- uses `data/midv500_index.jsonl` if present (otherwise scans `data/midv500/` directly),
- emits deterministic per-document evidence fields:
  `doc_sha256`, `doc_bytes`, `doc_path`, `doc_source`.

If you do not have MIDV-500 locally, set `USE_MIDV500=0` (default) and the workload falls back to synthetic documents.
