# Verification record

## Stabilization acceptance — 2026-09-14 (current)

This section is the current factual record; all older snapshots below are historical. **Phase 0: VERIFIED locally. Phase 1: VERIFIED on disposable PostgreSQL. Stabilization: COMPLETE for repository/local acceptance. Ready for the next local CLI Audit Framework milestone, after its documented design decisions; framework implementation has not begun.** Railway dashboard/runtime evidence remains NOT VERIFIABLE, independently of the local pass.

Environment: Windows, Node.js 22.14.0, Python 3.12.14 / Pandas 3.0.5, PostgreSQL 17.5 (x86_64-windows). No existing DATABASE_URL or .env was used. The working tree already contained review/path/documentation edits at the start; these were preserved. No Git commit, Railway deployment, existing-database migration or production privilege change was made.

| Command/check | Result | What actually ran |
| --- | --- | --- |
| npm test | PASSED — 17/17 | API/config, fixture parity/QA, local guards, real HTTP serving and app/env-probe bundle secrecy; rerun after database changes; final root-serving adjustment also passed tests/web.test.js (2/2) |
| API health/404/500 | PASSED | Hapi injection plus loopback health HTTP; sanitized internal error, no foreign-Origin CORS header |
| API payload/shutdown | PASSED | Test-only payload route rejects >1 MiB with 413; started server stops cleanly; no application endpoints added |
| PORT cases | PASSED | 3001/8080 accepted; 0/65536/abc/3001.5 rejected; default 3001 |
| npm run build | PASSED | API_URL=http://localhost:3001, no WEB_ALLOWED_HOST needed; Vite production assets emitted |
| Production dist HTTP | PASSED | Actual built index/assets entrypoint served at /, /audit-tests and /findings through apps/web/server.js |
| Web static server tests | PASSED | Root, nested navigation, HEAD, JS MIME, missing asset 404, dot/traversal paths, malformed encoding and method rejection |
| Secret boundary | PASSED | Actual application and explicit import.meta.env probe exclude database/JWT/unrelated prefixed sentinels while retaining public API_URL |
| npm run docs:check | PASSED | Final rerun: generated DDL parity, 41 Markdown files, 121 relative links and 13 Mermaid diagrams |
| audit-engine/.venv/Scripts/python.exe -m unittest discover -s audit-engine/tests | PASSED — 1/1 | Existing engine health test |
| audit-engine/.venv/Scripts/python.exe -m audit_engine | PASSED | status ok; Pandas 3.0.5 |
| npm run test:db | PASSED | Full private-cluster PostgreSQL acceptance; completed 2026-09-14T13:42:37.378Z |
| db:check / db:inspect | PASSED inside acceptance | Real SELECT connectivity and read-only empty-database catalogs; repeated inspection creates no schemas/metadata |
| db:status / db:validate-data | PASSED inside acceptance | Existing metadata/table readiness; consistent full fixture hash and anomaly QA |
| Git whitespace | PASSED | git diff --check passed after all edits |
| Existing Railway operation | REPORTED AS WORKING | Developer report retained; no automated remote proof |
| Railway commands, watch isolation, HTTPS, restart policy, remote grants | NOT VERIFIABLE | No dashboard/remote credentials or service URLs inspected |

Initial acceptance attempts are retained honestly: sandbox initdb FAILED to create its Windows restricted process token. A permitted broader-process run then exposed an admin URL construction defect in the new runner; a later run caught revalidation of Knex-normalized connection settings in reset. Both implementation defects were corrected. The final run above passed; each started cluster was stopped. Docker remains unavailable (missing engine pipe), and was unnecessary for the native PostgreSQL acceptance.

### Disposable target and workflow evidence

The runner accepts no target URL and ignores DATABASE_URL. It initializes a fresh temporary cluster with SCRAM credentials, binds loopback on a selected unused port, creates database auditlens, then executes the API-owned migrations and fixtures. It stops the server in finally. Test files remain in the OS temporary directory for diagnosis; the password file is deleted immediately after initdb. A stopped test cluster is not a provisioned Railway reader.

Verified order: empty inspection twice → connectivity/inspection commands → both migrations → eleven business tables and empty audit schema → seed/validate → rollback last batch → schemas absent → reapply → seed/validate with identical hashes → guarded reset → empty source tables → reseed/validate → constraints → reader provision twice → real permission tests → unchanged source hashes and zero audit tables.

