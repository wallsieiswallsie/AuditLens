# Open architectural questions

Fixture conventions remain in [ADR-005](adr/ADR-005-phase-1-dataset-conventions.md). Stabilization changes no anomaly semantics. Current acceptance is in [VERIFICATION](VERIFICATION.md); the pre-stabilization review remains historical.

| Question | Classification | Decision / next action |
| --- | --- | --- |
| Employment, invoice identity, approval and payment conventions | RESOLVED | Existing fixture v1 semantics and manifests unchanged |
| Runtime database acceptance | RESOLVED | Disposable PostgreSQL 17.5 migration/seed/rollback/reset/determinism/constraints passed |
| Source-reader boundary | RESOLVED | NOLOGIN permission role, explicit table SELECT, PUBLIC/default restrictions, real permission tests; ADR-008 |
| PORT/API_URL/database variables and Web host | RESOLVED | PORT canonical; API_URL public build input; DATABASE_URL server-only; optional local preview host |
| Repository production deployment contract | RESOLVED | Root workspace builds, separate API/Web start commands, static SPA fallback and watch recommendations documented |
| Actual Railway settings and reader provisioning | REQUIRED BEFORE REMOTE ACCESS | Dashboard/log/public URL checks and controlled database administration remain unverified; local evidence is not remote evidence |
| Initial source extraction contract | RESOLVED LOCALLY | Fixed Node pg bridge, explicit eleven-table/column SELECT, dedicated reader URL preferred, mandatory restricted SET ROLE; Python owns contracts/execution |
| Snapshot semantics | RESOLVED LOCALLY | One read-only repeatable-read transaction; versioned canonical JSONL, primary keys, UTC timestamps, exact decimal strings, counts and SHA-256; local creation time is not a source transaction cutoff |
| Local CLI operator provenance | RESOLVED LOCALLY | Explicit --operator or process AUDIT_OPERATOR; neutral local fallback; no personal machine discovery or authentication claim |
| Policy and procedure versions | RESOLVED FOUNDATION | Central framework/schema/policy/health versions and frozen configuration; business policy and Detector SDK are the next milestone |
| Ground-truth isolation | RESOLVED | Engine must not import generators, fixture QA or ground-truth.json; harness compares independently produced results afterward |
| Minimal evidence retention/redaction | RESOLVED LOCAL / REMOTE OPEN | Ignored local files, OS permissions and manual deletion; evidence contract minimizes copies; no automated retention, signatures or real-data redaction service |
| Result writer and runtime API identity | REQUIRED BEFORE DATABASE AUDIT ENDPOINTS | Local filesystem results need no DB writer; separate audit-only identity and split API migrations before database-backed audit endpoints |
| CORS policy | REQUIRED BEFORE REMOTE ACCESS | Exact Web-origin policy before cross-origin browser API data calls; currently absent, no wildcard |
| Platform identity, sessions and RBAC | REQUIRED BEFORE REMOTE ACCESS | Required for remote execution/evidence endpoints; local CLI framework can precede JWT |
| Real HR history, service accounts, currencies, thresholds and real privilege baseline | CAN WAIT | Revisit with expanded detector scope; v1 fixture rules are project conventions |
| Asynchronous queue/cancellation | CAN WAIT | Initial CLI remains synchronous; no persistent Python deployment |
| License attribution | CAN WAIT | MIT notice exists; owner attribution remains owner confirmation |

The local framework decisions are implemented in [ADR-009](adr/ADR-009-snapshot-based-audit-execution.md) and the [framework guide](AUDIT-FRAMEWORK.md). Next: Audit Policy + Detector SDK. Business detection, remote access and database result persistence remain separate work.
