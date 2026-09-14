# System architecture

Diagrams describe the target architecture unless labeled current. Phase 0 implemented the web shell, API health, schema boundaries and engine health CLI. Phase 1 adds business domain migrations, deterministic synthetic generation and fixture QA; disposable local PostgreSQL runtime acceptance now passes (see VERIFICATION.md).

The developer reports PostgreSQL connectivity and migrations working: **REPORTED AS WORKING**, not independently executed here. The [verification record](VERIFICATION.md) separates current local acceptance from unverified remote settings; the review is historical.

## Current repository and deployment boundaries

apps/api owns Hapi source and apps/api/database (Knex configuration, migrations, generators, seeds, validation and sample-data). Root scripts and tests orchestrate cross-component verification. audit-engine remains an independent Python package; docs remains repository documentation. Root npm workspaces delegate web/API development and web builds; root database commands point into API-owned tooling.

```mermaid
flowchart LR
  Browser --> Web["@auditlens/web — apps/web"]
  Web -->|"HTTPS / API_URL — future data calls"| API["@auditlens/api — apps/api"]
  API -->|"DATABASE_URL — migration/tooling access"| DB["PostgreSQL: business + audit"]
```

Separate Railway services are an explicit requirement and REPORTED AS WORKING. No page currently invokes apiFetch; health is database-free. API start runs migrations before the server. Python is not a deployed service. Railway watch paths and service settings are not checked into the repository and have not been inspected remotely. See [deployment](DEPLOYMENT.md) and [ADR-007](adr/ADR-007-api-database-and-independent-deployment.md).

## Database identities

CURRENT: DATABASE_URL remains the API/migration connection. Extraction prefers AUDIT_SOURCE_DATABASE_URL and always selects the provisioned NOLOGIN auditlens_source_reader role in a read-only repeatable-read transaction. A separate unprivileged login exercises the real CLI in disposable acceptance. No reader credential belongs in Web. Snapshot/execution/results are local files; least-privilege API runtime and database result writer remain planned. See [ADR-008](adr/ADR-008-database-privilege-separation.md), [ADR-009](adr/ADR-009-snapshot-based-audit-execution.md) and [framework contracts](AUDIT-FRAMEWORK.md).

## Current local execution

The Python package owns contracts, normalization, hashes, immutable context and execution. A narrow Node bridge reuses pg for approved SELECTs only. Detectors receive frozen context and never import the source repository. Source → extraction → snapshot/manifest/hash → validated audit context → framework.health → local run/provenance/result. The diagrams below include future database persistence and business analysis, which are not implemented.

## 1. System context
```mermaid
flowchart LR
  Employee --> Demo["Demo Business System (planned)"]
  Demo --> Source["Operational records"]
  Source --> Lens["AuditLens (planned analysis)"]
  Auditor --> Lens
  Lens --> Owner["Business owner"]
```
Employees generate source activity. AuditLens independently analyzes it. Auditors review conclusions and owners respond to findings.

## 2. Containers and components
```mermaid
flowchart TB
  Web["React 19 web"] --> API["Hapi API"]
  API --> Auth["JWT and RBAC (planned)"]
  API --> AuditRepo["Audit repositories (planned)"]
  AuditRepo --> AuditDB["PostgreSQL audit schema"]
  Demo["Business module (planned)"] --> BizDB["PostgreSQL business schema"]
  CLI["Local run CLI"] --> Engine["Python frozen audit context"]
  BizDB -->|SELECT only| Reader["Restricted extraction bridge"]
  Reader --> Snapshot["Validated frozen snapshot"]
  Snapshot --> Engine
  Engine --> Writer["Audit result writer (planned)"]
  Writer --> AuditDB
```
The web is a Vite application. Hapi provides a single API with separated modules. PostgreSQL hosts two schemas. Python handles snapshot normalization and framework execution. Extraction prefers a dedicated login selecting the explicitly provisioned reader role. Results currently use local files; the diagram's database writer remains planned. No queue, cache or deployed Python service is introduced.

## 3. Audit data flow
```mermaid
flowchart LR
  Source["Business tables"] --> Snapshot["Read-only consistent snapshot"]
  Snapshot --> Quality["Validate population"]
  Quality -->|valid| Analyze["Versioned test"]
  Quality -->|invalid| Failed["Inconclusive / failed"]
  Analyze --> Evidence["Evidence snapshot and hash"]
  Evidence --> Results["Audit results"]
  Results --> Review["Human review"]
  Review --> Findings["Findings"]
```
Snapshot metadata permits reproducibility. Hashes detect changes only when compared against a trusted value; database hashes alone do not make evidence tamper-proof. Raw sensitive fields should be minimized.

## 4. Authentication flow (planned)
```mermaid
sequenceDiagram
  participant U as Browser
  participant A as Hapi API
  participant D as Audit identity store
  U->>A: Login over HTTPS
  A->>D: Find identity and verify password hash
  D-->>A: Identity and assigned role
  A-->>U: Short-lived access JWT and refresh cookie
  U->>A: Bearer access JWT
  A->>A: Verify signature, issuer, audience, expiry and permissions
  A-->>U: Authorized response or 401/403
```
Access tokens remain in memory. Refresh tokens will be rotated and stored hashed server-side. Refresh cookies require HttpOnly, Secure and SameSite plus origin/CSRF checks. No authentication is implemented yet.

## 5. Audit testing flow (planned)
```mermaid
flowchart TD
  Request["Authorized run request"] --> Freeze["Freeze versions and parameters"]
  Freeze --> Extract["Extract source population"]
  Extract --> Validate["Validate data"]
  Validate --> Decision{"Data usable?"}
  Decision -->|No| Error["Record failed run"]
  Decision -->|Yes| Tests["Execute selected tests"]
  Tests --> Persist["Persist results and evidence atomically"]
  Persist --> Complete["Complete run"]
  Complete --> Review["Review exceptions"]
```
Future run orchestration must enforce idempotency and bounded workloads. Tests return pass, exception or error, with population counts; they do not issue assurance opinions.

## Technology references
Implementation follows [Vite setup](https://vite.dev/guide/), [DaisyUI Vite integration](https://daisyui.com/docs/install/vite/) and [Hapi startup](https://hapi.dev/tutorials/en_us/getting-started). npm lockfiles capture installed versions.
