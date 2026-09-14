# System design

## Business context and boundaries

This document describes target responsibilities and workflows. Today the API has only public GET /health, Web has navigation placeholders, and Python has a health CLI. Source generation and QA are implemented under apps/api/database; audit-domain persistence and execution are planned.
A fictional organization processes invoices and payments. Employees may have permissions that exceed their responsibilities; transaction and activity data can reveal control weaknesses.

| Actor/component | Responsibility |
| --- | --- |
| Demo employee | Operates future business workflows |
| Business owner | Explains exceptions and owns remediation |
| Auditor | Selects tests, reviews evidence, drafts findings |
| Audit manager | Approves findings and closure |
| React web | Presents audit workflows; never connects directly to PostgreSQL |
| Hapi API | Authenticates, authorizes and manages audit records |
| Demo business module (planned) | Owns operational writes using its own connection |
| Python engine | Validates extracts and computes test outcomes |
| PostgreSQL business schema | Source records owned by operational system |
| PostgreSQL audit schema | Run metadata, results, evidence and findings |

The API will remain modular rather than splitting into microservices. Operational routes will live under a separate business module and credential. Python will initially run through an explicit CLI, not an HTTP service or arbitrary API-spawned shell.

## Key flows
Employee → Demo Business System → business schema.
Read-only source connection → consistent extract → validation → Python analysis → audit result writer → auditor.
Audit users and their credentials are independent of the business users being tested.

## Audit lifecycle
Understand System → Identify Risk → Identify Control → Define Audit Test → Execute Test → Detect Exceptions → Review Evidence → Create Finding → Generate Report.

Planned run states: queued → running → completed or failed; queued/running may become cancelled. A run captures test version, parameters, dataset identity, extraction time, timezone and population counts. Failed data validation produces an error/inconclusive result, never a pass. Completed runs are not overwritten; reruns receive new IDs. A future worker must own transitions and prevent duplicate execution.

## Finding lifecycle
Draft → in_review → open → remediated → closed. A reviewer may return in_review to draft. A manager may reopen a closed finding with a reason. The auditor documents condition, criteria, risk, impact, evidence and recommendation; the responsible party responds; the manager verifies closure. Exceptions are not automatically findings. All transitions must eventually produce audit events.

## Data quality
Validate required columns, keys, nulls, referential integrity, currency and timestamp semantics before detection. Preserve source identifiers and snapshots rather than linking audit conclusions to mutable live rows. See [open questions](OPEN-QUESTIONS.md) for unresolved policy.
