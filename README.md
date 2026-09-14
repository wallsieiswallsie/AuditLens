# AUDITLENS
### Digital Audit & Internal Control Testing Platform

An educational full-stack project exploring how system data supports traceable internal control testing.

**Development status: Phase 0, Phase 1, stabilization and the Local CLI Audit Framework are verified locally. Frozen snapshots, integrity validation and local runs/results are implemented; policy-driven framework detectors and duplicate-reference, completeness and sequence-gap controls are implemented. Authentication is not implemented. Railway operation remains REPORTED AS WORKING, with dashboard checks outstanding.** See [verification](docs/VERIFICATION.md) and [roadmap](docs/13-DEVELOPMENT-ROADMAP.md).

## Problem and planned capabilities
Permissions, transactions and activity logs can hide control weaknesses when reviewed separately. AuditLens will connect repeatable testing with evidence and human-reviewed findings.

Planned modules: user access review; segregation of duties; transaction exceptions; audit trail analysis; risk/control mapping; findings; scope-aware dashboard and reporting.

## Architecture
A Demo Business System will own source writes. AuditLens reads approved source columns through a restricted connection, freezes normalized snapshots and executes policy-selected Python detectors against immutable context. Runs, provenance and results are local files. One PostgreSQL database, auditlens, contains business and audit schemas; no result tables are created. A modular Hapi API serves the React UI. See [source-reader provisioning](docs/adr/ADR-008-database-privilege-separation.md) and the [framework specification](docs/AUDIT-FRAMEWORK.md).

## Stack
React 19, Vite, JavaScript, React Router, Tailwind CSS and DaisyUI; Node.js and Hapi; PostgreSQL 17, Knex and pg; Python standard-library snapshot framework with Pandas health; JWT planned for Phase 2; Docker Compose for local PostgreSQL; Git. Use Node.js 22.12+ and Python 3.11+.

## Repository structure
```text
apps/
  web/src/pages/           React navigation and placeholders
  api/
    src/
      config/             Central environment configuration
      routes/ handlers/   HTTP contracts
      services/ repositories/ validators/ plugins/ utils/
    database/
      knexfile.js
      migrations/ generators/ validation/ seeds/ sample-data/
audit-engine/
  src/audit_engine/
    analyzers/ rules/ repositories/ models/
  tests/
docs/
  adr/
scripts/
tests/
docker-compose.yml
.env.example
```
Operational and audit submodules will be introduced inside the API when implemented. Reserved folders contain a README or Python package marker.

Database administration tooling is API-owned. Root commands and scripts orchestrate that tooling without changing ownership. Web and API are separate Railway services; Python is a local snapshot/execution CLI. Its narrow extraction transport reuses the installed Node pg driver. See [ADR-007](docs/adr/ADR-007-api-database-and-independent-deployment.md). node_modules, apps/web/dist, Python virtual environments, caches and audit-engine/artifacts are generated and ignored.

## Local setup
Install Node.js 22.12+, Python 3.11+, Docker Desktop (running with Linux containers) and Git. From the repository root:

```powershell
Copy-Item .env.example .env
# Edit .env: set DATABASE_URL and matching Docker-only POSTGRES_PASSWORD.
# Set API_URL=http://localhost:3001.
npm ci
docker compose up -d postgres
npm run db:inspect
npm run db:migrate
npm run dev
```

