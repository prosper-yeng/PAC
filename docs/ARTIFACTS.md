# Artifact outputs and mapping to the paper

## Evidence
- `out/evidence/opa_decisions.jsonl` — OPA decision log stream
- `out/evidence/events.jsonl` — workload events (latency, allow/deny)
- `out/evidence/ci_reports/*.json` — Conftest + opa test outputs
- `out/evidence/deletions/*.json` — deletion job completion evidence (for retention)

## OSCAL exports (per release rX)
- `out/oscal/rX/component-definition.json`
- `out/oscal/rX/system-security-plan.json`
- `out/oscal/rX/assessment-results.json`
- `out/oscal/rX/poam.json` (only if findings exist)

## Metrics
- `out/metrics/rq1_coverage.csv` — evidence coverage by release
- `out/metrics/rq2_oscal_consistency.json` — OSCAL referential integrity
- `out/metrics/rq2_hash_verification.json` — evidence hash verification
- `out/metrics/rq3_latency.csv` — latency p50/p95/p99 baseline vs enforced
- `out/metrics/rq3_evidence_volume.csv` — bytes/request evidence growth

## Paper-ready artifacts
- `out/paper/tables/*.tex`
- `out/paper/figures/*.pdf`

- `out/evidence/monitoring/windows/*.json` — window summaries (staleness evidence)
- `out/metrics/rq1_category_coverage.csv` and `out/paper/tables/rq1_category_coverage.tex`
- `out/metrics/delta_summary.csv` and `out/paper/tables/delta_summary.tex`

- `out/paper/figures/rq1_staleness_timeline.pdf` — staleness timeline plot
- `out/paper/figures/rq1_category_coverage_stacked.pdf` — stacked category coverage plot

- `docs/WORKLOADS.md` — workload definitions and alignment
- `workloads/wallet/*.json` — OpenID4VP + VC DM v2.0-shaped templates
- `data/midv500_index.jsonl` — optional MIDV-500 deterministic index
