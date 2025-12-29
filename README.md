# EviID Reproducibility Package (ESORICS paper experiments)
This package reproduces the experiments for:
**"Compliance-as-Code for AI-Driven Identity Systems: Clause-to-Control Traceability and Machine-Readable Evidence"**

It provides:
- Policy-as-code (OPA/Rego) controls for identity workflows
- CI compliance checks (Conftest + `opa test`)
- Runtime enforcement through a minimal identity API that queries OPA
- Evidence collection (OPA decision logs -> collector)
- OSCAL export (Component Definition + Assessment Results)
- Experiment runners and analysis scripts (coverage, staleness, overhead, evidence volume, time-to-dossier)

## Quick start
Prereqs: Docker + Docker Compose, Python 3.10+ (3.11 recommended), `make`.

```bash
unzip eviid-repro.zip
cd eviid-repro

make venv
source .venv/bin/activate

make build-bundle
make up

# Sanity check
curl -s http://localhost:8181/health
curl -s http://localhost:8081/health
curl -s http://localhost:8080/health

# Run experiments
make exp_rq1
make exp_rq2
make exp_rq3

# Generate figures + tables used in the paper
make analyze
make figures

# Outputs
ls -R out
```

See `docs/EXPERIMENTS.md` for detailed procedures.


## Extended features
- Windowed monitoring summaries + staleness metrics (RQ1)
- Control-category coverage + delta summary tables (make analyze)

## Additional paper figures (extended)
- `out/paper/figures/rq1_staleness_timeline.pdf`
- `out/paper/figures/rq1_category_coverage_stacked.pdf`


## Workloads
This package evaluates:
1) MIDV-500-driven onboarding (`USE_MIDV500=1`) and
2) OpenID4VP + W3C VC DM v2.0-aligned wallet presentation verification.
See `docs/WORKLOADS.md`.


## Windows notes
- Use `py -m scripts.experiments.exp_rq1` (module form) so imports work.
- CI uses Docker containers; ensure Docker Desktop is running.


### Windows note (OPA tests)
If you run OPA tests manually, use:
```
docker compose run --rm opa test /policies/rego /policies/tests -v
```
Do **not** prefix with an extra `opa` (i.e., avoid `opa opa test ...`).


### Manual OPA tests (Windows / PowerShell)
Run from the project root:

```
docker compose run --rm opa test /policies/rego /policies/tests -v
```

This works because `./policies` is mounted into the OPA container at `/policies`.


### Troubleshooting
If `opa test` reports a `rego_type_error` about comparing sets to `{}`, ensure the policy uses `count(set) == 0` rather than `== {}`.
