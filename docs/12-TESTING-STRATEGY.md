# Testing strategy

## Current foundation verification
Use npm test for API health contract, safe errors, unknown routes and configuration validation; npm run build for frontend compilation; npm run docs:check for relative links and Mermaid parsing; npm run db:check for a real SQL connection and npm run db:migrate for schema creation. Run Python unittest and its CLI after an editable install. See [verification results](VERIFICATION.md) for what actually ran.

## Planned layers
| Layer | Purpose and meaningful cases |
| --- | --- |
| Unit | Parameter validation, permission expansion, decimal comparison and lifecycle transitions |
| API | Success/error contracts, pagination, malformed payloads and status codes |
| Database | FKs, constraints, rollback/reapply, snapshot consistency and source write denial |
| Authorization | Anonymous 401, wrong role 403, object scope, disabled identity and reviewer separation |
| Engine | Nulls, boundary dates, timezone offsets, missing baseline and deterministic output |
| Detection accuracy | Exact expected record/group sets, false positives and false negatives |
| Integration | Source fixture → extraction → results/evidence → reviewed finding |

## Synthetic truth manifest
Implemented fixture v1 has the 14 exact categories and exception units documented in [dataset specification](16-SYNTHETIC-DATASET.md). This replaces the tentative Phase 0 counts under [ADR-005](adr/ADR-005-phase-1-dataset-conventions.md). Fixture SOD-001/002 represent observed transaction conflicts, distinct from the existing entitlement procedure IDs.

The Node tests verify same-seed complete equality, changed-seed variability, invalid seed rejection, exact population counts and exception sets, all foreign keys and log target references, legitimate partial-payment negatives, duplicate group members and checked-in artifact parity. Mutation tests introduce an orphan, unexpected duplicate, wrong SoD ID, additional self-confirmation and accidental dormant account; fixture QA must reject each even with hash checking disabled. PostgreSQL DDL is compiled offline, which is not database execution. docs:check compares ERD/dictionary inventories with compiled migration definitions and parses Mermaid and relative links.

Ground truth is only for development, automated tests and benchmarks. Future detection MUST NOT read ground-truth.json, generator modules or fixture QA during analysis. The independent engine receives source data plus frozen policy; only the test harness compares its output with truth afterward. Fixture QA assertions are not a deployable detection engine and are never imported by the API or Python package.

Compare exact ID sets (or exact group memberships), not counts alone. True positives are expected cases found; false positives are unexpected cases flagged; false negatives are expected cases missed. Precision = TP / (TP + FP); recall = TP / (TP + FN). Report undefined denominators explicitly instead of claiming perfect accuracy on an empty population. Future deterministic rule-based tests target precision and recall of 1.0 for this known fixture. There is no ML implementation. Benchmark units and overlap must be frozen before comparison.

Database tests must connect using the actual future source-reader role and prove INSERT/UPDATE/DELETE/DDL fail while SELECT succeeds. Do not claim read-only enforcement from a mocked repository. Never run destructive tests against a non-disposable database.

