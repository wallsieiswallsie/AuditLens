# Data dictionary

## IMPLEMENTED IN PHASE 1 — business source tables

Generated from the Knex PostgreSQL DDL by `npm run docs:schema`. Column inventory, types, keys, checks and indexes below match the migration. For current PostgreSQL runtime acceptance see [verification](VERIFICATION.md). All data is fictional; sensitivity describes the analogous real-world field. No SQL defaults or automatic timestamp triggers exist: writers supply UUIDs and UTC timestamps. Foreign keys use ON DELETE RESTRICT. Primary keys imply NOT NULL. Approvals/logs are append-only by convention; runtime enforcement is deferred.

### business.employees

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | 805f49a5-aadd-4739-aea4-69f474c01d63 | internal |
| created_at | timestamptz | no | — | check (updated_at >= created_at) | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |
| updated_at | timestamptz | no | — | check (updated_at >= created_at) | Last source modification instant | 2026-01-05T02:00:00.000Z | internal |
| employee_number | text | no | — | UNIQUE; check (length(trim("employee_number")) > 0) | Unique fictional HR reference | EMP-0001 | internal |
| full_name | text | no | — | check (length(trim("full_name")) > 0) | Fictional employee display name | Fictional Employee 1 | personal (synthetic) |
| department | text | no | — | check (length(trim("department")) > 0) | Fictional job department | Finance | internal |
| status | text | no | — | check (status IN ('active','inactive')); check ((status = 'active' AND ended_at IS NULL) OR (status = 'inactive' AND ended_at >= hired_at)); check (status <> 'inactive' OR ended_at IS NOT NULL) | Employment/account/workflow state; allowed values in constraint | active | internal |
| hired_at | timestamptz | no | — | check ((status = 'active' AND ended_at IS NULL) OR (status = 'inactive' AND ended_at >= hired_at)) | Employment start instant | 2026-01-05T02:00:00.000Z | personal (synthetic) |
| ended_at | timestamptz | yes | — | check ((status = 'active' AND ended_at IS NULL) OR (status = 'inactive' AND ended_at >= hired_at)); check (status <> 'inactive' OR ended_at IS NOT NULL) | Employment end; required for inactive employees | null | personal (synthetic) |

Indexes: none beyond keys. Primary and unique constraints also create indexes.

### business.users

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | 0caa7292-be6e-42d0-ac70-75b3aac7ff44 | internal |
| created_at | timestamptz | no | — | check (updated_at >= created_at); check (last_login_at IS NULL OR last_login_at >= created_at) | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |
| updated_at | timestamptz | no | — | check (updated_at >= created_at) | Last source modification instant | 2026-09-11T03:00:00.000Z | internal |
| employee_id | uuid | yes | FK business.employees.id | check (account_type <> 'human' OR employee_id IS NOT NULL) | Employee owner; human accounts require an owner | 805f49a5-aadd-4739-aea4-69f474c01d63 | personal (synthetic) |
| email | text | no | — | UNIQUE; check (length(trim("email")) > 0); check (email = lower(trim(email))) | Lowercase synthetic account identifier | employee1@example.test | personal (synthetic) |
| account_type | text | no | — | check (account_type IN ('human','service')); check (account_type <> 'human' OR employee_id IS NOT NULL) | Human or service identity | human | internal |
| status | text | no | — | check (status IN ('active','disabled')) | Employment/account/workflow state; allowed values in constraint | active | internal |
| last_login_at | timestamptz | yes | — | check (last_login_at IS NULL OR last_login_at >= created_at) | Last successful login; null means never used | 2026-09-11T03:00:00.000Z | personal (synthetic) |

Indexes: `employee_id`; `status, last_login_at`. Primary and unique constraints also create indexes.

### business.roles

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | db08ae3a-f307-4094-a5c8-d0dd57a9b4ee | internal |
| created_at | timestamptz | no | — | check (updated_at >= created_at) | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |
| updated_at | timestamptz | no | — | check (updated_at >= created_at) | Last source modification instant | 2026-01-05T02:00:00.000Z | internal |
| code | text | no | — | UNIQUE; check (length(trim("code")) > 0) | Stable unique master reference | administrator | internal |
| name | text | no | — | check (length(trim("name")) > 0) | Fictional display name | administrator | internal |

