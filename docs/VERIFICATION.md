# Verification record

## Phase 1 — 2026-09-14

Implementation is delivered, but Phase 1 is **not fully complete** because PostgreSQL runtime and the pre-existing source-reader write-denial acceptance cannot be verified on this host. No authentication or audit detection engine was added.

| Check | Result |
| --- | --- |
| Docker Compose configuration | Passed with a transient placeholder container password; no credential file written |
| docker info / docker compose up -d postgres | BLOCKED: Docker engine named pipe is unavailable; CLI also reports access denied reading its config |
| npm run db:check | BLOCKED: database credentials were absent; command fails clearly before connecting |
| PostgreSQL business/audit schema existence | NOT VERIFIED live |
| public.knex_migrations / clean migration status | NOT VERIFIED live; db:status command supplied |
| Domain migration | PostgreSQL DDL compiles offline: eleven business tables, PK/FK/unique/check constraints and indexes |
| Migration rollback/reapply | Down SQL compiles in reverse FK order; NOT EXECUTED on PostgreSQL |
| npm run db:generate | Passed: 250 users, 2,000 invoices, 1,840 approvals, 2,400 payments, 12,512 events |
| Fixture QA | Passed: all 14 exact anomaly sets and group memberships; zero orphan FKs or log targets; no unexpected duplicate/SoD/dormancy inflation |
| PostgreSQL seed and db:validate-data | NOT EXECUTED: authenticated isolated PostgreSQL unavailable |
| PostgreSQL reset atomicity / actual constraint rejection | NOT VERIFIED live; guarded transactional implementation and offline checks supplied |
| Source-reader write denial | NOT VERIFIED; roles/ingestion remain unimplemented. Existing Phase 1 acceptance remains open |
| npm run build | Passed: React/Vite production build |
| Python health / unittest | Passed: health returned ok and Pandas 3.0.5; 1/1 unittest |
| Automated generator and existing API tests | Passed: 8/8 Node tests, including six dataset/migration/guard tests and two existing API/config tests |
| Documentation consistency | Passed: compiled DDL inventory parity; 35 Markdown files, 72 relative links and 12 Mermaid diagrams parsed |

All data and references are fictional. The source seed writer is a local development administrator, not a restricted source reader. Schema separation alone is not grant enforcement. No .env or real credentials were created, no unrelated database was modified, and no Git commit was made. The existing Phase 0 files were already untracked when this work began.

## Definition of done

- [x] PostgreSQL Compose configuration validates statically.
- [ ] PostgreSQL connectivity, schemas, metadata and clean migration status verified live.
- [x] Business migrations exist; rollback SQL compiles.
- [x] Normal and anomalous synthetic data generation works deterministically.
- [x] Ground truth, dataset metadata, role policy and small examples exist.
- [x] Offline validation checks full record identities, keys and expected cases.
- [ ] Database migration/seed/reset/validation/rollback execution verified live.
- [ ] Actual source-reader INSERT/UPDATE/DELETE/DDL denial verified.
- [x] Automated generator tests exist and pass.
- [x] Existing API tests, web build and Python health/tests pass.
- [x] ERD and dictionary are generated from migration SQL.
- [x] Dataset, business process and lineage documentation exist.

## Remaining database verification

Use a dedicated disposable local PostgreSQL instance. Start Docker Desktop's Linux engine; copy .env.example to .env and configure DATABASE_URL and matching Docker-only POSTGRES_PASSWORD. If 5432 is occupied, change the Compose published port and the matching port in DATABASE_URL. Do not alter an unrelated server or delete its data.

```powershell
docker compose up -d postgres
npm run db:check
npm run db:migrate
npm run db:status
# Disposable database only: this drops domain tables and possibly boundary schemas.
npm run db:rollback
npm run db:migrate
npm run db:status
npm run db:seed
npm run db:validate-data
$env:AUDITLENS_ALLOW_LOCAL_RESET='YES'
npm run db:reset
Remove-Item Env:AUDITLENS_ALLOW_LOCAL_RESET
npm run db:seed
npm run db:validate-data
```

Check actual NOT NULL, FK, duplicate master-key, invalid status, nonpositive money and incomplete-confirmation constraint failures inside rollback-only transactions. Confirm audit remains untouched. Provision the future SELECT-only reader separately and prove real writes/DDL fail; mock tests cannot satisfy that acceptance. Record PostgreSQL version and results here before marking Phase 1 complete.

## Phase 0 historical verification

The foundation was previously verified on Windows with Node.js 22.14.0 and bundled Python 3.12 in audit-engine/.venv. npm install, API health/error and invalid-port tests, React/Vite build, API/frontend startup, live health/frontend HTTP requests, Python health/unittest, and relative-link/Mermaid parsing passed. Browser interaction was not automated. PostgreSQL was blocked then by absent credentials and an unavailable Docker Linux engine. Those infrastructure checks were not retrospectively marked passed.

## Environment refactor — 2026-09-14

- Node tests: 13/13 passed, including API health/error boundaries, DATABASE_URL validation, exact Knex input, missing-URL failures for all database command entry points, local dataset guard, URL normalization, and production bundle secrecy.
- Production web build passed with API_URL supplied. Both the actual app and an explicit import.meta.env probe were built with synthetic database/JWT/unrelated-variable sentinels; only the public API endpoint was present.
- Python unittest: 1/1 passed.
- Offline db:generate passed; generated fixture files have no Git content changes, anomaly counts unchanged, zero orphans.
- docs:check passed: schema parity, 37 Markdown files, 74 relative links, 12 Mermaid diagrams.
- docker compose config --quiet passed using a transient placeholder POSTGRES_PASSWORD. Docker emitted a config-file access warning; docker info failed because the engine pipe is unavailable.
- Live connectivity, migration, rollback, seed, reset and database validation remain unverified: no configured DATABASE_URL or running Docker engine. Missing-configuration command tests do not substitute for live PostgreSQL verification.
- Final source/Markdown search found no legacy database or frontend endpoint variable names. Dependencies, Git history, virtual environments and generated bundles were excluded from the source search; bundles were checked separately above.
- Corrected a pre-existing stale migration filename in the offline SQL helper so dataset and documentation tests can execute. Migration contents, business rules and phase scope are unchanged.
