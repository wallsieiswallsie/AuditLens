# Synthetic dataset v1

AuditLens uses artificial records to practice repeatable internal-control testing without real employees, customers or proprietary corporate data. All people are numbered Fictional Employees with example.test email addresses; all vendors are Fictional Suppliers. No real corporate or PwC data or methodology is used.

## Structure and size

The generator is split into core seed/ID utilities, reference data, ordinary transactions, anomaly injection, source activity logs, manifests and independent fixture QA under database/generators and database/validation. Knex migrates eleven source tables in business. The audit schema remains empty; no finding or test result is inserted into source records.

| Table | Rows |
| --- | ---: |
| employees | 250 |
| users | 250 |
| roles | 8 |
| permissions | 17 |
| user_roles | 250 |
| role_permissions | 27 |
| vendors | 100 |
| invoices | 2,000 |
| invoice_approvals | 1,840 |
| payments | 2,400 |
| audit_logs | 12,512 |

Invoices: 1,600 paid, 200 approved, 100 submitted, 50 draft, 50 void. Approval rows: 1,790 approved, 50 rejected. Payments: 800 invoices have two equal partial payments, 800 have one full payment. Exceptions then alter selected source facts. LOG-001 deliberately leaves the historical paid state after a material amount increase; it is not a fresh settlement calculation.

Among 4,650 account/invoice/payment entities, 152 are directly named by anomaly fixtures or their event targets (count each entity once), leaving 4,498 / 96.73% ordinary entities by that measure. Related records such as a payment's parent invoice are not recursively counted. This is a fixture composition measure, not a risk rate; the account subset has proportionally more access examples.

## Reproducibility and artifacts

Default AUDITLENS_DATA_SEED=20260914 accepts unsigned 32-bit integers. A seeded LCG varies amounts, and SHA-256 of version/seed/entity/ordinal produces stable UUID-shaped identifiers. No Math.random, randomUUID, wall clock, external data or Faker dependency is used. Dates are fixed UTC instants; generatedAt is the logical generation date, 2026-09-14T10:00:00.000Z, not the command execution time. Changing seed changes identifiers/amounts but preserves counts and business conventions.

[Dataset metadata](../database/sample-data/dataset-manifest.json) records version, seed, logical date, counts, expected anomaly counts and per-table hashes. Hashes sort rows and object keys, normalize UTC timestamp strings, and preserve decimal strings. They prove consistency against a known fixture, not external tamper resistance.

[Ground truth](../database/sample-data/ground-truth.json) stores anomaly category, explicit unit, source table, exact source IDs and duplicate-group membership. Duplicate invoice count 10 means 10 pairs / 20 rows / 10 excess rows. Duplicate payment count 12 means 12 pairs / 24 rows / 12 excess rows. Partial duplicate payments retain their original half amounts, preventing additional overpayment matches. Source event categories identify event IDs; event targets provide invoice/payment/account lineage. No anomaly marker columns exist in business tables.

[Fixture policy](../database/sample-data/fixture-policy.json) records the versioned role baseline, clock, timezone and calendar. This is independent expected policy configuration. Ground truth is restricted to development, automated testing and benchmark validation. **Future detection logic must never read ground-truth.json or import generator/fixture QA code during analysis.**

## Known anomalies and future procedures

All criteria are AuditLens project-defined examples, not authoritative professional audit standards. Decisions and alternatives are in [ADR-005](adr/ADR-005-phase-1-dataset-conventions.md).

