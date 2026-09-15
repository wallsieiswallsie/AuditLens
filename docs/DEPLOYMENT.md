# Environment and Railway deployment

API and Web remain separate services. Database administration tooling is owned by apps/api/database; Python is a local snapshot/execution CLI, not a deployed service. The running Railway services are **REPORTED AS WORKING** by the developer. Remote settings, domains, logs and deployment isolation have not been independently inspected. No Railway dashboard configuration is stored in this repository.

For the current Rule Pack integration, use the [production runbook](PRODUCTION-RUNBOOK.md).
Root aliases `npm run start:api` and `npm run start:web` delegate to the service
workspaces. API migrations now use `apps/api/src/migrate.js`, the locally installed
Knex library, module-relative migration paths and sanitized errors. Actual npm start
commands are checked from both root and service working directories. Build context
remains repository root because the shared lockfile lives there; a working service
command does not prove an isolated `/apps/api` Railway install strategy.
Production API configuration requires DATABASE_URL even for process startup;
development health remains database-free. Railway checks for this phase are NOT RUN.

## Canonical configuration

| Variable | Consumer and behavior |
| --- | --- |
| NODE_ENV | development locally; production in each deployed service |
| PORT | API runtime port, decimal integer 1–65535, default 3001. Web production server independently uses Railway PORT, default 4173 locally. Railway provides a separate PORT to each service |
| API_HOST | API bind address; default 0.0.0.0 for platform access; example sets 127.0.0.1 for local development |
| API_URL | Required public HTTP(S) API endpoint at Web build/dev time; trailing slashes normalized; no credentials/query/fragment; rebuild after changing it |
| DATABASE_URL | Canonical API/migration/tooling PostgreSQL connection; never set on Web |
| AUDIT_SOURCE_DATABASE_URL | Optional dedicated local extraction login; preferred over DATABASE_URL, always selects auditlens_source_reader; never set on Web. No URL query overrides. Process environment or root .env |
| AUDIT_OPERATOR | Optional explicit local operator label from process environment; --operator overrides; default local. No automatic OS identity collection |
| AUDITLENS_TEST_PYTHON | Optional interpreter path for disposable acceptance; defaults to engine venv then python on PATH |
| WEB_PORT | Vite development port, default 5173; does not control production serving |
| WEB_ALLOWED_HOST | Optional hostname for custom-host local Vite preview only; omitted for builds and standard localhost preview; no scheme, credentials or port |
| AUDITLENS_DATA_SEED | Fixture generation/QA seed, default 20260914 |
| AUDITLENS_ALLOW_LOCAL_RESET | YES explicitly permits local reset/rollback after destination verification; production remains forbidden |
| AUDITLENS_ALLOW_READER_PROVISION | YES permits explicit local reader provisioning; changes PUBLIC grants in the dedicated database |
| PG_BIN | Optional PostgreSQL 17+ binary directory for the self-contained acceptance runner; otherwise binaries use PATH |
| POSTGRES_PASSWORD | Compose initialization only, match the password encoded in the local DATABASE_URL |

JWT_ACCESS_SECRET and JWT_REFRESH_SECRET are unused future placeholders, server-side only. Vite sets envPrefix to an empty array and explicitly defines only API_URL; full environment loading in the build process is not browser exposure. Automated app/probe bundles verify sentinel secrets stay absent.

## REQUIRED RAILWAY DASHBOARD SETTINGS

Use repository root `/` as the build context for **both** services to retain the shared root workspace lockfile. Service source ownership remains apps/api and apps/web. Do not set isolated subdirectory roots without a separately verified lockfile/install strategy. These are reproducible repository contracts and required dashboard values, not assertions about the currently running services.