| Table | Generated / manifest / live rows |
| --- | --- |
| employees | 250 / 250 / 250 |
| users | 250 / 250 / 250 |
| roles | 8 / 8 / 8 |
| permissions | 17 / 17 / 17 |
| user_roles | 250 / 250 / 250 |
| role_permissions | 27 / 27 / 27 |
| vendors | 100 / 100 / 100 |
| invoices | 2000 / 2000 / 2000 |
| invoice_approvals | 1840 / 1840 / 1840 |
| payments | 2400 / 2400 / 2400 |
| audit_logs | 12512 / 12512 / 12512 |

Default seed 20260914, fixture version 1.0.0. Logical SHA-256: ce8a804cea5a71bba995530d06dab875433d61faf149ac2bf9ab298284a906f2. Every live per-table hash matched the unchanged canonical [dataset manifest](../apps/api/database/sample-data/dataset-manifest.json) across reloads. Ground truth/policy/manifest matched generation; all 14 exact anomaly sets and groups passed; zero orphans. Neither generators nor benchmark semantics changed. This is fixture QA, not audit detection.

### PostgreSQL constraint and permission evidence

Constraints rejected inside rolled-back transactions: foreign key 23503; invalid status, nonpositive amount, incomplete payment confirmation and invalid employment dates 23514; duplicate employee number 23505; null vendor name 23502. Source data remained intact.

Reader provisioned: auditlens_source_reader, NOLOGIN, non-owner and no parent memberships. A separately authenticated non-superuser auditlens_acceptance_login selected the role; both session_user and current_user were asserted. Ordinary read-write transactions were used for permission attempts so a read-only transaction setting could not mask excess privileges.

| Operation | Actual PostgreSQL result |
| --- | --- |
| SELECT | PASSED on all eleven source tables, including users/invoices/payments |
| INSERT / UPDATE / DELETE / TRUNCATE | PASSED: denied with 42501 |
| CREATE TABLE in business/public/audit | PASSED: denied with 42501 |
| CREATE SCHEMA / CREATE TEMP TABLE | PASSED: denied with 42501 |
| ALTER / DROP source table | PASSED: denied with 42501 |
| Read migration metadata | PASSED: denied with 42501 |
| Read a new business table | PASSED: denied with 42501; no blanket future SELECT |
| Read/update/drop audit test table | PASSED: denied with 42501 |
| Execute new business SECURITY DEFINER function | PASSED: denied with 42501 |
| Integrity afterward | PASSED: unchanged source hashes, no audit tables, migrations ready |

### Definition of Done

| Requirement | Status | Evidence |
| --- | --- | --- |
| PORT contract consistent | PASS | Example/config/tests use PORT; legacy occurrences only historical docs |
| API config tests | PASS | npm test |
| Web environment documented/tested | PASS | Optional preview host and URL tests; DEPLOYMENT |
| API_URL canonical | PASS | Single explicit public mapping |
| DATABASE_URL canonical main connection | PASS | Knex URL contract; no new reader application variable |
| Server secrets excluded from Web | PASS | App and env-probe sentinel builds |
| Production Web build | PASS | npm run build |
| Nested Web routes supportable | PASS | Actual built dist HTTP and static tests |
| Railway deployment contract documented | PASS | DEPLOYMENT dashboard requirements; remote execution unverified |
| Safe read-only DB inspection | PASS | Empty live database unchanged; read-only transaction |
| Database commands classified | PASS | DEPLOYMENT command table |
| Destructive commands guarded | PASS | Opt-in, production refusal, destination guards and tests |
| Disposable migration acceptance | PASS | test:db |
| Fixture seed/validation acceptance | PASS | test:db |
| Deterministic regeneration | PASS | Same live hashes after rollback/reset reload |
| Runtime representative constraints | PASS | PostgreSQL error codes above |
| Reader identity exists/reproducibly provisioned | PASS | Provision twice in fresh cluster; explicit admin tooling |
| Reader SELECT succeeds | PASS | All eleven tables |
| Reader INSERT fails | PASS | 42501 |
| Reader UPDATE fails | PASS | 42501 |
| Reader DELETE fails | PASS | 42501 |
| Reader DDL fails | PASS | CREATE/ALTER/DROP/schema/TEMP 42501 |
| Existing API tests | PASS | npm test |
| Existing dataset tests | PASS | npm test |
| Existing Python tests | PASS | 1/1 |
| Documentation synchronized | PASS | Current status/config/grants/commands and generated schema descriptions |
| VERIFICATION factual results | PASS | This dated record preserves earlier failures and reported facts |
| ROADMAP actual state | PASS | Local verified; remote unverified; no audit framework implemented |

