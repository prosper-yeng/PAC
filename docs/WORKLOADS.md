# Workloads (publicly reproducible)

This package evaluates two workloads:

## (i) Document-centric onboarding pipeline (MIDV-500-driven)
- Input: videos from MIDV-500 (public dataset; see arXiv:1807.05786).
- Workload generator scans `data/midv500/` for video files and derives deterministic document evidence:
  - `doc_sha256`, `doc_bytes`, `doc_path` (relative), `doc_source="MIDV-500"`.
- The onboarding API receives these attributes and enforces controls via OPA:
  - purpose limitation, least privilege, retention limit, logging schema.

If you do not have MIDV-500 locally, the generator falls back to synthetic documents and still produces comparable traceability/evidence metrics.

## (ii) Wallet presentation verification (OpenID4VP + W3C VC DM v2.0-aligned)
- The wallet workload simulates verifier requests and wallet responses in the **shape** of:
  - OpenID for Verifiable Presentations (OpenID4VP) 1.0
  - W3C Verifiable Credentials Data Model v2.0 (VC DM v2.0)
- For reproducibility, the package uses deterministic JSON templates under `workloads/wallet/` and generates
  per-request variations (claims requested, risk tier, roles).

The prototype does not implement cryptographic verification; the focus is **Compliance-as-Code** enforcement,
clause-to-control traceability, and machine-readable evidence generation.
