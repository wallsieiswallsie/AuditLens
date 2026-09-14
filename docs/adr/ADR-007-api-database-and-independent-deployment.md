# ADR-007: API-owned database tooling and independent Web/API deployment

Status: Accepted — records the developer's existing architecture decision.
Date: 2026-09-14.

## Context

AuditLens is an npm monorepo with separate Web and API packages and an independent Python audit-engine scaffold. Database tooling was intentionally moved into apps/api/database, while older docs and root imports still referenced a root database directory. Railway Web and API are separate services, reported working by the developer. Remote watch-path settings are not verified by repository inspection.

## Decision

Keep migrations, Knex configuration, development seeds, generators, fixture validation and sample artifacts in apps/api/database. PostgreSQL access is a backend responsibility. Root scripts/package commands may orchestrate API-owned tooling without owning its implementation.

Keep apps/web and apps/api separately deployed as @auditlens/web and @auditlens/api. Web uses HTTP through public API_URL; DATABASE_URL and future JWT secrets remain server-side. Web has no direct PostgreSQL dependency. Do not serve React from Hapi to reduce service count.

Retain audit-engine, docs, scripts and tests at root for their independent, documentation, repository-tooling and cross-component responsibilities. Python starts as an explicit CLI and is not automatically a persistent Railway service.

## Reasons

This gives database source a clear API owner and allows Web and API releases to be isolated. It preserves the existing AuditLens implementation and keeps browser configuration separate from credentials. It is a project choice, not a claim that this structure is universally superior.

## Alternatives considered

- Root-owned database tooling: valid in other monorepos, but not selected for AuditLens's backend ownership model; retaining it would undo the intentional move.
- Combined Web/API service: fewer services but conflicts with required independent deployment.
- Move all root components under API: confuses independent Python analysis and repository-wide verification with backend source.
- Persistent Python HTTP service: adds operations before any execution requirement exists; revisit only if CLI execution becomes insufficient.

## Trade-offs and follow-up

Root-relative imports must follow the move. Workspace commands can legitimately use database/knexfile.js relative to apps/api. One root lockfile means some shared dependency changes affect both builds; independent service watch paths must reflect real build dependencies. Cross-origin browser requests require a deliberate API policy when integrated. Schema separation alone does not enforce read-only access, and migration-running API startup does not deliver least-privilege runtime credentials.

The [review](../PROJECT-REVIEW.md) records path repairs and remaining stabilization work; [deployment](../DEPLOYMENT.md) distinguishes supported commands from reported Railway settings. No deployment or feature implementation is authorized by this record alone.
