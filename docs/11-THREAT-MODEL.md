# Threat model

The trust boundaries are browser→API, API/engine→database, source→extract and developer workstation→repository. This is a local educational environment; controls in this table are planned except loopback bindings and ignored environment files.

| Threat | Asset | Attack scenario | Impact | Mitigation |
| --- | --- | --- | --- | --- |
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

