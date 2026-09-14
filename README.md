# AUDITLENS
### Digital Audit & Internal Control Testing Platform

An educational full-stack project exploring how system data supports traceable internal control testing.

**Development status: Phase 1 dataset tooling implemented; PostgreSQL runtime verification pending. Audit capabilities remain planned.** See [verification](docs/VERIFICATION.md) for actual checks and local infrastructure limitations.

## Problem and planned capabilities
Permissions, transactions and activity logs can hide control weaknesses when reviewed separately. AuditLens will connect repeatable testing with evidence and human-reviewed findings.

Planned modules: user access review; segregation of duties; transaction exceptions; audit trail analysis; risk/control mapping; findings; scope-aware dashboard and reporting.

## Architecture
A Demo Business System will own source writes. AuditLens will read source records through a restricted connection and save its results separately. One PostgreSQL database, auditlens, contains business and audit schemas. A modular Hapi API serves the React UI; an explicit Python CLI will perform analysis. Auditors have independent identities from the business accounts being tested. Schema separation and empty migrations alone do not enforce read-only access; dedicated database roles are a prerequisite for ingestion.

## Stack
React 19, Vite, JavaScript, React Router, Tailwind CSS and DaisyUI; Node.js and Hapi; PostgreSQL 17 and Knex; Python and Pandas with SQL planned for extraction; JWT planned for Phase 2; Docker Compose for local PostgreSQL; Git. Use Node.js 22.12+ and Python 3.11+.

## Repository structure
```text
apps/
  web/src/pages/           React navigation and placeholders
  api/src/
    config/               Central environment configuration
    routes/ handlers/     HTTP contracts
    services/ repositories/ validators/ plugins/ utils/
audit-engine/
  src/audit_engine/
    analyzers/ rules/ repositories/ models/
  tests/
database/
  migrations/ generators/ validation/ seeds/ sample-data/
docs/
  adr/
scripts/
tests/
docker-compose.yml
.env.example
```
Operational and audit submodules will be introduced inside the API when implemented. Reserved folders contain a README or Python package marker.

## Local setup
Install Node.js 22.12+, Python 3.11+, Docker Desktop (running with Linux containers) and Git. From the repository root:

```powershell
Copy-Item .env.example .env
# Edit .env and supply DATABASE_PASSWORD with a local password.
npm install
docker compose up -d postgres
npm run db:check
npm run db:migrate
npm run dev
```

On macOS/Linux replace Copy-Item with cp. Open [web](http://127.0.0.1:5173) and [API health](http://127.0.0.1:3001/health). Stop development servers with Ctrl+C. API and web run on the host; only PostgreSQL uses Docker.

.env is loaded from the repository root regardless of workspace command location. API_PORT defaults to 3001, WEB_PORT to 5173, DATABASE_PORT to 5432. JWT placeholders are unused in this phase; do not invent credentials to run health. DATABASE_USER is the local migration administrator only. Never expose database or API services publicly with this foundation.

For an existing local PostgreSQL server, skip Docker and configure DATABASE_HOST/PORT/NAME/USER/PASSWORD for a dedicated development database. The user needs permission to create schemas and Knex metadata tables. npm run db:check verifies connection, while db:migrate creates boundaries.

```powershell
cd audit-engine
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m audit_engine
.venv\Scripts\python -m unittest discover -s tests
cd ..
```
Use .venv/bin/python on macOS/Linux. If python is unavailable, install Python or invoke your installed interpreter by absolute path.

## Development and verification commands
```powershell
npm test
npm run build
npm run docs:check
npm run dev:api
npm run dev:web
docker compose ps
docker compose logs postgres
docker compose stop
```
npm run db:reset is the guarded, local-only repeat-seed command. The domain db:rollback drops business tables and data; use rollback only against a disposable database. The original boundary rollback still refuses to drop nonempty schemas. Existing PostgreSQL volumes keep their original credentials; changing .env does not rotate database passwords. Do not delete volumes to fix credentials unless you explicitly intend to discard their data.

## Synthetic dataset workflow

After db:migrate, run `npm run db:status`, `npm run db:seed` and `npm run db:validate-data`. Offline generation: `npm run db:generate`. See [dataset and guarded reset instructions](docs/16-SYNTHETIC-DATASET.md), [business process](docs/17-BUSINESS-PROCESS.md), [lineage](docs/18-DATA-LINEAGE.md) and [Phase 1 decisions](docs/adr/ADR-005-phase-1-dataset-conventions.md). Default seed: 20260914. No detector may consume the development ground truth.

## Roadmap
Phase 0 foundation → Phase 1 synthetic dataset → Phase 2 authentication/RBAC → Phase 3 audit framework → Phases 4–7 audit modules → Phase 8 findings → Phase 9 reporting → Phase 10 portfolio polish. Each phase has a definition of done in the [roadmap](docs/13-DEVELOPMENT-ROADMAP.md).

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
A deterministic synthetic source dataset, business migrations, manifests and fixture QA now exist. Authentication, audit rules, finding workflows and reports remain planned. Health indicates process liveness, not database readiness. PostgreSQL migration/seed/rollback execution and source-reader write-denial remain unverified. This is not production-ready or an assurance tool.

"AuditLens is an educational portfolio project designed to demonstrate digital audit, internal control, system analysis, and software engineering concepts using synthetic data. It does not represent or reproduce any proprietary audit methodology."

Licensed under [MIT](LICENSE).