Indexes: none beyond keys. Primary and unique constraints also create indexes.

### business.permissions

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | be783756-6d18-4910-ac3b-afe40473f4e6 | internal |
| created_at | timestamptz | no | — | check (updated_at >= created_at) | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |
| updated_at | timestamptz | no | — | check (updated_at >= created_at) | Last source modification instant | 2026-01-05T02:00:00.000Z | internal |
| code | text | no | — | UNIQUE; check (length(trim("code")) > 0) | Stable unique master reference | audit_log.read | internal |
| is_privileged | boolean | no | — | — | Project policy sensitive administrative capability flag | false | internal |

Indexes: none beyond keys. Primary and unique constraints also create indexes.

### business.user_roles

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| user_id | uuid | no | PK, FK business.users.id | — | Assigned source account | 0caa7292-be6e-42d0-ac70-75b3aac7ff44 | internal |
| role_id | uuid | no | PK, FK business.roles.id | — | Assigned or granting source role | 469893b0-6574-40e4-ad46-a88e5de664de | internal |
| created_at | timestamptz | no | — | — | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |

Indexes: `user_id`; `role_id`. Primary and unique constraints also create indexes.

### business.role_permissions

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| role_id | uuid | no | PK, FK business.roles.id | — | Assigned or granting source role | db08ae3a-f307-4094-a5c8-d0dd57a9b4ee | internal |
| permission_id | uuid | no | PK, FK business.permissions.id | — | Granted capability | 5eff1d8d-306f-473c-a3c0-e83aef7d2c79 | internal |
| created_at | timestamptz | no | — | — | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |

Indexes: `role_id`; `permission_id`. Primary and unique constraints also create indexes.

### business.vendors

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | 4d751393-9767-4f6e-a467-b4dcf3905987 | internal |
| created_at | timestamptz | no | — | check (updated_at >= created_at) | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |
| updated_at | timestamptz | no | — | check (updated_at >= created_at) | Last source modification instant | 2026-01-05T02:00:00.000Z | internal |
| code | text | no | — | UNIQUE; check (length(trim("code")) > 0) | Stable unique master reference | VEN-1 | internal |
| name | text | no | — | check (length(trim("name")) > 0) | Fictional display name | Fictional Supplier 1 | internal |

Indexes: none beyond keys. Primary and unique constraints also create indexes.

### business.invoices

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | 392fad23-450b-43ff-a86c-9116ca94a1d5 | internal |
| created_at | timestamptz | no | — | check (updated_at >= created_at) | Source insertion instant | 2026-08-03T02:00:00.000Z | internal |
| updated_at | timestamptz | no | — | check (updated_at >= created_at) | Last source modification instant | 2026-08-03T05:30:00.000Z | internal |
| vendor_id | uuid | no | FK business.vendors.id | — | Fictional supplier issuing invoice | 4d751393-9767-4f6e-a467-b4dcf3905987 | internal |
| reference | text | no | — | check (length(trim("reference")) > 0) | External business reference; duplicates represent control failures | INV-000001 | financial (synthetic) |
| amount | numeric(18, 2) | no | — | check (amount > 0) | Positive gross amount; serialized as exact decimal string | 46221.00 | financial (synthetic) |
| currency | char(3) | no | — | check (currency IN ('IDR')) | Fixture currency; IDR only | IDR | financial (synthetic) |
| status | text | no | — | check (status IN ('draft','submitted','approved','paid','void')) | Employment/account/workflow state; allowed values in constraint | paid | internal |
| created_by | uuid | no | FK business.users.id | — | Source creator account | 0caa7292-be6e-42d0-ac70-75b3aac7ff44 | personal (synthetic) |
| supporting_reference | text | yes | — | — | Synthetic reference only; never fetch arbitrary URLs | sample://invoice/1 | internal |

