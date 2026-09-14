# Development roadmap

Phase 0 is VERIFIED locally. Phase 1 is VERIFIED on disposable PostgreSQL 17.5. Stabilization and the Local CLI Audit Framework are COMPLETE for repository/local acceptance. Phase 3's local snapshot/run/result foundation is implemented; its remote/database extension remains future work. Phase 2 remains NOT STARTED. Audit Rule Pack v1 has five implemented business detectors; the broader business detector phases remain incomplete. Railway runtime remains separately unverified.

## Immediate next milestone

Audit Policy + Detector SDK and the [Audit Rule Pack v1 foundation](AUDIT-RULE-PACK.md) are implemented. Completeness control `business.missing_required_field` is implemented. Sequence integrity control `business.sequence_gap` is implemented. Exact composite payment control `business.duplicate_payment` is implemented. Statistical amount control `business.amount_outlier` is implemented with Decimal-only Tukey median-of-halves IQR. Recommended next phase: Audit Rule Pack v1 integration and production-readiness verification. Advanced contextual rules remain not started.

Completed: PORT/test/example alignment, optional preview host, production static serving with SPA fallback, independent Railway contract, safe inspection, guarded rollback/reset, deterministic disposable database acceptance and verified source-reader grants. Source tables, fixture semantics and expected hashes are unchanged. See [current evidence](VERIFICATION.md).

Delivered after stabilization: typed contracts, restricted read-only extraction, deterministic JSONL snapshots/hashes, independent integrity validation, explicit operator provenance, central versions, immutable context, CLI lifecycle and local results. Policy-driven framework detectors and duplicate-reference, completeness, sequence-gap and duplicate-payment detection now run through the existing frozen-context SDK. Authentication/RBAC is required before remote audit access; database result writer and retention service remain deferred. See [framework](AUDIT-FRAMEWORK.md) and [ADR-009](adr/ADR-009-snapshot-based-audit-execution.md).

## Phase 0: Architecture & Documentation

- Status: VERIFIED locally; config, API/Web/Python and documentation checks pass. Railway manual validation is separate.
- Objective: Define boundaries and runnable foundation.
- Deliverables: Docs, diagrams, shell, health, schema tooling.
- Dependencies: None.
- Definition of done: Build and smoke checks pass; unresolved infrastructure validation explicitly recorded.

## Phase 1: Database Verification & Deterministic Synthetic Business Dataset

- Status: VERIFIED on disposable local PostgreSQL 17.5; no remote database acceptance claimed.
- Objective: Model source processes.
- Deliverables: Resolve Phase 1 questions, domain migrations, seed generator and truth manifest.
- Dependencies: Phase 0.
- Definition of done: Repeatable seeds, exact known anomalies, manifests, schema-aligned documentation and application checks. PostgreSQL migration/seed/validation/rollback and actual source-reader write-denial must pass before completion. See [verification](VERIFICATION.md).
- Delivered: eleven source tables, 14 anomaly categories, generator QA, reproducible local reset/seed workflow and dataset/process/lineage documentation.

## Phase 2: Authentication & RBAC Foundation

- Objective: Protect platform access.
- Deliverables: Hashing, JWT, refresh sessions, authorization matrix and activity events.
- Dependencies: Separate AuditLens identity/session design and a verified database foundation; business.users is not the platform identity model.
- Definition of done: 401/403/object-scope tests pass; no insecure bypass.

## Phase 3: Audit Framework

- Current local milestone: COMPLETE and locally verified; snapshots, CLI, provenance, result contracts, Audit Policy and Detector SDK. Three business rules are available in Audit Rule Pack v1; no database result tables exist.

- Objective: Execute reproducible validated runs.
- Deliverables: Extraction snapshots, manifests, versioned tests, results/evidence and CLI orchestration.
- Dependencies: Verified Phase 1 source and SELECT-only extraction. Full application authentication is not required for a local CLI framework. Decide explicit CLI provenance before introducing the proposed audit_runs.requested_by FK; do not fabricate business-user identities. Phase 2 is required before exposing authenticated audit operations remotely.
- Definition of done: A non-business harness verifies lifecycle, failures and immutable results.

## Phase 4: User Access Review

- Objective: Analyze account appropriateness.
- Deliverables: UA tests and versioned access baseline.
- Dependencies: Phase 3.
- Definition of done: Exact known anomaly sets detected with clean negatives.

## Phase 5: Segregation of Duties

- Objective: Explain incompatible permissions.
- Deliverables: SoD rules, permission expansion and conflicts.
- Dependencies: Phases 3â€“4.
- Definition of done: Cross-role combinations detected with traceable evidence.

## Phase 6: Transaction Testing

- Objective: Find transaction deviations.
- Deliverables: Duplicate, overpayment and approval tests.
- Dependencies: Phase 3 plus settled payment policy.
- Definition of done: Decimal/currency and valid partial-payment cases verified.

## Phase 7: Audit Trail Analysis

- Objective: Analyze changes and overrides.
- Deliverables: Event vocabulary, chronology tests and status history.
- Dependencies: Phases 1,3 and log completeness.
- Definition of done: Known material changes detected; missing logs reported.

## Phase 8: Findings Management

- Objective: Support human conclusions.
- Deliverables: Draft/review/closure workflow and evidence links.
- Dependencies: Phases 2â€“3 and at least one test module.
- Definition of done: Unauthorized transitions rejected; evidence retained.

## Phase 9: Dashboard & Reporting

- Objective: Communicate coverage and conclusions.
- Deliverables: Scope-aware summaries and exports.
- Dependencies: Phases 4â€“8.
- Definition of done: Counts reconcile to runs and findings; limitations displayed.

## Phase 10: Portfolio Polish

- Objective: Make work understandable and reproducible.
- Deliverables: Screenshots, walkthrough, CI and deployment assessment.
- Dependencies: Prior phases.
- Definition of done: Fresh-clone setup succeeds; synthetic-only demonstration reviewed.
