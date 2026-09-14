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
| Initial source extraction contract | REQUIRED BEFORE AUDIT FRAMEWORK | Prefer direct PostgreSQL reader for the initial local CLI to preserve the tested identity boundary; API-mediated extraction requires new endpoints/auth; exported snapshots improve portability. Final selection must freeze types, tables and versioned inputs before code |
| Snapshot semantics | REQUIRED BEFORE AUDIT FRAMEWORK | Prefer one repeatable-read source transaction with extraction timestamp, source IDs, counts and canonical hashes; decide whether to retain a versioned export package. Fixture QA is evidence for types/hashes, not an implemented extractor |
| Local CLI operator provenance | REQUIRED BEFORE AUDIT FRAMEWORK | Record explicit local operator label, origin, execution timestamp and tool version. This is self-asserted local provenance, not authentication; never reuse business.users as audit operators |
| Policy and procedure versions | REQUIRED BEFORE AUDIT FRAMEWORK | Freeze policy/rule versions, dataset identity and run parameters in every result contract |
| Ground-truth isolation | RESOLVED | Engine must not import generators, fixture QA or ground-truth.json; harness compares independently produced results afterward |
| Minimal evidence retention/redaction | REQUIRED BEFORE AUDIT FRAMEWORK | Decide retention period, redaction, location and integrity metadata before durable evidence. External anchoring can follow later |
| Result writer and runtime API identity | REQUIRED BEFORE AUDIT FRAMEWORK | Define separate audit-only writer before result persistence; split API migration execution/credentials before database-backed audit endpoints. No new identity or table implemented yet |
| CORS policy | REQUIRED BEFORE REMOTE ACCESS | Exact Web-origin policy before cross-origin browser API data calls; currently absent, no wildcard |
| Platform identity, sessions and RBAC | REQUIRED BEFORE REMOTE ACCESS | Required for remote execution/evidence endpoints; local CLI framework can precede JWT |
| Real HR history, service accounts, currencies, thresholds and real privilege baseline | CAN WAIT | Revisit with expanded detector scope; v1 fixture rules are project conventions |
| Asynchronous queue/cancellation | CAN WAIT | Initial CLI remains synchronous; no persistent Python deployment |
| License attribution | CAN WAIT | MIT notice exists; owner attribution remains owner confirmation |

The local framework may start as the next milestone after resolving the design choices above. This stabilization does not select a result schema, implement extraction, or begin audit detection.