Indexes: `vendor_id`; `created_by`; `vendor_id, reference, currency, amount`; `status, created_at`. Primary and unique constraints also create indexes.

### business.invoice_approvals

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | 8206ce1a-ba1c-40e7-aa8f-14573949a900 | internal |
| created_at | timestamptz | no | — | check (created_at >= decided_at) | Source insertion instant | 2026-08-03T03:00:00.000Z | internal |
| invoice_id | uuid | no | FK business.invoices.id | — | Parent invoice | 392fad23-450b-43ff-a86c-9116ca94a1d5 | internal |
| decided_by | uuid | no | FK business.users.id | — | Account making the approval decision | 0caa7292-be6e-42d0-ac70-75b3aac7ff44 | personal (synthetic) |
| decision | text | no | — | check (decision IN ('approved','rejected')) | Approved or rejected decision | approved | internal |
| decided_at | timestamptz | no | — | check (created_at >= decided_at) | Decision instant; authoritative approval time | 2026-08-03T03:00:00.000Z | internal |

Indexes: `invoice_id`; `decided_by`; `invoice_id, decided_at`. Primary and unique constraints also create indexes.

### business.payments

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | 93439682-0101-4cb8-a36d-8af3b40b2e08 | internal |
| created_at | timestamptz | no | — | check (updated_at >= created_at); check (confirmed_at IS NULL OR (confirmed_at >= created_at AND updated_at >= confirmed_at)) | Source insertion instant | 2026-08-03T04:00:00.000Z | internal |
| updated_at | timestamptz | no | — | check (updated_at >= created_at); check (confirmed_at IS NULL OR (confirmed_at >= created_at AND updated_at >= confirmed_at)) | Last source modification instant | 2026-08-03T04:30:00.000Z | internal |
| invoice_id | uuid | no | FK business.invoices.id | — | Parent invoice | 392fad23-450b-43ff-a86c-9116ca94a1d5 | internal |
| reference | text | no | — | check (length(trim("reference")) > 0) | External business reference; duplicates represent control failures | PAY-1 | financial (synthetic) |
| amount | numeric(18, 2) | no | — | check (amount > 0) | Positive gross amount; serialized as exact decimal string | 23110.50 | financial (synthetic) |
| currency | char(3) | no | — | check (currency IN ('IDR')) | Fixture currency; IDR only | IDR | financial (synthetic) |
| status | text | no | — | check (status IN ('pending','confirmed','void')); check ((status = 'confirmed' AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL) OR (status <> 'confirmed' AND confirmed_by IS NULL AND confirmed_at IS NULL)) | Employment/account/workflow state; allowed values in constraint | confirmed | internal |
| created_by | uuid | no | FK business.users.id | — | Source creator account | dd542519-a6fd-4406-ada0-068d333332f7 | personal (synthetic) |
| confirmed_by | uuid | yes | FK business.users.id | check ((status = 'confirmed' AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL) OR (status <> 'confirmed' AND confirmed_by IS NULL AND confirmed_at IS NULL)) | Confirmer; required only when confirmed | 8118a0b9-682d-4183-ab8b-36b698b0576c | personal (synthetic) |
| confirmed_at | timestamptz | yes | — | check ((status = 'confirmed' AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL) OR (status <> 'confirmed' AND confirmed_by IS NULL AND confirmed_at IS NULL)); check (confirmed_at IS NULL OR (confirmed_at >= created_at AND updated_at >= confirmed_at)) | Confirmation instant; required only when confirmed | 2026-08-03T04:30:00.000Z | internal |

Indexes: `invoice_id`; `created_by`; `confirmed_by`; `invoice_id, reference, currency, amount`. Primary and unique constraints also create indexes.

### business.audit_logs

| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id | uuid | no | PK | — | Immutable synthetic source UUID | 286cb4a7-304f-4e0c-a6d8-c07400edc12a | internal |
| created_at | timestamptz | no | — | check (created_at >= occurred_at) | Source insertion instant | 2026-01-05T02:00:00.000Z | internal |
| actor_id | uuid | yes | FK business.users.id | — | Source event actor; null for system events | e5df1ea3-96d0-4516-a677-5635bad1a033 | personal (synthetic) |
| action | text | no | — | check (length(trim("action")) > 0); check (action IN ('user.role_assigned','user.role_removed','invoice.created','invoice.submitted','invoice.updated','invoice.approved','invoice.rejected','invoice.paid','invoice.voided','payment.created','payment.confirmed','payment.status_overridden')) | Allowlisted source event action | user.role_assigned | internal |
| entity_type | text | no | — | check (entity_type IN ('user','invoice','payment')) | Source entity kind | user | internal |
| entity_id | uuid | no | — | — | Source snapshot identifier; deliberately no FK | 0caa7292-be6e-42d0-ac70-75b3aac7ff44 | internal |
| before_data | jsonb | yes | — | — | Redacted values before change | null | sensitive (synthetic) |
| after_data | jsonb | yes | — | — | Redacted values after change | {"role_id":"469893b0-6574-40e4-ad46-a88e5de664de","change_reference":"sample://access/1"} | sensitive (synthetic) |
| occurred_at | timestamptz | no | — | check (created_at >= occurred_at) | Source event instant | 2026-01-05T02:00:00.000Z | internal |

Indexes: `actor_id`; `entity_type, entity_id, occurred_at`; `action, occurred_at`. Primary and unique constraints also create indexes.

## PLANNED — audit schema

The following audit tables are proposed only. Common planned columns: id uuid primary key; created_at timestamptz not null; mutable entities also have updated_at timestamptz not null. Junctions use composite primary keys. No audit domain migrations exist.

## audit.users

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| email | text | no | UNIQUE | Auditor login | auditor@example.test | normalized lowercase | personal |
| password_hash | text | no | — | Encoded password hash | <argon2id hash> | never plaintext or API response | secret |
| role | text | no | — | Initial platform role | auditor | viewer/auditor/manager; policy pending | internal |
| status | text | no | — | Access state | active | active/disabled | internal |

## audit.risks

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | text | no | UNIQUE | Risk identifier | R-001 | stable | internal |
| title | text | no | — | Risk name | Unauthorized access | nonempty | internal |
| description | text | no | — | Exposure description | Former staff retain access | nonempty | internal |

## audit.controls

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | text | no | UNIQUE | Control identifier | C-001 | stable | internal |
| title | text | no | — | Control name | Access review | nonempty | internal |
| expectation | text | no | — | Project control criterion | Disable inactive accounts | nonempty | internal |
| control_type | text | no | — | Control classification | preventive | preventive/detective/corrective | internal |
| frequency | text | no | — | Control frequency | monthly | document owner policy | internal |

## audit.risk_controls

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| risk_id | uuid | no | PK, FK risks | Mapped risk | UUID | unique pair | internal |
| control_id | uuid | no | PK, FK controls | Mapped control | UUID | unique pair | internal |

## audit.audit_tests

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | text | no | UNIQUE with version | Catalog ID | UA-001 | catalog format | internal |
| version | integer | no | UNIQUE with code | Immutable definition version | 1 | positive | internal |
| name | text | no | — | Test name | Dormant Account | nonempty | internal |
| definition | jsonb | no | — | Logic and parameter specification | {"days":90} | validated per test schema | internal |

## audit.control_tests

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control_id | uuid | no | PK, FK controls | Control coverage | UUID | unique pair | internal |
| test_id | uuid | no | PK, FK audit_tests | Versioned test | UUID | unique pair | internal |

## audit.audit_runs

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| requested_by | uuid | no | FK users | Requesting auditor | UUID | active authorized identity | personal |
| status | text | no | — | Execution state | queued | queued/running/completed/failed/cancelled | internal |
| dataset_reference | text | no | — | Immutable extract identity | synthetic-v1 | versioned manifest reference | internal |
| parameters | jsonb | no | — | Frozen run options | {"timezone":"Asia/Jakarta"} | allowlisted options | internal |
| started_at | timestamptz | yes | — | Start | 2026-08-12T00:00:00Z | UTC | internal |
| finished_at | timestamptz | yes | — | Completion | 2026-08-12T00:01:00Z | not before start | internal |

