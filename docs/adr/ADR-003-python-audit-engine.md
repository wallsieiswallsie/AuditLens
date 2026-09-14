# ADR-003: Python audit engine

Status: accepted foundation direction; future controls remain planned.
Date: 2026-09-14

## Decision
Use Python, Pandas and parameterized SQL through an explicit CLI first.

## Rationale
Tabular analysis is readable and testable without a new network service.

## Alternatives considered
All analysis in Node; Python HTTP microservice; distributed processing.

## Trade-offs and consequences
Two language toolchains; serialization, decimal precision and versioning need explicit contracts. No rules yet.

## Follow-up
See [open questions](../OPEN-QUESTIONS.md) and [roadmap](../13-DEVELOPMENT-ROADMAP.md). Revisit through a superseding ADR if requirements change.