| Anomaly ID | Category | Description | Expected count | Relevant business tables | Future audit test |
| --- | --- | --- | ---: | --- | --- |
| AC-001 | Access | Inactive employee, active account | 8 accounts | employees, users | UA-002 |
| AC-002 | Access | Dormant active account | 12 accounts | users | UA-001 |
| AC-003 | Access | Role exceeds fixture baseline | 6 accounts | users, user_roles, roles, role_permissions, permissions | UA-003 |
| SOD-001 | SoD | Creator also approves invoice | 10 invoices | invoices, invoice_approvals | SOD-003 observed; SOD-001 entitlement is separate |
| SOD-002 | SoD | Creator also confirms payment | 8 payments | payments | SOD-004 observed; SOD-002 entitlement is separate |
| TX-001 | Transaction | Duplicate invoice business key | 10 groups | invoices, vendors | TX-001 |
| TX-002 | Transaction | Duplicate confirmed payment key | 12 groups | payments, invoices | TX-002 |
| TX-003 | Transaction | Confirmed cumulative amount exceeds invoice | 8 invoices | invoices, payments | TX-003 |
| TX-004 | Transaction | Required approval missing | 10 invoices | invoices, invoice_approvals, payments | TX-004 |
| TX-005 | Transaction | Creation after employee ended_at | 8 events | audit_logs, users, employees | TX-005 employment-ending subset |
| TX-006 | Transaction | Creation outside business hours | 20 events | audit_logs, invoices | TX-006 creation-event scope |
| LOG-001 | Trail | Material invoice change after approval | 10 events | audit_logs, invoices, invoice_approvals | LOG-001 |
| LOG-002 | Trail | Manual status override | 8 events | audit_logs, payments | LOG-002 |
| LOG-003 | Trail | Role removal/grant without approved reference | 12 events | audit_logs, users, roles | LOG-003 |

Exceptions use disjoint transaction selections. Six excessive-access accounts are also targets of twelve unapproved role-change events (remove ordinary role, grant admin). Disabled former employees produce the eight inactive creation events; they are distinct from the eight retained active accounts. SoD self-approval/confirmation is a workflow bypass and may also imply lack of authorization; no unrelated authorization benchmark is claimed. Normal actors have appropriate separate roles. Administrators have administrative permissions without financial approval/create permissions, so privilege fixtures do not inflate the entitlement SoD population.

Clean controls include recent active logins, a never-used old dormant account, a recently created never-used account, an account exactly at 90 days (not dormant), legitimate distinct-reference partial payments, paid approved invoices and ordinary submitted/draft invoices. The definition of unusual hours applies to invoice/payment creation events; technical/master timestamps are outside that population.

## Local workflow

```powershell
Copy-Item .env.example .env
# Configure DATABASE_URL and matching Docker-only POSTGRES_PASSWORD; start Docker Desktop Linux engine.
docker compose up -d postgres
npm run db:check
npm run db:migrate
npm run db:status
npm run db:generate
npm run db:seed
npm run db:validate-data
npm test
```

Offline db:generate validates and writes only small sample/manifest artifacts; it never writes PostgreSQL. db:seed requires empty source tables and inserts batches atomically. db:validate-data reads every source table in one read-only repeatable-read transaction, compares exact canonical table hashes with regeneration for the configured seed, checks keys, orphan references, chronology and exact exception sets. It is strict fixture QA, not a detector for arbitrary business data.

For repeat seeding, retain the same seed and explicitly delete local fixture rows:

```powershell
$env:AUDITLENS_ALLOW_LOCAL_RESET='YES'
npm run db:reset
Remove-Item Env:AUDITLENS_ALLOW_LOCAL_RESET
npm run db:seed
npm run db:validate-data
```

Reset requires NODE_ENV=development, a loopback database host, database name auditlens and the explicit opt-in. It deletes source rows in reverse FK order in one transaction, with no CASCADE, schema drop, volume deletion or audit data deletion. It does not create tables; migrate first. It does not prove a loopback-forwarded service is safe: use a dedicated local development instance. Do not use it for a shared or production database. Seed/reset coordinate with an advisory lock; do not run a separate source writer during fixture maintenance.

Changing seed: set AUDITLENS_DATA_SEED, reset, seed and validate. Checked-in manifests/examples intentionally represent the default seed; restore that seed with db:generate before running default artifact tests or committing fixture artifacts. Do not keep two seeds' files mixed.

On a disposable database, verify rollback before seeding: migrate, db:rollback, migrate again, then seed. Knex rolls back a batch, which may include both the domain and boundary migrations. The domain down migration drops source tables and their data; only use it on a disposable database. Reset is the preferred repeat-seed workflow.

## Limitations and next use

No actual source UI, immutable log enforcement, rehire history, approval delegation, refunds, FX, service-account population, real holidays or real supporting documents exists. No source-reader grants are provisioned; the existing real-role write-denial acceptance remains pending. Ground truth is not a substitute for independent future algorithms or real-world completeness checks. See [verification](VERIFICATION.md) for runtime blockers; Phase 1 is not declared fully complete. Next planned development phase is Phase 2 — Authentication & RBAC Foundation.