## audit.audit_test_results

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| run_id | uuid | no | FK audit_runs | Execution parent | UUID | unique with test_id | internal |
| test_id | uuid | no | FK audit_tests | Exact test version | UUID | unique with run_id | internal |
| outcome | text | no | — | Test outcome | exception | pass/exception/error | internal |
| population_count | integer | no | — | Eligible records | 100 | nonnegative | internal |
| exception_count | integer | no | — | Flagged units | 20 | nonnegative; unit defined per test | internal |
| summary | jsonb | no | — | Metrics and validation errors | {"unit":"account"} | no credentials | internal |

## audit.evidence

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| result_id | uuid | no | FK audit_test_results | Origin test result | UUID | immutable parent | internal |
| source_reference | text | no | — | Source record or group identity | business.users:UUID | snapshot reference; not cross-schema FK | internal |
| snapshot | jsonb | no | — | Minimal preserved facts | {"status":"active"} | redacted, schema validated | sensitive |
| sha256 | char(64) | no | — | Canonical snapshot digest | 64 lowercase hex characters | hash canonical UTF-8 JSON | internal |
| captured_at | timestamptz | no | — | Capture time | 2026-08-12T00:00:00Z | UTC | internal |

## audit.findings

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| title | text | no | — | Finding title | Inactive account remains enabled | nonempty | internal |
| condition | text | no | — | Observed facts | Account remained active | evidence-backed | sensitive |
| criteria | text | no | — | Control expectation | Disable inactive employee access | cite control version in narrative | internal |
| risk_id | uuid | no | FK risks | Primary risk | UUID | existing risk | internal |
| impact | text | no | — | Potential consequence | Unauthorized transactions | distinguish actual and potential | internal |
| recommendation | text | no | — | Proposed response | Disable and review access | actionable | internal |
| severity | text | no | — | Reviewed severity | medium | low/medium/high/critical | internal |
| status | text | no | — | Finding state | draft | documented lifecycle | internal |
| responsible_party | text | yes | — | Business owner reference | Finance operations | required before open; not auditor FK | personal |
| created_by | uuid | no | FK users | Author | UUID | authorized auditor | personal |

## audit.finding_evidence

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| finding_id | uuid | no | PK, FK findings | Finding | UUID | unique pair | internal |
| evidence_id | uuid | no | PK, FK evidence | Preserved evidence | UUID | unique pair | internal |

## audit.sod_rules

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | text | no | UNIQUE with version | Rule ID | SOD-001 | stable | internal |
| version | integer | no | UNIQUE with code | Rule version | 1 | positive | internal |
| permission_a | text | no | — | First source permission code | invoice.create | snapshot code; no cross-schema FK | internal |
| permission_b | text | no | — | Conflicting permission code | invoice.approve | different from a | internal |
| severity | text | no | — | Default review guidance | high | low/medium/high/critical | internal |

## audit.sod_conflicts

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| result_id | uuid | no | FK audit_test_results | Origin result | UUID | unique with rule and source user | internal |
| rule_id | uuid | no | FK sod_rules | Exact rule version | UUID | existing rule | internal |
| source_user_id | uuid | no | — | Source account snapshot ID | UUID | no cross-schema FK | personal |
| evidence_id | uuid | no | FK evidence | Supporting permission snapshot | UUID | must belong to same result | sensitive |

## audit.activity_events

| Name | Type | Nullable | Key | Purpose | Example | Validation | Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| actor_id | uuid | yes | FK users | Platform actor | UUID | null for engine/system | personal |
| action | text | no | — | Platform event | finding.closed | allowlisted actions | internal |
| entity_type | text | no | — | Entity type | finding | allowlist | internal |
| entity_id | uuid | no | — | Entity snapshot ID | UUID | not FK | internal |
| details | jsonb | no | — | Redacted transition details | {"from":"remediated","to":"closed"} | exclude secrets | sensitive |
| occurred_at | timestamptz | no | — | Event time | 2026-08-12T00:00:00Z | UTC | internal |

