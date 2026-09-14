# AuditLens project overview

**Status: Phase 1 source dataset implemented; database runtime verification pending. All audit capabilities described here are planned.**

## Technical explanation
AuditLens is a modular digital audit and internal control testing platform. A synthetic Demo Business System produces users, permissions, invoices, approvals, payments and activity records. AuditLens reads that source through a restricted database identity, validates the population, executes versioned tests and preserves evidence for human review. Its own findings and results belong to a separate audit schema.

The problem is that scattered permissions and transaction records make control failures difficult to identify consistently. Repeatable analysis makes the review traceable; it does not establish fraud or replace professional judgment.

## Plain-language explanation
Think of a practice company and an independent inspection desk. The practice company records work and payments. The inspection desk checks copies of those records for things that need explanation, such as an account still active after an employee leaves. An auditor decides whether an alert deserves a finding.

## Users and objectives
Auditors review exceptions and evidence. Audit managers review findings and reporting. Business owners explain exceptions and own remediation. Demo employees operate the future source application. Developers maintain reproducible datasets and tests.

The objectives are to demonstrate system analysis, database design, RBAC, segregation of duties, data integrity, risk assessment, audit trails and full-stack engineering in a readable portfolio.

## Scope
Current: documentation, business domain migrations, deterministic synthetic generator and fixture QA, web placeholders, API health and Python health execution.
Future: authentication, access review, SoD, transaction and log testing, risk/control mapping, findings and reporting.
Excluded: production ERP integration, real employee data, certification, proprietary methodologies and automated assurance opinions.

## Limitations and motivation
Synthetic records simplify organizational complexity. Detected exceptions require context, completeness checks and human assessment. Local administrators can alter this development database; immutable evidence is not yet delivered. The project exists to make audit concepts concrete through an incremental software implementation.