On macOS/Linux replace Copy-Item with cp. Open [web](http://127.0.0.1:5173) and [API health](http://127.0.0.1:3001/health). Stop development servers with Ctrl+C. API and web run on the host; only PostgreSQL uses Docker.

.env is loaded from the repository root for API/database/Vite commands. PORT defaults to 3001 for API and is strictly validated; WEB_PORT defaults to 5173 for Vite development. API_HOST defaults to 0.0.0.0; the local example uses 127.0.0.1. API_URL is required for Web builds. WEB_ALLOWED_HOST is optional for custom-host local preview only. JWT placeholders are unused. Independent Railway services remain REPORTED AS WORKING; dashboard settings require manual verification.

For an existing local PostgreSQL server, skip Docker and configure DATABASE_URL for a dedicated development database. The user needs permission to create schemas and Knex metadata tables. npm run db:check verifies connection, while db:migrate creates boundaries.

```powershell
cd audit-engine
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m audit_engine
.venv\Scripts\python -m unittest discover -s tests
cd ..
```
Use .venv/bin/python on macOS/Linux. If python is unavailable, install Python or invoke your installed interpreter by absolute path.

Configure the application with one connection string (percent-encode special characters in the password):

```dotenv
DATABASE_URL=postgresql://auditlens_dev:CHANGE_ME@127.0.0.1:5432/auditlens
API_URL=http://localhost:3001
```

Compose uses POSTGRES_DB (default auditlens), POSTGRES_USER (default auditlens_dev), and POSTGRES_PASSWORD only to initialize the PostgreSQL container. Set POSTGRES_PASSWORD to the same local password as the URL; it is not read by application code. If changing the published Compose port, update the port in DATABASE_URL too. A containerized API would use the PostgreSQL service hostname instead of loopback; dataset writes intentionally remain local-only.

See [environment and Railway configuration](docs/DEPLOYMENT.md) and [ADR-006](docs/adr/ADR-006-environment-connection-strings.md). Set API_URL before building the web app; rebuild after changing it. Missing API_URL fails clearly at development startup/build. Database commands require DATABASE_URL; database-free health and offline fixture generation do not.

## Development and verification commands
```powershell
npm test
npm run build
npm run docs:check
npm run dev:api
npm run dev:web
# After building: independent production static server, default port 4173
npm run start -w @auditlens/web
docker compose ps
docker compose logs postgres
docker compose stop
```
npm run db:reset is the guarded, local-only repeat-seed command. The domain db:rollback drops business tables and data; use rollback only against a disposable database. The original boundary rollback still refuses to drop nonempty schemas. Existing PostgreSQL volumes keep their original credentials; changing .env does not rotate database passwords. Do not delete volumes to fix credentials unless you explicitly intend to discard their data.

Database commands are classified in [deployment](docs/DEPLOYMENT.md#database-command-safety). db:inspect is non-mutating; db:status also fails when readiness is incomplete. Both inspect existing metadata without invoking the Knex migrator. Reset and rollback require AUDITLENS_ALLOW_LOCAL_RESET=YES and refuse production. Reader provisioning requires its own explicit opt-in and changes PUBLIC privileges.

Run `npm run test:db` with PostgreSQL 17+ initdb/pg_ctl on PATH (or PG_BIN). This creates and stops its own fresh temporary cluster, ignores DATABASE_URL, and tests migration/fixtures/constraints/permissions. Temporary files are retained for diagnosis. No existing database is used.

## Synthetic dataset workflow

After db:migrate on a confirmed disposable development database, run `npm run db:status`, `npm run db:seed` and `npm run db:validate-data`. Offline generation: `npm run db:generate`. See [dataset and guarded reset instructions](docs/16-SYNTHETIC-DATASET.md), [business process](docs/17-BUSINESS-PROCESS.md), [lineage](docs/18-DATA-LINEAGE.md) and [Phase 1 decisions](docs/adr/ADR-005-phase-1-dataset-conventions.md). Default seed: 20260914. No detector may consume the development ground truth.

## Roadmap
Next milestone: Audit Policy + Detector SDK. The local snapshot framework is implemented; authentication/RBAC remains required before remote audit access. See [roadmap](docs/13-DEVELOPMENT-ROADMAP.md) and [open questions](docs/OPEN-QUESTIONS.md).

## Local audit framework

Prefer AUDIT_SOURCE_DATABASE_URL for a dedicated login authorized to select the existing reader role; extraction falls back to DATABASE_URL but always selects auditlens_source_reader. Neither URL belongs in Web. From repository root:

```powershell
.\audit-engine\.venv\Scripts\python.exe -m audit_engine health
.\audit-engine\.venv\Scripts\python.exe -m audit_engine snapshot
.\audit-engine\.venv\Scripts\python.exe -m audit_engine snapshot inspect <snapshot-id>
.\audit-engine\.venv\Scripts\python.exe -m audit_engine run --snapshot <snapshot-id>
.\audit-engine\.venv\Scripts\python.exe -m audit_engine result inspect <audit-run-id>
```

See [contracts, integrity and retention](docs/AUDIT-FRAMEWORK.md) and [ADR-009](docs/adr/ADR-009-snapshot-based-audit-execution.md). A passed framework.health result only means the snapshot is readable.

## Documentation
- [01 PROJECT OVERVIEW](docs/01-PROJECT-OVERVIEW.md)
- [02 SYSTEM DESIGN](docs/02-SYSTEM-DESIGN.md)
- [03 SYSTEM ARCHITECTURE](docs/03-SYSTEM-ARCHITECTURE.md)
- [04 ERD](docs/04-ERD.md)
- [05 DATA DICTIONARY](docs/05-DATA-DICTIONARY.md)
- [06 RISK CONTROL MATRIX](docs/06-RISK-CONTROL-MATRIX.md)
- [07 AUDIT METHODOLOGY](docs/07-AUDIT-METHODOLOGY.md)
- [08 AUDIT TEST CATALOG](docs/08-AUDIT-TEST-CATALOG.md)
- [09 API DESIGN](docs/09-API-DESIGN.md)
- [10 SECURITY DESIGN](docs/10-SECURITY-DESIGN.md)
- [11 THREAT MODEL](docs/11-THREAT-MODEL.md)
- [12 TESTING STRATEGY](docs/12-TESTING-STRATEGY.md)
- [13 DEVELOPMENT ROADMAP](docs/13-DEVELOPMENT-ROADMAP.md)
- [14 STAKEHOLDER GUIDE](docs/14-STAKEHOLDER-GUIDE.md)
- [15 GLOSSARY](docs/15-GLOSSARY.md)
- [PROJECT OVERVIEW ID](docs/PROJECT-OVERVIEW-ID.md)
- [OPEN QUESTIONS](docs/OPEN-QUESTIONS.md)
- [IMPLEMENTATION PLAN](docs/IMPLEMENTATION-PLAN.md)
- [VERIFICATION](docs/VERIFICATION.md)
- [ADR 001: system boundaries](docs/adr/ADR-001-system-boundaries.md)
- [ADR 002: audit read-only principle](docs/adr/ADR-002-audit-read-only-principle.md)
- [ADR 003: Python audit engine](docs/adr/ADR-003-python-audit-engine.md)
- [ADR 004: database strategy](docs/adr/ADR-004-database-strategy.md)

## Limitations and disclaimer
A deterministic synthetic source dataset, business migrations, manifests and fixture QA exist. Authentication, additional audit rules, finding workflows and reports remain planned. Health indicates process liveness, not database readiness. Disposable local migration/seed/rollback/constraints and source-reader write denial pass; remote provisioning and deployment settings remain unverified. PORT tests and configured Web build now pass. This is not production-ready or an assurance tool.

"AuditLens is an educational portfolio project designed to demonstrate digital audit, internal control, system analysis, and software engineering concepts using synthetic data. It does not represent or reproduce any proprietary audit methodology."

Licensed under [MIT](LICENSE).

## Audit Policy + Detector SDK (0.3.0)

The local framework now supports explicit versioned detector registration and immutable
JSON policies. Default execution remains `framework.health`; select
`audit-engine/policies/examples.json` to run both non-business framework detectors.
See [Detector SDK](docs/DETECTOR-SDK.md) and [ADR-010](docs/adr/ADR-010-detector-sdk-and-audit-policy.md).
Audit Rule Pack v1 now includes `business.duplicate_transaction_reference`, `business.missing_required_field` and `business.sequence_gap`. See [rule semantics and offline example](docs/AUDIT-RULE-PACK.md). No production deployment changes are included.
