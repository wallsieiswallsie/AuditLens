# Entity relationship design

**Business tables are IMPLEMENTED in the Phase 1 migration; audit tables remain PLANNED.** Disposable local PostgreSQL 17.5 migration, constraint and fixture acceptance passed; Railway runtime remains separately unverified. See [verification](VERIFICATION.md). Migration source is under apps/api/database/migrations. The design separates identity domains and preserves source evidence without cross-schema foreign keys.

## Conceptual ERD
```mermaid
erDiagram
  EMPLOYEE ||--o{ BUSINESS_ACCOUNT : owns
  BUSINESS_ACCOUNT }o--o{ BUSINESS_ROLE : assigned
  BUSINESS_ROLE }o--o{ PERMISSION : grants
  VENDOR ||--o{ INVOICE : issues
  INVOICE ||--o{ APPROVAL : receives
  INVOICE ||--o{ PAYMENT : settles
  RISK }o--o{ CONTROL : mitigated_by
  CONTROL }o--o{ TEST : evaluated_by
  RUN ||--o{ RESULT : contains
  TEST ||--o{ RESULT : produces
  RESULT ||--o{ EVIDENCE : preserves
  FINDING }o--o{ EVIDENCE : supported_by
```

## Logical ERD
Names prefixed business_ and audit_ represent their PostgreSQL schemas. Each FK line below is explained in the relationship inventory.

### A. Demo Business System — IMPLEMENTED IN PHASE 1

Migration implemented; runtime acceptance is recorded in VERIFICATION.md. Names use `business_` to represent the business schema.

```mermaid
erDiagram
  business_employees {
    uuid id PK
    timestamptz created_at
    timestamptz updated_at
    text employee_number
    text full_name
    text department
    text status
    timestamptz hired_at
    timestamptz ended_at
  }
  business_users {
    uuid id PK
    timestamptz created_at
    timestamptz updated_at
    uuid employee_id FK
    text email
    text account_type
    text status
    timestamptz last_login_at
  }
  business_employees |o--o{ business_users : employee_id
  business_roles {
    uuid id PK
    timestamptz created_at
    timestamptz updated_at
    text code
    text name
  }
  business_permissions {
    uuid id PK
    timestamptz created_at
    timestamptz updated_at
    text code
    boolean is_privileged
  }
  business_user_roles {
    uuid user_id PK
    uuid role_id PK
    timestamptz created_at
  }
  business_users ||--o{ business_user_roles : user_id
  business_roles ||--o{ business_user_roles : role_id
  business_role_permissions {
    uuid role_id PK
    uuid permission_id PK
    timestamptz created_at
  }
  business_roles ||--o{ business_role_permissions : role_id
  business_permissions ||--o{ business_role_permissions : permission_id
  business_vendors {
    uuid id PK
    timestamptz created_at
    timestamptz updated_at
    text code
    text name
  }
  business_invoices {
    uuid id PK
    timestamptz created_at
    timestamptz updated_at
    uuid vendor_id FK
    text reference
    numeric amount
    char currency
    text status
    uuid created_by FK
    text supporting_reference
  }
  business_vendors ||--o{ business_invoices : vendor_id
  business_users ||--o{ business_invoices : created_by
  business_invoice_approvals {
    uuid id PK
    timestamptz created_at
    uuid invoice_id FK
    uuid decided_by FK
    text decision
    timestamptz decided_at
  }
  business_invoices ||--o{ business_invoice_approvals : invoice_id
  business_users ||--o{ business_invoice_approvals : decided_by
  business_payments {
    uuid id PK
    timestamptz created_at
    timestamptz updated_at
    uuid invoice_id FK
    text reference
    numeric amount
    char currency
    text status
    uuid created_by FK
    uuid confirmed_by FK
    timestamptz confirmed_at
  }
  business_invoices ||--o{ business_payments : invoice_id
  business_users ||--o{ business_payments : created_by
  business_users |o--o{ business_payments : confirmed_by
  business_audit_logs {
    uuid id PK
    timestamptz created_at
    uuid actor_id FK
    text action
    text entity_type
    uuid entity_id
    jsonb before_data
    jsonb after_data
    timestamptz occurred_at
  }
  business_users |o--o{ business_audit_logs : actor_id
```

