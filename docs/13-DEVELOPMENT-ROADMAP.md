# Development roadmap

Phase 0 foundation delivered with infrastructure limitations recorded. Phase 1 source implementation and offline QA delivered; full completion remains blocked on PostgreSQL runtime and actual source-reader write-denial verification. Phases 2 onward are planned.

## Phase 0: Architecture & Documentation

- Status: Delivered; original database runtime limitation remains recorded.
- Objective: Define boundaries and runnable foundation.
- Deliverables: Docs, diagrams, shell, health, schema tooling.
- Dependencies: None.
- Definition of done: Build and smoke checks pass; unresolved infrastructure validation explicitly recorded.

## Phase 1: Database Verification & Deterministic Synthetic Business Dataset

- Status: Implementation and offline tests delivered; NOT fully complete.
- Objective: Model source processes.
- Deliverables: Resolve Phase 1 questions, domain migrations, seed generator and truth manifest.
- Dependencies: Phase 0.
- Definition of done: Repeatable seeds, exact known anomalies, manifests, schema-aligned documentation and application checks. PostgreSQL migration/seed/validation/rollback and actual source-reader write-denial must pass before completion. See [verification](VERIFICATION.md).
- Delivered: eleven source tables, 14 anomaly categories, generator QA, reproducible local reset/seed workflow and dataset/process/lineage documentation.

## Phase 2: Authentication & RBAC Foundation

- Objective: Protect platform access.
- Deliverables: Hashing, JWT, refresh sessions, authorization matrix and activity events.
- Dependencies: Identity model from Phase 1.
- Definition of done: 401/403/object-scope tests pass; no insecure bypass.

## Phase 3: Audit Framework

- Objective: Execute reproducible validated runs.
- Deliverables: Extraction snapshots, manifests, versioned tests, results/evidence and CLI orchestration.
- Dependencies: Phases 1–2.
- Definition of done: A non-business harness verifies lifecycle, failures and immutable results.

## Phase 4: User Access Review

- Objective: Analyze account appropriateness.
- Deliverables: UA tests and versioned access baseline.
- Dependencies: Phase 3.
- Definition of done: Exact known anomaly sets detected with clean negatives.

## Phase 5: Segregation of Duties

- Objective: Explain incompatible permissions.
- Deliverables: SoD rules, permission expansion and conflicts.
- Dependencies: Phases 3–4.
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
- Dependencies: Phases 2–3 and at least one test module.
- Definition of done: Unauthorized transitions rejected; evidence retained.

## Phase 9: Dashboard & Reporting

- Objective: Communicate coverage and conclusions.
- Deliverables: Scope-aware summaries and exports.
- Dependencies: Phases 4–8.
- Definition of done: Counts reconcile to runs and findings; limitations displayed.

## Phase 10: Portfolio Polish

- Objective: Make work understandable and reproducible.
- Deliverables: Screenshots, walkthrough, CI and deployment assessment.
- Dependencies: Prior phases.
- Definition of done: Fresh-clone setup succeeds; synthetic-only demonstration reviewed.

