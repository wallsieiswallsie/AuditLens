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
Schemas are not protection against the database owner. Future least-privilege roles must be verified. Domain migrations are deferred until policy questions are resolved.

## Follow-up
See [open questions](../OPEN-QUESTIONS.md) and [roadmap](../13-DEVELOPMENT-ROADMAP.md). Revisit through a superseding ADR if requirements change.

