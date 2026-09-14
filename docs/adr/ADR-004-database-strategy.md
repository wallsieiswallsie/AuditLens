# ADR-004: Database strategy

Status: accepted foundation direction; future controls remain planned.
Date: 2026-09-14

## Decision
Use one PostgreSQL database named auditlens with business and audit schemas; Knex owns migrations in public metadata tables.

## Rationale
Simple Compose setup with visible logical boundaries and transactional integrity.

## Alternatives considered
Separate databases; SQLite; a single shared schema.

## Trade-offs and consequences
Schemas are not protection against the database owner. Future least-privilege roles must be verified. Historical Phase 0 deferred domain migrations; Phase 1 subsequently implemented eleven business tables under apps/api/database/migrations. Audit-domain tables remain planned. See [ADR-007](ADR-007-api-database-and-independent-deployment.md) for current tooling ownership.

## Follow-up
See [open questions](../OPEN-QUESTIONS.md) and [roadmap](../13-DEVELOPMENT-ROADMAP.md). Revisit through a superseding ADR if requirements change.
