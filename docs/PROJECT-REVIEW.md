> Historical pre-stabilization review. Configuration, serving, diagnostics and acceptance work subsequently changed the repository. [VERIFICATION](VERIFICATION.md) and [ROADMAP](13-DEVELOPMENT-ROADMAP.md) are the current evidence and phase authority. PORT/API_PORT and required-host references below preserve the original findings, not current instructions.

# A. Executive Summary

AuditLens is an educational Digital Audit platform foundation with a substantial synthetic business dataset, not yet an operational audit application. Its strongest implementation is eleven source tables plus deterministic generation and fixture QA for fourteen anomaly categories. Web is a navigation shell, Hapi exposes public health, and Python exposes dependency health.

PostgreSQL connectivity, successful migrations and independent Railway Web/API services are **REPORTED AS WORKING** by the developer. This workspace has no DATABASE_URL or local .env, so those runtime facts were not independently verified.

After repairing stale paths, all six dataset tests pass, the configured Web build passes, and Python health/tests pass. The full Node suite is **12/13**, with a remaining PORT/API_PORT contract failure. Phase 0 and Phase 1 are PARTIAL under current acceptance; later capability phases are NOT STARTED in code.

**NEXT PHASE: Configuration and deployment stabilization with Phase 1 runtime acceptance.** This review changes documentation and broken paths only. No next-phase feature, database write, deployment or commit was performed.

# B. Project Understanding

The business source is a fictional invoice-to-payment process: employees own accounts; roles grant permissions; vendors issue invoices; separate actors create, approve and pay; source events preserve activity. The generator implements that teaching population. There is no interactive source business application.

AuditLens is intended to independently test those records, associate risks with controls and procedures, preserve evidence and support human-reviewed findings and recommendations. Exceptions are not findings or proof of fraud. Generic project-defined controls are used; no proprietary audit-firm methodology is reproduced.

Auditors execute/review procedures, managers review conclusions, business owners explain and remediate exceptions, and developers maintain reproducibility. The Python component will analyze validated source extracts. Its future results belong to the audit domain, never to business records.

Today business-process understanding, structural integrity, anomaly design, population definitions and benchmark discipline are demonstrated. Independent audit execution, evidence retention and reviewed findings remain future work.

# C. Actual Repository Structure

Inventory covered all 95 initially tracked files, including root/workspace manifests and lock metadata, all project Markdown and six existing ADRs, database source, fixture metadata/examples, Web/API/Python source and tests. Dependencies/generated directories were classified rather than treated as authored architecture.

```text
AuditLens/
  apps/
    api/                              SOURCE
      package.json                    package/start/migrate configuration
      src/
        index.js server.js            startup and Hapi construction
        config/env.js
        routes/health.js handlers/health.js plugins/errors.js
        services/ repositories/ validators/ utils/  README placeholders
      database/                       SOURCE + backend TOOLING
        knexfile.js
        migrations/                   two migrations
        generators/                   seven modules
        seeds/                        workflow.js + README
        validation/                   validate.js
        sample-data/                  fixture manifest, truth, policy, README
          examples/                   four three-row JSON samples
      node_modules/                   DEPENDENCY
    web/                              SOURCE
      package.json index.html vite.config.js
      src/                            App, main, styles, config/api, PlaceholderPage
      node_modules/                   DEPENDENCY
      dist/                           GENERATED
  audit-engine/                       SOURCE, independent Python package
    pyproject.toml requirements.txt README.md
    src/audit_engine/                 health CLI + four reserved packages
    tests/test_health.py              TESTING
    .venv/                            DEPENDENCY
    **/__pycache__/                   GENERATED
  docs/                               DOCUMENTATION
    01–18 topic documents, supporting documents, adr/
  scripts/                            TOOLING, six repository-level scripts
  tests/                              TESTING, three Node test files
  node_modules/                       DEPENDENCY
  package.json package-lock.json      workspace orchestration/dependency lock
  .env.example .gitignore docker-compose.yml README.md LICENSE
```

