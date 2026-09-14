# Security design

**Target controls below are planned unless explicitly identified as implemented. Current surfaces are public health and static placeholders; independent Railway services are REPORTED AS WORKING. This is not a production security acceptance.**

## Authentication and JWT
Use independent audit identities. Plan Argon2id password hashing with per-password salts, benchmarked parameters and no recoverable passwords. Login failures use generic messages and throttling. Access JWTs are short-lived, held in browser memory, and checked for signature, fixed allowed algorithm, issuer, audience, expiry and active account status. JWT payloads contain no sensitive evidence.

Refresh tokens use Secure/HttpOnly/SameSite cookies, rotation, hashed server-side storage, replay detection and revocation. Origin and CSRF protection apply to cookie-based endpoints. Session storage design is pending Phase 2. Never implement insecure placeholder authentication.

## Authorization and RBAC
Default deny. Proposed viewer reads authorized audit summaries; auditor executes tests and drafts findings; manager approves and closes. Permissions are checked server-side per endpoint and object, including exports and evidence. Business permissions being reviewed are separate from platform roles. A UI hidden button is not authorization. Enforce separation between author and reviewer where the final workflow requires it.

## Least privilege and read-only source
Explicit provisioning creates auditlens_source_reader as a NOLOGIN, non-owner, non-superuser role with no parent memberships. It receives CONNECT, business USAGE and SELECT on eleven approved tables; no source writes, DDL, sequence or audit grants. PUBLIC database CREATE/TEMP and application schema/table/routine permissions are revoked in the dedicated database. Provisioning-owner default function/table grants are restricted; future tables are not automatically exposed. See [provisioning guide](../apps/api/database/security/README.md) and [ADR-008](adr/ADR-008-database-privilege-separation.md). Actual PostgreSQL 17.5 permission tests PASSED on the disposable local cluster: all source SELECTs succeeded; INSERT/UPDATE/DELETE/TRUNCATE, CREATE/ALTER/DROP, schema/TEMP creation, audit access and tested function execution failed with 42501. Source hashes were unchanged. This verifies that provisioned identity only; Railway grants remain NOT VERIFIABLE.

## Input and database protection
Validate payload schemas, lengths, enums, IDs and pagination. Use Knex bindings or parameterized SQL; allowlist identifiers and sort keys because parameters do not escape identifiers. No arbitrary SQL or shell commands accepted from clients. Cap extract sizes and run concurrency.

## Logging, evidence and errors
Separate source events from platform activity. Record actor, time, action, target and request/run ID; redact passwords, tokens and unnecessary personal data. Evidence snapshots are append-only by runtime policy, hashed and linked to results. Hashes stored beside data are not protection against a database administrator; external anchoring and retention remain open.

Implemented: centralized environment loading, bounded database tooling pool, generic internal HTTP error responses, 1 MiB payload limit and graceful shutdown. API_HOST defaults to 0.0.0.0; the example file supplies loopback for local use. Health is liveness, not database readiness. CORS is not enabled, and no page currently calls the API.

Current start command runs migrations before starting Hapi, so that service receives migration-capable credentials. Separating migration execution from future least-privilege runtime access is outstanding; do not interpret the target credential model above as delivered. Reader provisioning is an explicit separate administration step, not part of the two migrations. The Phase 1 seed is administrator tooling, not audit ingestion. Repeat actual source-reader permission acceptance after grant/schema changes and before extraction on any new target.

## Secrets and local exposure
The implemented [local framework](AUDIT-FRAMEWORK.md) prefers a dedicated reader URL and ALWAYS selects the fixed restricted role before explicit allowlisted SELECTs in a read-only repeatable-read transaction. No SQL/role/table CLI input exists. Extraction errors suppress driver details. Snapshot metadata has no connection identity, host or password. Deeply frozen context carries no database handle. Canonical UUID paths, containment/link checks and atomic no-clobber publication protect local artifacts; validation rejects tampering. AUDIT_OPERATOR is explicit and defaults to local. Runtime artifacts are ignored, but still need OS access restrictions and operator-managed retention. Hashes are not signatures and trusted local code is not sandboxed. Production grant drift and source-field content require separate review.

Only .env.example is tracked; local .env, virtual environments and build outputs are ignored. Vite disables automatic environment exposure and defines only API_URL; build probes verify database/JWT sentinels are absent. WEB_ALLOWED_HOST is optional local-preview configuration; production Web uses a dist-only static server. Compose requires a supplied database password and binds PostgreSQL to loopback. Remote authenticated audit access still requires the planned authorization, session and deployment controls. See [current verification](VERIFICATION.md). CORS remains deferred until real separate-origin browser API calls; full authorization is required before remote audit access. Reset/rollback refuse production even with opt-in, validate the local destination before connection, and require AUDITLENS_ALLOW_LOCAL_RESET=YES.