Remaining remote/manual checks do not substitute for any local result. Framework prerequisites still require explicit extraction/snapshot, local operator provenance, policy versioning, evidence retention and result-writer decisions; see [open questions](OPEN-QUESTIONS.md).

## Historical pre-stabilization repository review — 2026-09-14

This historical review superseded earlier snapshots at the time; the stabilization record above now takes precedence. Historical results below are retained as history, not represented as current passes. PostgreSQL connectivity, successful migrations and separate Railway Web/API services are **REPORTED AS WORKING** by the developer. No DATABASE_URL or local .env is available in this review environment; remote runtime was not inspected.

| Check | Current result |
| --- | --- |
| Initial npm test | Failed: dataset imports and database command paths referenced the removed root database directory; port-contract and missing WEB_ALLOWED_HOST failures also reproduced |
| Limited path repairs | Root migration/rollback commands, five script imports and two test files now point into apps/api/database; workspace-local API migration path was already correct |
| npm test after path repairs, WEB_ALLOWED_HOST=localhost supplied | 12/13 passed; API_PORT test fails because implementation reads PORT. Application behavior and that test were not altered |
| Generator and fixture QA | Six dataset tests passed: deterministic equality, alternate seed, exact counts/14 anomaly sets, mutation rejection, local-write guards and offline DDL/rollback compilation |
| Artifact parity | Ground truth, policy and manifest match regenerated fixture; all four three-row sample files checked independently and match |
| Web build | Passed with API_URL=http://localhost:3001 and WEB_ALLOWED_HOST=localhost; missing API_URL fails clearly; API_URL alone does not satisfy required host configuration |
| Browser secret boundary | App and explicit environment probe pass with synthetic database/JWT/unrelated-variable sentinels absent from compiled output |
| API health/error tests | Health, 404 and sanitized 500 contract passed; live loopback HTTP health 200 also passed, with no CORS allow-origin header for a foreign Origin |
| Web development smoke | Vite served nested /findings as HTTP 200 with the application entrypoint; no browser interaction automation |
| Python | Existing virtual environment: unittest 1/1 passed and CLI returned ok with Pandas 3.0.5 |
| db:check and db:validate-data | Attempted; both stop on missing DATABASE_URL before connecting. Not live verification |
| PostgreSQL schema/seed/rollback/constraint/reader denial | Not independently verified; no database writes, migrations or resets were performed |
| Documentation | Compiled ERD/dictionary parity; 39 Markdown files, 104 relative links and 13 Mermaid diagrams validated after reconciliation |
| Git | Clean initial working tree; only documented review changes and stale path repairs; no commit or deployment |

The current API default is API_HOST=0.0.0.0 and PORT=3001, while .env.example still supplies API_PORT and omits WEB_ALLOWED_HOST. Explicit loopback and required Web variables are documented in [deployment](DEPLOYMENT.md). These remaining configuration changes belong to the [next-phase plan](PROJECT-REVIEW.md), not this limited review.

db:status is not guaranteed read-only on an uninitialized database: installed Knex migrate.list() calls ensureTable for migration metadata. It was not run against an unknown destination. A future read-only status command should query catalogs without creating metadata.

## Historical Phase 1 — 2026-09-14

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

## Historical definition of done

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

## Historical environment refactor — 2026-09-14

- Node tests: 13/13 passed, including API health/error boundaries, DATABASE_URL validation, exact Knex input, missing-URL failures for all database command entry points, local dataset guard, URL normalization, and production bundle secrecy.
- Production web build passed with API_URL supplied. Both the actual app and an explicit import.meta.env probe were built with synthetic database/JWT/unrelated-variable sentinels; only the public API endpoint was present.
- Python unittest: 1/1 passed.
- Offline db:generate passed; generated fixture files have no Git content changes, anomaly counts unchanged, zero orphans.
- docs:check passed: schema parity, 37 Markdown files, 74 relative links, 12 Mermaid diagrams.
- docker compose config --quiet passed using a transient placeholder POSTGRES_PASSWORD. Docker emitted a config-file access warning; docker info failed because the engine pipe is unavailable.
- Live connectivity, migration, rollback, seed, reset and database validation remain unverified: no configured DATABASE_URL or running Docker engine. Missing-configuration command tests do not substitute for live PostgreSQL verification.
- Final source/Markdown search found no legacy database or frontend endpoint variable names. Dependencies, Git history, virtual environments and generated bundles were excluded from the source search; bundles were checked separately above.
- Corrected a pre-existing stale migration filename in the offline SQL helper so dataset and documentation tests can execute. Migration contents, business rules and phase scope are unchanged.
