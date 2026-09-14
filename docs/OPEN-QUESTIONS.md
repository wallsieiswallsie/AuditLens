# Open architectural questions

Phase 1 decisions are AuditLens project conventions, not authoritative professional audit standards. [ADR-005](adr/ADR-005-phase-1-dataset-conventions.md) records each decision, rationale, alternatives and limitations.

| Question | Status / decision | Follow-up |
| --- | --- | --- |
| Employee authority and lifecycle | Resolved for fixture: separate employees/accounts, one hired_at/ended_at interval, independent account state | Real HR history, rehire and effective account-disable history remain open |
| Invoice identity and vendors | Resolved: vendor + trimmed uppercase reference + currency + amount; duplicate references permitted, UUID unique | Credit notes deferred |
| Approval policy | Resolved for fixture: single-stage approval for every applicable invoice; decisions authoritative, rejection invalidates prior approval | Delegation/thresholds/multiple stages deferred |
| Payments | Resolved: partial payments, IDR only, confirmed sums per invoice | Refunds/reversals/FX deferred |
| Baseline privileges | Fixture-only per-account allowed roles provided separately | Real versioned job policy remains Phase 4 |
| Dormancy/unusual hours | Fixture-only frozen as-of, >90 days, never-used fallback, Asia/Jakarta weekday 09:00–17:00, no holidays | Real calendars and service-account treatment remain Phase 4 |
| Evidence/reference semantics | sample:// only; logs preserve polymorphic IDs; no external fetch | Retention, redaction and externally anchored integrity remain Phase 3 |
| Snapshot method | Fixture version, fixed timestamps and canonical hashes resolved; QA database read uses repeatable-read transaction | Actual source extraction/export strategy remains Phase 3 |
| Worker execution | Unresolved; explicit CLI first | Queue polling/cancellation before asynchronous runs, Phase 3 |
| Identity roles/authentication | Unresolved; proposed auditor/manager/viewer | Admin separation and refresh-session model, Phase 2 |
| Database runtime and read-only roles | Unresolved on this host; Docker unavailable and password absent | Verify migrations/seed/rollback and actual source-reader denial before declaring Phase 1 complete |
| License ownership | MIT remains proposed | Confirm copyright holder before publishing |

Business migrations and synthetic tooling are implemented. Audit-domain tables and production policy are still planned. No future architecture was silently finalized.