### B. AuditLens — PLANNED
```mermaid
erDiagram
  audit_users {
    uuid id PK
    text email
    text password_hash
    text role
    text status
    timestamptz created_at
    timestamptz updated_at
  }
  audit_risks {
    uuid id PK
    text code
    text title
    text description
    timestamptz created_at
    timestamptz updated_at
  }
  audit_controls {
    uuid id PK
    text code
    text title
    text expectation
    text control_type
    text frequency
    timestamptz created_at
    timestamptz updated_at
  }
  audit_risk_controls {
    uuid risk_id PK
    uuid control_id PK
    timestamptz created_at
  }
  audit_risks ||--o{ audit_risk_controls : risk_id
  audit_controls ||--o{ audit_risk_controls : control_id
  audit_audit_tests {
    uuid id PK
    text code
    integer version
    text name
    jsonb definition
    timestamptz created_at
  }
  audit_control_tests {
    uuid control_id PK
    uuid test_id PK
    timestamptz created_at
  }
  audit_controls ||--o{ audit_control_tests : control_id
  audit_audit_tests ||--o{ audit_control_tests : test_id
  audit_audit_runs {
    uuid id PK
    uuid requested_by FK
    text status
    text dataset_reference
    jsonb parameters
    timestamptz started_at
    timestamptz finished_at
    timestamptz created_at
    timestamptz updated_at
  }
  audit_users ||--o{ audit_audit_runs : requested_by
  audit_audit_test_results {
    uuid id PK
    uuid run_id FK
    uuid test_id FK
    text outcome
    integer population_count
    integer exception_count
    jsonb summary
    timestamptz created_at
  }
  audit_audit_runs ||--o{ audit_audit_test_results : run_id
  audit_audit_tests ||--o{ audit_audit_test_results : test_id
  audit_evidence {
    uuid id PK
    uuid result_id FK
    text source_reference
    jsonb snapshot
    char sha256
    timestamptz captured_at
    timestamptz created_at
  }
  audit_audit_test_results ||--o{ audit_evidence : result_id
  audit_findings {
    uuid id PK
    text title
    text condition
    text criteria
    uuid risk_id FK
    text impact
    text recommendation
    text severity
    text status
    text responsible_party
    uuid created_by FK
    timestamptz created_at
    timestamptz updated_at
  }
  audit_risks ||--o{ audit_findings : risk_id
  audit_users ||--o{ audit_findings : created_by
  audit_finding_evidence {
    uuid finding_id PK
    uuid evidence_id PK
    timestamptz created_at
  }
  audit_findings ||--o{ audit_finding_evidence : finding_id
  audit_evidence ||--o{ audit_finding_evidence : evidence_id
  audit_sod_rules {
    uuid id PK
    text code
    integer version
    text permission_a
    text permission_b
    text severity
    timestamptz created_at
  }
  audit_sod_conflicts {
    uuid id PK
    uuid result_id FK
    uuid rule_id FK
    uuid source_user_id
    uuid evidence_id FK
    timestamptz created_at
  }
  audit_audit_test_results ||--o{ audit_sod_conflicts : result_id
  audit_sod_rules ||--o{ audit_sod_conflicts : rule_id
  audit_evidence ||--o{ audit_sod_conflicts : evidence_id
  audit_activity_events {
    uuid id PK
    uuid actor_id FK
    text action
    text entity_type
    uuid entity_id
    jsonb details
    timestamptz occurred_at
    timestamptz created_at
  }
  audit_users |o--o{ audit_activity_events : actor_id
```

## Relationship inventory

