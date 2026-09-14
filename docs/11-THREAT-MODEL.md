# Threat model

The trust boundaries are browser→API, API/engine→database, source→extract and developer workstation→repository. This is an educational project with separate Railway services REPORTED AS WORKING. Controls in this table are planned unless verified elsewhere. Compose binds to loopback; the API defaults to 0.0.0.0 unless API_HOST is set. Ignored secret files and explicit frontend environment exposure are implemented. Migration-capable API startup credentials remain a boundary concern before database-backed audit routes are added.

| Threat | Asset | Attack scenario | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| Reader privilege drift | Source integrity | Reader inherits writes, ownership or executable mutating routines | Extraction alters source | Explicit role checks, PUBLIC/default privilege restrictions, whitelist SELECT and real PostgreSQL write/DDL/function denial acceptance; repeat after changes |
| Migration identity reused for extraction | Source integrity | Engine uses owner DATABASE_URL | Unrestricted modification | Dedicated reader role and separate future login; current API migration credential remains elevated and must not be reused by engine |
| Browser secret exposure | Credentials | Build publishes environment values | Database compromise | Explicit API_URL mapping, disabled automatic env exposure and production bundle sentinel probes |
| Destructive tooling targets production | Source availability | Reset/rollback uses wrong URL | Data loss | Development/loopback/database guards, explicit opt-in, no production override; self-created acceptance cluster ignores DATABASE_URL |
| Unauthorized auditor access | Evidence and findings | Stolen password or token permits review | Confidentiality loss | Password hashing, short JWT expiry, rotation, revocation and object authorization |
| Source manipulation | Business population | Employee changes data before extraction | Missed or misleading exceptions | Read-only extraction, source logs, manifests, reconciled counts and explicit extraction cutoff |
| Result manipulation | Audit conclusions | User edits completed results | False conclusions | Immutable runs, restricted writer, platform events and reviewer approval |
| Privilege escalation | Platform permissions | Caller changes role or accesses another object's ID | Unauthorized control | Default-deny permissions, no mass assignment and authorization tests |
| Deleted evidence | Finding support | Owner deletes a source row or snapshot | Findings cannot be substantiated | Independent snapshots, restricted deletion, backups and retention policy |
| Insecure API | Database and availability | Injection, oversized request or unlimited run requests | Data loss or denial of service | Parameter binding, schema validation, rate limits and bounded work |
| Leaked credentials | Database and identities | .env or logs committed | Unauthorized access | Git ignores, secret review, redaction and rotation |
| Compromised audit logs | Event history | Administrator rewrites records | Concealed misuse | Restricted append-only runtime access, external anchoring later, documented residual admin risk |
| Dependency compromise | Developer machine | Malicious package install | Code execution | Lockfiles, reviewed updates and minimal dependencies |
| Inconsistent extraction | Evidence accuracy | Concurrent updates split related records | False positives/negatives | Consistent snapshot, validation and transaction cutoff |

Residual risks: a local database administrator controls both schemas, a compromised host can read local secrets, and incomplete source logging limits what tests can infer. Schema separation is logical isolation, not an independent security perimeter.