Root package.json uses apps/* workspaces. dev delegates to both workspaces; build delegates only to Web; test and documentation checks are repository-level. Database entry commands invoke API-owned tooling. Root and API both declare Knex/pg/dotenv; this does not give Web database ownership. No CI, Dockerfile or Railway configuration file is checked in.

# D. Actual Architecture

React 19 + React Router uses Vite, Tailwind and DaisyUI. Node/Hapi implements only health and safe internal HTTP errors. Knex/pg handle migrations and fixture tooling. The lockfile resolves Vite 8.3.0 and Knex 3.3.0; package declarations and the root lockfile were inspected.

Database source belongs to apps/api/database. The root migration commands were broken after the move; they now address apps/api/database/knexfile.js. The API workspace's relative database/knexfile.js was already correct.

Hapi does not currently query PostgreSQL. API workspace start runs migrate first, then src/index.js. Root dev:api runs the watch server without migration. Python is not invoked by Hapi and contains no database extraction.

Schema separation expresses ownership but does not enforce it. No reader/writer role provisioning exists. Source log references are polymorphic IDs; no cross-schema audit-to-source foreign keys exist. Audit migrations are absent except creation of the empty audit schema.

# E. Railway Deployment Architecture

apps/web → @auditlens/web → HTTPS/API_URL → @auditlens/api ← apps/api; API tooling/startup → DATABASE_URL → PostgreSQL.

These are separate services by requirement and developer report. Web must not be served by Hapi merely to consolidate deployments. Python is not an implied Railway service.

Actual Railway build/start commands, watch paths, health settings and remote hosting were not available in repository evidence. Independent package directories alone do not prove isolation. Verify service-specific watch paths and genuinely shared root inputs; shared lockfile changes can legitimately affect both builds. See [Railway's monorepo guidance](https://docs.railway.com/deployments/monorepo).

The Web package has a preview script but no production start script. Its shell $PORT expansion is not portable to Windows npm's default cmd shell. Vite states that [preview is not a production server](https://vite.dev/guide/static-deploy). The actual Railway start method is unknown, so this is a deployment acceptance gap, not a claim about the running service.

# F. API State

| Method | Path | Purpose | Implementation | Database-backed | Authenticated | Tested |
| --- | --- | --- | --- | --- | --- | --- |
| GET | /health | Process liveness | IMPLEMENTED; returns status=ok and service=auditlens-api | No | No; intentionally public | Injection and live loopback HTTP 200 verified |

This is the only registered application endpoint. The temporary /test-failure route exists only inside a test. Unknown routes return 404 and internal handler failures return sanitized 500. Payload maximum is 1 MiB. Service/repository/validator/utils folders contain no domain implementation. Login, runs, findings and every other API-design contract are PLANNED.

# G. Database State

Location: apps/api/database. Migration order:

1. 20260914034933_create_boundaries.js creates business and audit.
2. 20260914035028_create_business_domain.js creates the eleven business tables.

Compiled SQL contains **11 primary keys, 13 foreign keys, 5 unique constraints, 40 checks and 20 explicit secondary indexes**. Knex metadata belongs to public.knex_migrations and its lock table.

Implemented source tables: employees, users, roles, permissions, user_roles, role_permissions, vendors, invoices, invoice_approvals, payments and audit_logs. Audit-domain tables remain PLANNED.

Foreign keys link users to employees, assignments to users/roles, grants to roles/permissions, invoices to vendors/creators, decisions to invoices/actors, payments to invoices/creators/confirmers, and logs to actors. ON DELETE RESTRICT applies. Five master identifiers are unique: employee_number, email, role code, permission code and vendor code. Junctions have composite primary keys.

Checks cover nonempty text, normalized email, human account ownership, supported states/actions, employment dates, positive IDR numeric(18,2) amounts, timestamp chronology and complete payment confirmation. Invoice/payment references deliberately allow duplicate business keys. Writers supply UUIDs and timestamps; no automatic timestamp triggers/defaults or immutable-log enforcement exist. Indexes support foreign keys, account status/activity, transaction grouping and event chronology. The generated dictionary and ERD match compiled DDL.

Rollback drops domain tables in reverse dependency order; the boundary rollback refuses nonempty schemas. This is source code/offline SQL verification, not live rollback testing. Connectivity and migration execution are REPORTED AS WORKING. Seed/reset/constraint rejection and live table contents remain independently unverified.

Root commands remain entry points; the implementation is API-owned. The root Knex CLI now uses the real location. db:status is not strictly read-only on a fresh database: installed migrate.list() invokes ensureTable for migration metadata.

# H. Synthetic Dataset State

Generator: seven modules under apps/api/database/generators. Seed defaults to **20260914**, accepts unsigned 32-bit integers, uses seeded arithmetic and SHA-256-derived UUIDs, and freezes dataset version **1.0.0**, policy **fixture-policy-1**, as-of **2026-09-14T10:00:00.000Z**. No runtime clock/randomUUID/Math.random dependency was found.

| Table | Generated rows |
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

These are verified generated counts, not claimed live PostgreSQL counts.

| Fixture | Status | Exact expected unit/count |
| --- | --- | --- |
| AC-001 | IMPLEMENTED | 8 active accounts linked to inactive employees |
| AC-002 | IMPLEMENTED | 12 dormant accounts |
| AC-003 | IMPLEMENTED | 6 accounts outside fixture allowed-role baseline |
| SOD-001 | IMPLEMENTED | 10 observed self-approval invoices |
| SOD-002 | IMPLEMENTED | 8 observed self-confirmation payments |
| TX-001 | IMPLEMENTED | 10 duplicate groups / 20 invoice members |
| TX-002 | IMPLEMENTED | 12 duplicate groups / 24 payment members |
| TX-003 | IMPLEMENTED | 8 cumulatively overpaid invoices |
| TX-004 | IMPLEMENTED | 10 invoices without required approval |
| TX-005 | IMPLEMENTED, restricted scope | 8 creation events after employment end; historical account disablement is unavailable |
| TX-006 | IMPLEMENTED, restricted scope | 20 out-of-hours creation events |
| LOG-001 | IMPLEMENTED | 10 material post-approval changes |
| LOG-002 | IMPLEMENTED | 8 payment status overrides |
| LOG-003 | IMPLEMENTED | 12 unapproved role-change events |

Fixture SOD-001/002 are observed events, mapping to planned procedures SOD-003/004; catalog SOD-001/002 remain entitlement tests. Access fixture IDs AC map to UA procedure IDs. No entitlement SoD-positive population is claimed. TX-007 has clean supporting-reference negatives; LOG-004 has no injected deletion fixture.

Ground truth at apps/api/database/sample-data/ground-truth.json contains version/seed, explicit units, exact source table/record IDs and duplicate groups. Manifest contains counts and canonical table hashes; fixture policy provides expected behavior separately. All three artifacts match regeneration; four sample files also match.

QA checks exact sets, not just counts; mutation tests reject an orphan, unexpected duplicate, wrong truth ID, extra self-confirmation and unintended dormant account without relying on hashes. Seed inserts into empty tables atomically; reset deletes reverse-FK business rows under local-development and explicit-reset guards. Full data is generated in memory, not checked in as a large dataset.

Ground truth is only used by fixture QA and tests; no implemented detector imports it. Future algorithms must remain independent. Current QA is fixture-specific, not a generalized audit engine; its simplified chronology/policy cases do not establish detection accuracy on arbitrary source systems.

# I. Web State

| Route | Page | Classification |
| --- | --- | --- |
| / | Dashboard | PLACEHOLDER |
| /audit-tests | Audit Tests | PLACEHOLDER |
| /findings | Findings | PLACEHOLDER |
| /risks-controls | Risks & Controls | PLACEHOLDER |
| * | Not found | PLACEHOLDER fallback |

REAL FUNCTIONALITY: routing/navigation, shared styling, URL validation and a fetch helper. No data page, forms, authentication state, route guards or audit workflow exists. No page invokes apiFetch.

API_URL is explicitly exposed by Vite and normalized centrally. Automatic environment-prefix exposure is disabled. No direct Web pg/Knex/database access exists. WEB_ALLOWED_HOST is required by the Vite config even during builds and is absent from .env.example. apiFetch has no higher-level response/error state handling yet; it is currently unused.

Configured production build and live Vite nested-route HTML delivery passed. No browser interaction/accessibility test was performed.

# J. Python Audit Engine State

pyproject.toml defines auditlens-engine 0.1.0, Python >=3.11, Pandas >=2.2,<3.1 and an explicit CLI entrypoint. requirements.txt installs the package editable. analyzers, models, repositories and rules contain package markers only.

Only dependency-aware health exists; unittest 1/1 and CLI pass using Pandas 3.0.5. There are no detectors, database drivers/extraction, run models, persistence, scheduling, benchmark execution or evidence output. Future CLI execution is already the ADR-003 direction; exact extraction/provenance contracts remain open. No persistent service is required.

# K. Identity & Authentication State

business.employees/users/roles/permissions and their joins represent **source identities being audited**. They are synthetic facts, including a role named auditor_viewer; that name does not grant AuditLens application access.

AuditLens authentication is **NOT STARTED**: no audit.users migration, password hashes, login routes, JWT library/issuance, refresh sessions, authentication plugin, permission middleware, login UI or guards. JWT variable placeholders are not authentication.

Full authentication is not technically necessary for a local CLI framework. Its operator provenance must still be designed: the proposed required audit_runs.requested_by FK assumes audit.users exists. Resolve that future schema/CLI contract explicitly; do not reuse business.users or create fake authenticated users. Authentication and authorization must precede remote audit execution/evidence access.

# L. Audit Domain State

| Entity | Documented | Implemented | Tested | Runtime verified |
| --- | --- | --- | --- | --- |
| risks | Yes | No | No | No |
| controls | Yes | No | No | No |
| risk_controls | Yes | No | No | No |
| audit_tests | Yes | No | No | No |
| control_tests | Yes | No | No | No |
| audit_runs | Yes | No | No | No |
| audit_test_results / exceptions | Yes | No | No | No |
| evidence | Yes | No | No | No |
| findings | Yes | No | No | No |
| finding_evidence | Yes | No | No | No |
| sod_rules | Yes | No | No | No |
| sod_conflicts | Yes | No | No | No |
| activity_events | Yes | No | No | No |

The audit schema boundary exists in migration source, but does not constitute an implemented audit framework. Risks/controls/procedures are documentation; fixture ground truth is not persisted audit results or evidence.

# M. Environment Configuration State

DATABASE_URL is canonical server-side configuration. requireDatabaseUrl validates PostgreSQL scheme/host without putting the supplied credential in validation errors. Knex receives the original URL. API_URL is canonical public Web configuration; no database/JWT values entered the tested bundles.

API uses PORT, with API_HOST defaulting to 0.0.0.0. .env.example and an API test retain API_PORT: **LEGACY configuration/test references**, documented for stabilization. WEB_ALLOWED_HOST is an implemented build/preview requirement omitted from the example. WEB_PORT is local Vite configuration.

No legacy split DATABASE_HOST/PORT/NAME/USER/PASSWORD application configuration or alternative frontend endpoint variable was found in authored source. POSTGRES_* is **INTENTIONAL Docker initialization**, not application configuration. VITE_UNRELATED_SECRET is an **INTENTIONAL negative test sentinel**. Discussion of legacy names in the review is documentation only.

# N. Security Review

No CRITICAL leak was established in the current tracked files. Only .env.example is tracked; values are placeholders. Targeted current-tree inspection found no hard-coded Railway credential/private key. This is not a historical secret scan or dependency vulnerability audit.

- **HIGH before audit ingestion:** no source-reader grants/write-denial verification. Reusing the migration identity for analysis would defeat the intended boundary; no detector exists yet.
- **MEDIUM:** API start runs migrations using the same service environment, coupling startup to elevated schema privileges. Separate migration execution and future runtime privileges before database-backed audit features.
- **MEDIUM local exposure:** absent API_HOST defaults to all interfaces; previous docs incorrectly promised loopback. Only public health is currently exposed.
- **MEDIUM deployment acceptance:** production Web serving and actual service watch settings are unverified; a preview script exists but its remote usage is unknown.

Positive evidence: generic HTTP 500 response, 1 MiB payload cap, explicit public-env mapping with passing secrecy probe, parameterized schema query, fixed/allowlisted table names, local seed/reset guards, read-only repeatable-read dataset validation and no current Web database access.

CORS is absent, not wildcard/permissive. Live health returned no Access-Control-Allow-Origin for a supplied foreign origin. This blocks future cross-origin browser integration until designed; it is not an auth bypass. No user-supplied SQL or shell execution route exists. Startup logs can emit an Error object; no observed credential disclosure was found, so redaction should be verified when database-backed startup behavior expands.

# O. Testing & Verification State

| Check | Result actually obtained |
| --- | --- |
| Initial Node suite | Failed on stale paths, missing WEB_ALLOWED_HOST and port test |
| After path repairs with WEB_ALLOWED_HOST=localhost | 12/13; only API_PORT test fails |
| Dataset tests | 6/6: determinism, full QA, artifact parity, mutations, guards, offline DDL/rollback |
| Environment tests | 5/5 with required host: URL validation, exact Knex input, missing DB URL, URL normalization, bundle secrecy |
| API tests | Health/error contract passes; port-contract test fails |
| Production Web build | Pass with API_URL and WEB_ALLOWED_HOST supplied |
| Live API HTTP | Loopback ephemeral port /health returns 200/expected JSON; foreign Origin gets no CORS header |
| Live Vite HTTP | Nested /findings returns 200 with correct entrypoint |
| Python | 1/1 unittest; CLI healthy with Pandas 3.0.5 |
| db:check / db:validate-data | Attempted, fail on missing DATABASE_URL before connecting |
| Offline data/sample comparison | All counts and fourteen exact fixture sets pass; zero orphans; four sample files match |
| Documentation | DDL inventory parity, relative links and Mermaid parsing pass; final counts recorded in VERIFICATION.md |
| Git diff whitespace | Pass |

No migration, rollback, seed, reset, production data change or deployment was executed. Missing-configuration tests invoke database command branches with DATABASE_URL explicitly blank; they cannot substitute for live PostgreSQL testing. No browser UI automation or database integration/constraint/privilege tests exist. Do not demand tests for unimplemented business features.

# P. Documentation Mismatches Found

1. README tree placed database at root; catalog/dataset links and nested database README links broke after the move.
2. Root commands, five scripts and two test files still imported removed paths.
3. API_PORT/loopback claims contradicted implemented PORT and all-interface default.
4. WEB_ALLOWED_HOST was undocumented; setup/build examples were incomplete.
5. Deployment arrows and service descriptions did not clearly distinguish browser requests, API database access and separate deployable packages.
6. Railway isolation/start/watch settings were not recorded; Web preview was the only serving script.
7. Prior all-pass verification and Docker-blocked status were historical, not current checkout evidence.
8. Roadmap mandated authentication before framework and implied source identities supply the platform identity model.
9. ADR-004 still described business migrations as deferred.
10. System-design roles read as implemented responsibilities without a prominent target/current qualifier.
11. Source-reader and runtime credential separation were presented as targets without highlighting migration-running API startup.
12. db:status appeared suitable for safe status checking but installed Knex can create metadata.
13. Open questions still called MIT proposed despite an existing LICENSE.
14. Historical Phase 0 implementation plan appeared current.

ERD/dictionary business fields were already correct after path recovery. No schema redesign was needed. Generated dictionary wording points to VERIFICATION.md; “pending” means independent runtime acceptance, not denial of the developer's successful migration report.

# Q. Documentation Corrections Made

| File | What was wrong / change / why |
| --- | --- |
| README.md | Corrected repository tree, ownership, local environment guidance, reported runtime status and next milestone; makes entry instructions match code |
| apps/api/database/seeds/README.md | Fixed link depth to repository docs |
| apps/api/database/sample-data/README.md | Fixed link depth to repository docs |
| docs/01-PROJECT-OVERVIEW.md | Distinguishes offline implementation from reported runtime |
| docs/02-SYSTEM-DESIGN.md | Marks target responsibilities versus current health/placeholder behavior |
| docs/03-SYSTEM-ARCHITECTURE.md | Adds current repository/service boundaries and accurately qualified data-flow diagram |
| docs/04-ERD.md | Clarifies implemented business/planned audit and independent versus reported migration status; generated fields unchanged |
| docs/08-AUDIT-TEST-CATALOG.md | Repairs ground-truth/policy links without changing procedure semantics |
| docs/10-SECURITY-DESIGN.md | Corrects binding claim; records absent CORS/roles and elevated startup boundary |
| docs/11-THREAT-MODEL.md | Corrects local-only assumption and current credential exposure context |
| docs/12-TESTING-STRATEGY.md | Records port/build regression and status-command side effect |
| docs/13-DEVELOPMENT-ROADMAP.md | Reassesses phases and replaces rigid auth dependency with explicit local-CLI/remote-access gates |
| docs/16-SYNTHETIC-DATASET.md | Corrects tooling/artifact paths and next milestone; preserves fixtures |
| docs/18-DATA-LINEAGE.md | Specifies actual API-owned source paths and independent engine boundary |
| docs/DEPLOYMENT.md | Reconciles actual config, service direction, workspace commands and unverified deployment settings |
| docs/IMPLEMENTATION-PLAN.md | Labels Phase 0 plan historical; links current plan |
| docs/OPEN-QUESTIONS.md | Updates runtime/license facts and timing of unresolved decisions |
| docs/PROJECT-OVERVIEW-ID.md | Reconciles Indonesian architecture/status/next-step explanation |
| docs/VERIFICATION.md | Adds current results while preserving historical records |
| docs/adr/ADR-004-database-strategy.md | Records that business migrations now exist |
| docs/adr/ADR-007-api-database-and-independent-deployment.md | New record for the existing intentional architecture decision |
| docs/PROJECT-REVIEW.md | This evidence-based review and ordered next-phase plan |

# R. Architecture Decision Records

All six existing ADRs were read. ADR-001 covers system boundaries, 002 read-only extraction, 003 Python CLI, 004 schema strategy, 005 fixture conventions, and 006 canonical connection variables. None fully documented the database move plus independent Web/API deployments.

Added **ADR-007**, using the next number. It records context, chosen ownership/service boundaries, reasons, alternatives and trade-offs. It preserves root Python/docs/scripts/tests, server-only secrets, HTTP-only Web access and project-specific reasoning. It does not claim Railway settings or read-only privileges were verified.

# S. Roadmap Status

| Phase | Name | Status | Evidence | Remaining work |
| --- | --- | --- | --- | --- |
| 0 | Architecture & Documentation | PARTIAL | Scaffold, health and configured build work; port test regressed | Config/test reconciliation and current deployment acceptance |
| 1 | Business Data Model & Synthetic Dataset | PARTIAL | Eleven tables and all fixture QA implemented | Live seed/rollback/constraints, reader privileges and acceptance evidence |
| 2 | Authentication & RBAC | NOT STARTED | JWT placeholders/design only | Separate identities, sessions, authorization |
| 3 | Audit Framework | NOT STARTED | Empty audit schema and Python health only | Extraction, lifecycle, versions, immutable output/provenance |
| 4 | User Access Review | NOT STARTED | UA procedures and AC fixtures only | Independent detectors and benchmarks |
| 5 | Segregation of Duties | NOT STARTED | Procedures and observed-conflict fixtures only | Permission expansion/rules and observed-event tests |
| 6 | Transaction Testing | NOT STARTED | Fixture QA only | Independent transaction procedures |
| 7 | Audit Trail Analysis | NOT STARTED | Source events and planned catalog | Independent chronological analysis |
| 8 | Findings & Evidence | NOT STARTED | Proposed tables/workflow | Durable evidence and reviewed findings |
| 9 | Dashboard & Reporting | NOT STARTED | Placeholder route | Scope-aware live summaries/exports |
| 10 | Portfolio Polish | PARTIAL | MIT, extensive docs, synthetic disclaimer | Reproducible accepted setup, CI, real audit walkthrough |

No phase is called VERIFIED solely because files exist. Phase 10's partial documentation is incidental groundwork, not a reason to implement reporting early.

# T. Phase 0 Definition of Done

| Requirement | Status | Evidence |
| --- | --- | --- |
| Repository scaffold/workspaces | PASS | Real separated packages and root orchestrators |
| Web runs/builds | PARTIAL | Configured build and live HTTP pass; example lacks required host |
| API runs | PASS | Ephemeral loopback live HTTP 200 |
| Health endpoint/error boundary | PASS | Actual route and injection test |
| Database config foundation | PASS | URL validation and repaired Knex paths tested; live connection separate |
| Environment contract/tests | FAIL | PORT implementation versus API_PORT test/example |
| Python scaffold/health | PASS | CLI and unittest pass |
| Architecture/ERD | PASS | Reconciled docs; generated DDL parity |
| Security/threat model | PASS | Design exists and current gaps explicitly marked |
| Audit methodology/catalog | PASS | Generic traceable concepts and clear fixture/procedure mapping |
| Stakeholder documentation | PASS | English/Indonesian explanations |
| Roadmap | PASS | Evidence-based dependency update |
| Independent Railway operation | NOT VERIFIABLE | REPORTED AS WORKING; remote settings unavailable |

Documentation PASS means the design artifact is present and reconciled, not that its proposed controls are implemented.

# U. Phase 1 Definition of Done

| Requirement | Status | Evidence |
| --- | --- | --- |
| DATABASE_URL works live | NOT VERIFIABLE | Configuration tests pass; connectivity REPORTED AS WORKING |
| Business schema migrations exist | PASS | Two actual migration files |
| Migrations successfully run | NOT VERIFIABLE | REPORTED AS WORKING, not executed here |
| Source-domain tables exist live | NOT VERIFIABLE | Eleven table definitions compile; no live catalog query |
| Deterministic generator | PASS | Same-seed complete equality |
| Controlled seed | PASS | Default and input validation tested |
| Normal source data | PASS | Full generated population/clean negatives |
| Known anomalies | PASS | Fourteen exact sets verified |
| Ground truth | PASS | IDs/units/groups/version and parity |
| Dataset manifest | PASS | Counts/canonical hashes match |
| Dataset validation works | PARTIAL | Offline QA passes; live DB command cannot connect |
| Generator tests | PASS | Six tests pass |
| ERD matches migrations | PASS | Compiled DDL parity |
| Dictionary matches migrations | PASS | Compiled DDL parity |
| Dataset docs match implementation | PASS | Paths corrected; counts/limitations agree |
| Business-process documentation | PASS | Implemented synthetic process described |
| Data-lineage documentation | PASS | Current versus future flow and truth boundary |
| Seed/reset/rollback/constraints | PARTIAL | Guarded code and offline down SQL exist; live acceptance absent |
| Real source-reader denial | FAIL | No provisioning/grants/tests implemented |

Migrations working does not close the remaining acceptance items.

# V. Open Questions

| Question | Classification | Decision/timing |
| --- | --- | --- |
| Employment/account model | RESOLVED BY IMPLEMENTATION | Separate identities and one hire/end interval in v1 |
| Rehire/account disable history | STILL OPEN; CAN WAIT | Required only for broader historical access tests |
| Invoice/vendor identity | RESOLVED BY IMPLEMENTATION | Vendor/reference/currency/amount convention |
| Approval rules | RESOLVED BY IMPLEMENTATION for v1 | Delegation/thresholds/multiple stages CAN WAIT |
| Payment policy | RESOLVED BY IMPLEMENTATION for v1 | Partial IDR payments; FX/refunds CAN WAIT |
| Privilege baseline | Fixture resolved; STILL OPEN for real policy | Before broader UA-003 implementation |
| Dormancy/calendar | Fixture resolved; extensions CAN WAIT | Freeze real policy when scope expands |
| Evidence retention/redaction | STILL OPEN | Minimal policy before durable evidence; external anchoring can wait |
| Snapshot/extraction contract | STILL OPEN | Before framework; fixture hashes are not extraction |
| Worker/queue | Initial CLI direction resolved by ADR | Queue NO LONGER RELEVANT to initial synchronous CLI; revisit for async |
| Platform identity/session model | STILL OPEN; CAN WAIT | Before remote audit operations |
| Database runtime/reader roles | REQUIRED BEFORE NEXT PHASE completion | Local disposable acceptance and real grant tests |
| Configuration/deployment | REQUIRED BEFORE NEXT PHASE completion | PORT/host/tests and actual service settings |
| License | MIT RESOLVED BY IMPLEMENTATION | Owner attribution confirmation CAN WAIT for stabilization |

No new business-policy rule was silently selected.

# W. Blockers

- **CRITICAL:** none established.
- **HIGH:** no independent live Phase 1 acceptance environment/evidence; source-reader privileges are unimplemented. These block claiming source extraction is safe.
- **MEDIUM:** one failing port-contract test and incomplete example settings block a reliable clean setup; Web production serving/watch isolation remain unverified.
- **MEDIUM, repaired:** stale root paths blocked dataset tests, docs checks and database entry commands.
- **LOW:** placeholder labels and broad dependency ranges can wait; they are not blockers to stabilization.

Missing local DATABASE_URL does not mean the developer's Railway database is broken.

# X. Technical Debt

**Fix Before Next Phase completion:** configuration/example/test consistency; portable and documented Web serving; runtime acceptance for existing database tooling; migration-versus-reader privilege boundary; captured Railway isolation settings; safe status tooling. These protect reproducibility and the next extraction boundary.

**Can Be Deferred:** independent auth until remote audit access, unused apiFetch response-state abstraction, fuller source business UI, Python dependency locking until the framework milestone, expanded historical policies, entitlement SoD-positive fixtures until that module, cosmetic placeholder text, generalized validator refactoring and deduplication of dependency declarations.

Do not move root scripts/tests simply because they import backend tooling.

# Y. Digital Audit Portfolio Assessment

Today the project demonstrates thoughtful source modeling, process/control failure examples, exact benchmark units, lineage, exception-versus-finding discipline and reliable offline population QA.

Risk/control mapping, independent procedures, durable evidence, immutable runs, reviewer workflow and reporting remain theoretical/documented. The central missing capability is an independently executed audit procedure whose conclusion can be traced to a validated population and preserved facts.

The highest substantive portfolio value is a local CLI framework followed by one explainable user-access review: for example, independently detect retained former-employee access, preserve supporting employment/account facts, and compare exact outputs against truth only in the benchmark harness. Stabilization is the immediate enabling milestone.

# Z. Next-Phase Options

| Option | Prerequisites/current fit | Architecture/security/complexity | Learning/portfolio value | Rework risk and decision |
| --- | --- | --- | --- | --- |
| A: Finish Phase 1 dataset work | Most source/generator work already implemented; live acceptance remains | Existing schema/fixtures, modest verification effort | Strong data-integrity evidence; little gain from more rows | Low if limited to acceptance; avoid redundant generator rebuild |
| B: Authentication & RBAC | Needs separate platform identity/session policy | Moderate/high security scope; not required for local analysis | Full-stack value, less immediate audit differentiation | Premature identity/runtime schema decisions; defer until remote audit operations |
| C: Audit Framework | Needs stable config, verified source read-only boundary and provenance contract | Moderate scope; explicit CLI fits ADR; no persistent service needed | Highest next substantive audit value | Risks building atop failing setup and unproved access boundary; follow stabilization |
| D: Stabilization | Existing code and reported runtime provide a concrete acceptance target | Bounded config/testing/deployment work; no source redesign | Indirect portfolio value through trustworthy demonstrations | Lowest rework; RECOMMENDED, including remaining Phase 1 runtime acceptance |

Full AuditLens authentication does **not** have to precede a local framework. The concrete dependency is operator provenance and safe source access, not JWT. Public API execution/evidence access does require application authorization.

# AA. Recommended Next Phase

**NEXT PHASE: Configuration and deployment stabilization with Phase 1 runtime acceptance.**

**Why now:** the implementation contains mature fixtures but current setup/tests and live acceptance are inconsistent. Fixing these gives the framework a credible base.

**Why not alternatives:** more dataset features repeat existing work; authentication does not unlock local analysis; framework implementation would carry configuration and privilege gaps forward.

**Prerequisites:** selected disposable local PostgreSQL with explicit destination/credentials; access to actual Railway service settings for read-only inspection; preserve the developer's deployment boundaries and fixture policy.

**Scope:** environment contract, existing command reliability, Web serving/deployment acceptance, safe database status, real migration/seed/reset/constraint checks in disposable infrastructure, and a SELECT-only reader foundation. Record production credential changes as a separate operational step; never weaken guards to seed Railway.

**Deliverables:** consistent example/config/tests; reproducible verification commands/results; documented service commands/watch inputs; constrained source-reader tooling and live denial tests; updated acceptance record. No audit-domain tables are required.

**Definition of Done:** clean configured Node suite/build/docs/Python checks pass; invalid PORT fails; supported preview works; actual Web service serving/SPA fallback and independent deployment settings are evidenced; existing database workflow passes on a disposable instance; reader SELECT succeeds and writes/DDL fail; source data and audit schema remain intact after denied operations; no credentials or server settings leak into browser artifacts. If remote evidence is unavailable, record the remaining gate instead of claiming completion.

**Do not build yet:** login/JWT, audit runs/results/findings schema, anomaly detectors, dashboards, queue or persistent Python service. Do not broaden the business dataset or redesign existing tables.

# AB. Detailed Next-Phase Implementation Plan

**NP-01 — Reconcile configuration and test contract.**
Objective: make local/CI/service startup inputs explicit and consistent.
Likely components: apps/api/src/config/env.js, .env.example, apps/web/vite.config.js, tests/health.test.js, tests/environment.test.js, README and deployment docs.
Dependencies: none.
Expected result: PORT is consistently documented/tested; invalid values fail; explicit local loopback; WEB_ALLOWED_HOST handling documented and appropriately scoped; required test environment is set by fixtures rather than hidden workstation state.
Verification: clean-environment npm test, configured npm run build, missing/invalid value cases and existing secret probe.
Risks/cautions: preserve DATABASE_URL/API_URL, retain Railway PORT behavior, never expose all Vite-loaded variables; decide whether host is preview-only before changing its validation.

**NP-02 — Capture independent service and serving contracts.**
Objective: make the existing deployment reproducible.
Likely components: apps/web/package.json, Web hosting configuration if required, docs/DEPLOYMENT.md, root workspace configuration only where necessary; Railway service settings.
Dependencies: NP-01.
Expected result: actual root/build/start/health/PORT/SPA settings documented; explicit production static serving for Web; portable local preview; per-service watched inputs and shared lockfile caveat.
Verification: local nested-route HTTP, build artifacts, read-only service-setting evidence; controlled deployment-isolation acceptance only within the later implementation task's authorization.
Risks/cautions: no service merge, no arbitrary dependency introduction, no assumption that current remote hosting uses preview; shared dependency changes may affect both services.

**NP-03 — Establish non-mutating database diagnostics and disposable target.**
Objective: separate connectivity/catalog inspection from schema-changing commands.
Likely components: scripts/check-database.js, scripts/dataset-database.js or likely separate status utility, API-owned database tooling, tests, verification docs.
Dependencies: NP-01 and explicitly selected local PostgreSQL.
Expected result: status inspects catalogs/migration records without creating metadata; missing tables are reported; target is redacted and verified as disposable before any writes.
Verification: read-only credential succeeds on catalog inspection, uninitialized database remains unchanged, bad config emits no secret. Record PostgreSQL version.
Risks/cautions: migrate.list() currently ensures metadata; loopback can be a tunnel. Do not infer disposable ownership from hostname alone.

**NP-04 — Complete live acceptance for existing Phase 1 tooling.**
Objective: verify source code actually works under PostgreSQL.
Likely components: existing apps/api/database migrations/seeds/validation, repository database integration tests (likely new), docs/VERIFICATION.md.
Dependencies: NP-03; confirmed disposable database.
Expected result: migrate, inspect eleven tables, rollback/reapply, seed, validate, guarded reset/reseed and revalidate with same logical hashes; different seed only as a separate controlled case. Audit data is not modified by seed/reset.
Verification: actual FK/unique/NOT NULL/status/nonpositive amount/incomplete-confirmation failures in isolated rollback-only transactions; failed seed transaction leaves no partial population; compare exact manifest/ground-truth sets.
Risks/cautions: no production/shared database writes, no guard bypass, no volume deletion; preserve checked-in default seed artifacts and existing table semantics.

**NP-05 — Establish and test source-reader privileges.**
Objective: enforce the read-only source boundary required before framework ingestion.
Likely components: API-owned database provisioning tooling (likely new outside business-domain migrations), isolated database tests, docs/10-SECURITY-DESIGN.md, docs/18-DATA-LINEAGE.md.
Dependencies: NP-04.
Expected result: administrator/migration tooling separated from a non-owner, SELECT-only source identity; fixed approved tables/schema grants, no writer-role memberships, ownership or write-capable functions. API startup migration credential lifecycle documented separately from future runtime identity.
Verification: connect as the actual reader; SELECT succeeds and INSERT/UPDATE/DELETE/DDL fail, including schema/function privilege checks. Confirm denied operations did not change source or audit data.
Risks/cautions: no secret file committed; provision roles only on the disposable environment in tests. Do not turn this into application RBAC or introduce audit-domain schema. Remote privilege rollout requires its own explicit operational acceptance.

**NP-06 — Verify current API/Web boundaries without new features.**
Objective: prevent integration preparation from weakening existing boundaries.
Likely components: tests/environment.test.js, tests/health.test.js, current API/Web config, deployment documentation.
Dependencies: NP-01–02.
Expected result: reproducible health/build/bundle checks; Web continues without database dependencies; documented exact-origin CORS requirements for the later first browser data call.
Verification: HTTP health, 404/sanitized 500, port validation, separate static route fallback, app/environment sentinel build.
Risks/cautions: do not invent auth, data endpoints or dummy dashboards; no need to implement unused CORS behavior in this milestone.

**NP-07 — Record Python readiness and future framework entry contract.**
Objective: preserve the independent CLI boundary and define the next handoff.
Likely components: audit-engine/README.md, docs/OPEN-QUESTIONS.md, docs/13-DEVELOPMENT-ROADMAP.md.
Dependencies: NP-04–05 for source acceptance evidence.
Expected result: existing Python health remains reproducible; framework prerequisites identify source snapshot contract, policy inputs, truth exclusion and CLI operator provenance decision. No new Python analysis code.
Verification: existing unittest/CLI; review that no generator/ground-truth runtime dependency has been added.
Risks/cautions: planned audit_runs.requested_by assumes a platform identity; explicitly defer schema choice to framework design instead of silently reusing source users.

**NP-08 — Close acceptance and update handoff.**
Objective: leave one trustworthy, bounded milestone completion record.
Likely components: docs/VERIFICATION.md, README, docs/13-DEVELOPMENT-ROADMAP.md, next implementation prompt.
Dependencies: NP-01–07.
Expected result: all local checks green, live disposable DB/reader evidence, actual service acceptance recorded separately, concise framework-ready handoff.
Verification: one final appropriate test/build/docs/Python run, secret/diff review, fresh setup reproduction and documented unresolved external gates.
Risks/cautions: no blanket VERIFIED label if Railway evidence is still only reported; no automatic continuation into framework implementation.

# AC. Recommended Sequence After That

| Phase | Primary goal | Dependency | Major deliverable |
| --- | --- | --- | --- |
| Local CLI Audit Framework | Reproducible extraction/run lifecycle and evidence contract | Stabilization plus safe reader | Versioned validated runs, immutable results; non-business harness first |
| User Access Review | Deliver first independent audit conclusions | Framework and frozen access baseline | UA detectors, exact benchmarks and explainable source evidence |
| Authentication & RBAC | Protect remote audit operations | Separate identity/session design and framework contracts | Authorized API/UI with session/object checks |
| SoD and Transaction Testing | Broaden audit coverage | Framework, settled fixture policy; auth for remote use | Entitlement/observed-conflict and decimal transaction procedures |
| Findings & Evidence Workflow | Turn reviewed exceptions into findings | Auth plus at least one independent module | Reviewer transitions and retained evidence |

Audit-trail analysis follows its historical-source prerequisites; reporting follows meaningful executed scope and findings. These are high-level phases, not additional implementation tasks for this review.

# AD. Files I Should Personally Review

1. [PROJECT-REVIEW.md](PROJECT-REVIEW.md): maturity, concrete blockers and next-task boundaries.
2. [VERIFICATION.md](VERIFICATION.md): current passes/failure versus historical/reported runtime.
3. [Deployment](DEPLOYMENT.md) and [ADR-007](adr/ADR-007-api-database-and-independent-deployment.md): chosen ownership and independently deployed services.
4. [Generator](../apps/api/database/generators/index.js) and [fixture QA](../apps/api/database/validation/validate.js): source population versus development assertions.
5. [Business migration](../apps/api/database/migrations/20260914035028_create_business_domain.js): structural integrity while keeping intentional control failures representable.
6. [API environment](../apps/api/src/config/env.js) and [Vite config](../apps/web/vite.config.js): remaining port/host mismatch and public-secret boundary.
7. [Audit test catalog](08-AUDIT-TEST-CATALOG.md): procedures versus fixture IDs and observed versus entitlement SoD.

# AE. Safe Commands I Should Run Locally

From repository root, these commands do not modify database contents. Build produces ignored local output. Tests currently retain one known port-contract failure.

```powershell
$env:API_URL='http://localhost:3001'
$env:WEB_ALLOWED_HOST='localhost'
npm test
npm run build
npm run docs:check
git diff --check
Push-Location audit-engine
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m audit_engine
Pop-Location
```

With DATABASE_URL already supplied privately for an explicitly selected authorized database:

```powershell
npm run db:check
npm run db:validate-data
```

The latter reads the full fixture and can be expensive on an unrelated population; use the intended synthetic database. Do not put credential values in shared command output. db:status is omitted because of its metadata side effect on fresh databases. Migrate/rollback/seed/reset are not non-destructive inspection commands and are not included here.

# AF. Railway Impact of the Recommended Next Phase

**Web:** may need a documented production static server, host/PORT setup and validated watch paths; keep its independent service. No new dashboard.

**API:** reconcile PORT/tests and record migration startup policy; plan/verify credential separation. No new application endpoint or authentication.

**PostgreSQL:** existing schema/data preserved remotely. Live workflow and source-reader grants are tested on disposable local infrastructure first; no business-table redesign.

**audit-engine:** no Railway deployment. Existing Python health remains local. Later CLI analysis does not require an always-on service.

No deployment was performed during this review.

# AG. Files Changed During This Review

**Documentation changes:** the 22 files individually listed in section Q.

**Configuration/path repairs only:**

- package.json: root db:migrate and db:rollback now locate API-owned Knex configuration.
- scripts/check-database.js: corrected Knex import.
- scripts/dataset-database.js: corrected config/generator/validator/seed/core/artifact imports.
- scripts/document-schema.js: corrected generator/validator imports; generated prose/schema logic unchanged.
- scripts/generate-dataset.js: corrected generator/validator/artifact imports.
- scripts/migration-sql.js: corrected actual migration import.
- tests/dataset.test.js: corrected source imports and fixture artifact path.
- tests/environment.test.js: corrected Knex/config command paths.

No source tree moves, schema edits, new features, dependency changes or test expectation changes. The configured build updated only ignored output. The initial working tree was clean.

# AH. Final Recommendation

1. **Where today?** Substantial offline-verified Phase 1 source dataset on a partially stabilized foundation; no independent audit execution.
2. **Immediately next?** Configuration and deployment stabilization with Phase 1 runtime acceptance.
3. **What waits?** Auth, framework implementation, detectors, findings and dashboards until this bounded gate; then local framework before full remote auth.
4. **Biggest architecture risk?** Treating schema separation and migration-capable service credentials as an enforced read-only audit boundary.
5. **Biggest portfolio opportunity?** One independent, explainable user-access audit with immutable evidence and exact-set benchmarking.
6. **Ready?** Ready to begin stabilization now. Completion needs disposable PostgreSQL and actual service evidence; not yet ready to claim framework source-access prerequisites are verified.

# AI. Suggested Git Commit

Prefer two reviewable commits because both categories are material:

- `fix: align project paths with API-owned database architecture`
- `docs: align project documentation with current AuditLens architecture`

No commit was created.
