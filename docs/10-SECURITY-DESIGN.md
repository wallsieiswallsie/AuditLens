# Security design

**Target controls below are planned unless explicitly identified as implemented. Phase 0 is local-only and exposes only public health plus static placeholders.**

## Authentication and JWT
Use independent audit identities. Plan Argon2id password hashing with per-password salts, benchmarked parameters and no recoverable passwords. Login failures use generic messages and throttling. Access JWTs are short-lived, held in browser memory, and checked for signature, fixed allowed algorithm, issuer, audience, expiry and active account status. JWT payloads contain no sensitive evidence.

Refresh tokens use Secure/HttpOnly/SameSite cookies, rotation, hashed server-side storage, replay detection and revocation. Origin and CSRF protection apply to cookie-based endpoints. Session storage design is pending Phase 2. Never implement insecure placeholder authentication.

## Authorization and RBAC
Default deny. Proposed viewer reads authorized audit summaries; auditor executes tests and drafts findings; manager approves and closes. Permissions are checked server-side per endpoint and object, including exports and evidence. Business permissions being reviewed are separate from platform roles. A UI hidden button is not authorization. Enforce separation between author and reviewer where the final workflow requires it.

## Least privilege and read-only source
Phase 0 uses an administrator credential only for local migrations. It must never become an API/engine runtime identity. Before Phase 1 ingestion, provision separate operational writer, audit source reader and audit result writer roles. Source reader receives CONNECT, USAGE on business and SELECT only on explicitly approved tables/views; revoke public schema CREATE and verify default privileges for future tables. It must lack ownership, membership in writer roles, write-capable functions and audit write grants. Read-only transactions add defense in depth, not a substitute for grants. Separate connection pools prevent accidental source writes.

## Input and database protection
Validate payload schemas, lengths, enums, IDs and pagination. Use Knex bindings or parameterized SQL; allowlist identifiers and sort keys because parameters do not escape identifiers. No arbitrary SQL or shell commands accepted from clients. Cap extract sizes and run concurrency.

## Logging, evidence and errors
Separate source events from platform activity. Record actor, time, action, target and request/run ID; redact passwords, tokens and unnecessary personal data. Evidence snapshots are append-only by runtime policy, hashed and linked to results. Hashes stored beside data are not protection against a database administrator; external anchoring and retention remain open.

Implemented: centralized environment loading, bounded database pool, loopback API, generic internal error response and graceful shutdown. Health is liveness, not database readiness. No credentials are required for health.

## Secrets and local exposure
Only .env.example is tracked; local .env, virtual environments and build outputs are ignored. Never use VITE_ variables for secrets. Compose requires a locally supplied database password and binds PostgreSQL to loopback. HTTPS, cookie security and deployment hardening are mandatory before remote use; they are not delivered here.

