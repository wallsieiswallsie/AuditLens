# ADR-002: Audit read-only principle

Status: accepted foundation direction; future controls remain planned.
Date: 2026-09-14

## Decision
Audit extraction uses a SELECT-only source identity; results use an independent audit writer. No cross-schema evidence FKs.

## Rationale
Analysis must not alter source records and conclusions must survive source changes.

## Alternatives considered
Shared administrator connection; live-row evidence references.

## Trade-offs and consequences
Extra credential provisioning and snapshot storage; grants are planned before ingestion, not implemented by empty schemas.

## Follow-up
See [open questions](../OPEN-QUESTIONS.md) and [roadmap](../13-DEVELOPMENT-ROADMAP.md). Revisit through a superseding ADR if requirements change.