- business.users.employee_id → business.employees: each child references zero or one parent; a parent can have zero or many children. Human owner; null for service accounts.
- business.user_roles.user_id → business.users: each child references exactly one parent; a parent can have zero or many children. Assigned account.
- business.user_roles.role_id → business.roles: each child references exactly one parent; a parent can have zero or many children. Assigned role.
- business.role_permissions.role_id → business.roles: each child references exactly one parent; a parent can have zero or many children. Role.
- business.role_permissions.permission_id → business.permissions: each child references exactly one parent; a parent can have zero or many children. Capability.
- business.invoices.vendor_id → business.vendors: each child references exactly one parent; a parent can have zero or many children. Supplier.
- business.invoices.created_by → business.users: each child references exactly one parent; a parent can have zero or many children. Creator.
- business.invoice_approvals.invoice_id → business.invoices: each child references exactly one parent; a parent can have zero or many children. Reviewed invoice.
- business.invoice_approvals.decided_by → business.users: each child references exactly one parent; a parent can have zero or many children. Decision maker.
- business.payments.invoice_id → business.invoices: each child references exactly one parent; a parent can have zero or many children. Paid invoice.
- business.payments.created_by → business.users: each child references exactly one parent; a parent can have zero or many children. Creator.
- business.payments.confirmed_by → business.users: each child references zero or one parent; a parent can have zero or many children. Confirmer.
- business.audit_logs.actor_id → business.users: each child references zero or one parent; a parent can have zero or many children. Actor; null for system event.
- audit.risk_controls.risk_id → audit.risks: each child references exactly one parent; a parent can have zero or many children. Mapped risk.
- audit.risk_controls.control_id → audit.controls: each child references exactly one parent; a parent can have zero or many children. Mapped control.
- audit.control_tests.control_id → audit.controls: each child references exactly one parent; a parent can have zero or many children. Control coverage.
- audit.control_tests.test_id → audit.audit_tests: each child references exactly one parent; a parent can have zero or many children. Versioned test.
- audit.audit_runs.requested_by → audit.users: each child references exactly one parent; a parent can have zero or many children. Requesting auditor.
- audit.audit_test_results.run_id → audit.audit_runs: each child references exactly one parent; a parent can have zero or many children. Execution parent.
- audit.audit_test_results.test_id → audit.audit_tests: each child references exactly one parent; a parent can have zero or many children. Exact test version.
- audit.evidence.result_id → audit.audit_test_results: each child references exactly one parent; a parent can have zero or many children. Origin test result.
- audit.findings.risk_id → audit.risks: each child references exactly one parent; a parent can have zero or many children. Primary risk.
- audit.findings.created_by → audit.users: each child references exactly one parent; a parent can have zero or many children. Author.
- audit.finding_evidence.finding_id → audit.findings: each child references exactly one parent; a parent can have zero or many children. Finding.
- audit.finding_evidence.evidence_id → audit.evidence: each child references exactly one parent; a parent can have zero or many children. Preserved evidence.
- audit.sod_conflicts.result_id → audit.audit_test_results: each child references exactly one parent; a parent can have zero or many children. Origin result.
- audit.sod_conflicts.rule_id → audit.sod_rules: each child references exactly one parent; a parent can have zero or many children. Exact rule version.
- audit.sod_conflicts.evidence_id → audit.evidence: each child references exactly one parent; a parent can have zero or many children. Supporting permission snapshot.
- audit.activity_events.actor_id → audit.users: each child references zero or one parent; a parent can have zero or many children. Platform actor.

## Normalization and responsibility decisions
Employees and users are separate because employment and access status differ; one employee can own multiple accounts. Vendors provide a stable duplicate-invoice grouping key. Role assignments and control coverage use junctions to avoid arrays and many-to-many duplication. One payment applies to one invoice in the initial proposed model; multiple partial payments are possible.

A generic transactions table is deferred: invoices and payments already represent distinct business events and a catch-all would blur validation. Business audit_logs record source activity, while audit.activity_events record platform activity. Source password/session design is deferred until authentication; audit.users is a distinct platform identity.

Evidence is a standalone snapshot entity because exceptions need evidence before a finding exists and multiple findings may cite the same evidence. finding_evidence is therefore a junction. sod_conflicts is a typed projection for explainable rule/user combinations, tied to evidence and results rather than a second independent truth. Validate evidence/result consistency before persistence.

Source references deliberately are not FKs: findings must survive source mutation/deletion. Reports will be derived views rather than a table until export retention requirements exist. The eleven business domain tables have migrations; audit domain tables remain planned.
