# ADR-001: System boundaries

Status: accepted foundation direction; future controls remain planned.
Date: 2026-09-14

## Decision
Use one modular API and a separate Python analysis package; maintain distinct operational and audit modules and identities.

## Rationale
Makes source ownership explicit while keeping local development understandable.

## Alternatives considered
Microservices; one undifferentiated CRUD application.

## Trade-offs and consequences
Less deployment overhead, but module and credential separation require discipline. Phase 0 has no operational endpoints.

## Follow-up
See [open questions](../OPEN-QUESTIONS.md) and [roadmap](../13-DEVELOPMENT-ROADMAP.md). Revisit through a superseding ADR if requirements change.

