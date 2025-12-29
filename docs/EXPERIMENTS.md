# Experiments: step-by-step instructions

## Common setup
```bash
make venv
source .venv/bin/activate
make build-bundle
make up
```

Sanity checks:
```bash
curl -s http://localhost:8181/health
curl -s http://localhost:8081/health
curl -s http://localhost:8080/health
```

All outputs go under `out/`.

---

## Experiment RQ1: Traceability and coverage under change
```bash
make exp_rq1
```

Produces:
- `out/metrics/rq1_coverage.csv`
- `out/oscal/r1..r4/*`
- `out/paper/tables/rq1_coverage.tex`
- `out/paper/figures/rq1_coverage.pdf`

---

## Experiment RQ2: OSCAL portability and hash integrity
```bash
make exp_rq2
```

Produces:
- `out/metrics/rq2_oscal_consistency.json`
- `out/metrics/rq2_hash_verification.json`

---

## Experiment RQ3: Overhead and scaling
Default:
```bash
make exp_rq3
```

Override parameters:
```bash
N=20000 CONC=200 POLICY_COMPLEXITY=high make exp_rq3
```

Produces:
- `out/metrics/rq3_latency.csv`
- `out/paper/tables/rq3_latency.tex`
- `out/paper/figures/rq3_latency.pdf`
- `out/metrics/rq3_evidence_volume.csv`

---

## Paper-ready outputs
```bash
make analyze
make figures
```


### Extended outputs
- `out/metrics/rq1_staleness.csv` (staleness)
- `out/paper/tables/rq1_category_coverage.tex` (category coverage)
- `out/paper/tables/delta_summary.tex` (bundle/findings/POA&M deltas)


### Figures (extended)
After `make figures`, you also get:
- `out/paper/figures/rq1_staleness_timeline.pdf`
- `out/paper/figures/rq1_category_coverage_stacked.pdf`


## Workload notes
- Onboarding workload can be driven by MIDV-500 (`USE_MIDV500=1`).
- Wallet workload is aligned with OpenID4VP request/response shapes and W3C VC DM v2.0.
See `docs/WORKLOADS.md`.