| Setting | @auditlens/api | @auditlens/web |
| --- | --- | --- |
| Root directory | / | / |
| Install/build command | npm ci | npm ci && npm run build -w @auditlens/web |
| Start command | npm run start -w @auditlens/api | npm run start -w @auditlens/web |
| Compiled output | None; Node source | apps/web/dist |
| Runtime | Node.js 22.12+ | Node.js 22.12+ |
| Variables | NODE_ENV=production, API_HOST=0.0.0.0, Railway PORT, DATABASE_URL referencing PostgreSQL | NODE_ENV=production, Railway PORT; API_URL supplied during build |
| Health check | /health | /index.html |
| Watch paths | /apps/api/**, /package.json, /package-lock.json | /apps/web/**, /package.json, /package-lock.json |

API start runs migrate:latest before Hapi. A migration failure exits startup; Railway health must not admit that deployment. Restarts rerun only pending migrations using Knex metadata/locking. No rollback, reset or seed runs at startup. The current API therefore uses migration-capable credentials; separating migration execution from a future database-backed runtime identity is required before those endpoints. GET /health is liveness, not database readiness.

Web start uses the small Node static server in apps/web/server.js, independently of Hapi. It serves only dist, supports GET/HEAD, returns index.html for extensionless browser navigation (Accept: text/html), and keeps missing assets at 404. HTML uses no-cache; static assets use a one-hour cache. It binds 0.0.0.0 and handles shutdown. Railway supplies HTTPS termination. Vite preview remains a local preview tool, [not a production server](https://vite.dev/guide/static-deploy). If Railway already uses a working independent static server, retain it only after verifying equivalent dist serving and SPA behavior; the actual remote mechanism remains unverified.

Watch paths are relative to the repository root. Shared package manifests/lockfile legitimately trigger both services. Root docs, scripts, tests and audit-engine changes need not trigger either current service; revisit if a build begins consuming them. Verify this behavior in deployment history; see [Railway monorepo guidance](https://docs.railway.com/deployments/monorepo).

Do not give Web PostgreSQL/admin/JWT credentials or deploy Python. Future cross-origin browser data calls require an exact-origin API CORS policy before integration; today CORS is absent and pages remain placeholders.

## Database command safety

| Command | Classification | Behavior |
| --- | --- | --- |
| npm run db:check | READ-ONLY | SELECT 1 connectivity only |
| npm run db:inspect | READ-ONLY | Consistent read-only catalog inspection plus existing migration-name SELECT; prints readiness, exits successfully when inspection succeeds even if not ready |
| npm run db:status | READ-ONLY | Same report; nonzero if not ready |
| npm run db:validate-data | READ-ONLY | Repeatable-read fixture counts, hashes, keys and exact ground-truth QA |
| npm run db:generate | LOCAL FILE WRITE | Regenerates small manifests/examples, no database access |
| python -m audit_engine snapshot | SOURCE READ / LOCAL FILE WRITE | Fixed reader role, consistent explicit SELECT; normalized JSONL/manifest under ignored artifacts |
| python -m audit_engine run --snapshot ID | LOCAL FILE READ/WRITE | Validate frozen snapshot, execute health, publish run/provenance/result; no database access |
| npm run db:migrate | MUTATING | Applies pending migrations; administrator responsibility |
| npm run db:seed | MUTATING / LOCAL-ONLY | Development, loopback, database auditlens, password, no URL overrides; requires empty source tables |
| npm run db:reset | DESTRUCTIVE / LOCAL-ONLY | Same destination restrictions plus AUDITLENS_ALLOW_LOCAL_RESET=YES; deletes source rows transactionally |
| npm run db:rollback | DESTRUCTIVE / LOCAL-ONLY | Same restrictions and opt-in; drops the last migration batch, including business data |
| npm run db:provision-reader | PRIVILEGE MUTATION / LOCAL-ONLY | Same destination restrictions plus AUDITLENS_ALLOW_READER_PROVISION=YES; provision after migrations as owner/role administrator |
| npm run test:db | DISPOSABLE INFRASTRUCTURE ONLY | Creates its own new cluster, random port/password; ignores DATABASE_URL; runs full acceptance and stops the cluster |

A loopback URL may be a tunnel. The operator must verify disposability before seed/reset/rollback/provision; the guards are not proof of destination ownership. Never bypass them with raw Knex rollback against production. No deliberate production override is provided. See [reader provisioning](../apps/api/database/security/README.md).

Inspection checks connection/database/version, business/audit schemas, each of eleven business tables, both Knex metadata tables, expected migration filenames, applied names, pending names and unexpected names. It never calls the Knex migrator, creates metadata or writes source data. Migration names are read only if metadata already exists; the caller needs SELECT on that metadata. Readiness does not prove migration contents/checksums, fixture validity or database security. Connection errors omit URLs/passwords.

## Local use and manual Railway checks
Local extraction requires the editable engine package, Node on PATH and npm ci. Provision a dedicated reader login separately under the existing reader permission role; the extractor never creates credentials or changes grants. Inspect/run/health need no database connection. Artifact storage is manual local retention; no result schema/migration is added. See [CLI setup and limits](AUDIT-FRAMEWORK.md).


Copy .env.example, set local DATABASE_URL and matching Compose-only POSTGRES_PASSWORD, then npm ci. Run db:inspect before migration. Compose binds PostgreSQL to loopback and retains original credentials in its named volume; changing .env does not rotate passwords. Do not delete an existing volume to fix credentials.

Only remote manual checks remain: confirm service roots/commands/runtime versions/variables above, database reference and migration logs, health-check configuration, public HTTPS/API health, direct browser reload of /audit-tests, effective restart policy, and actual per-service watch isolation in deployment history. No browser business call exists yet; do not interpret static page success as authenticated API integration. Record results in [verification](VERIFICATION.md).
