# System architecture

Diagrams describe the target architecture unless labeled current. Phase 0 implemented the web shell, API health, schema boundaries and engine health CLI. Phase 1 adds business domain migrations, deterministic synthetic generation and fixture QA; PostgreSQL runtime verification remains pending.

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
  CLI["Explicit run CLI (planned)"] --> Engine["Python / Pandas / SQL"]
  BizDB -->|SELECT only| Reader["Source reader (planned)"]
  Reader --> Engine
  Engine --> Writer["Audit result writer (planned)"]
  Writer --> AuditDB
```
The web is a Vite application. Hapi provides a single API with separated modules. PostgreSQL hosts two schemas. Python handles tabular analysis. Reader and writer use different credentials; no source-writing capability belongs to the reader. No queue, cache or additional service is required in Phase 0.

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
