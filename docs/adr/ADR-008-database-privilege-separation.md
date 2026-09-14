# ADR-008: Database privilege separation

Status: Accepted; runtime evidence is recorded in [verification](../VERIFICATION.md).
Date: 2026-09-14.

## Context

Schemas alone cannot stop an extractor from changing source data. Current API start runs migrations and requires an owner-capable DATABASE_URL. Future Python extraction must have a narrower identity. ADR-007 already fixes tooling ownership and independent deployment; this record addresses grants only.

## Decision

Keep the migration/admin identity responsible for schema changes and local fixtures. The API currently shares that startup identity; a distinct future runtime identity is PLANNED before database-backed audit endpoints.

Provision a NOLOGIN auditlens_source_reader permission role explicitly, outside migrations/startup. It owns nothing, belongs to no parent role, and receives CONNECT, business USAGE and SELECT on eleven explicitly approved source tables. Source writes, DDL, sequences and audit access are not granted. Revoke inherited PUBLIC capabilities in the dedicated application schemas/database; control the provisioning owner's default table/function grants. New tables require explicit approval. Use a separate unprivileged login with SET ROLE for acceptance; no additional application URL or stored reader password is necessary yet.

A future result writer is PLANNED with access only to approved audit results, independently of the reader. Extraction, result tables and authentication are outside this milestone.

## Alternatives considered

- Reuse migration credentials with read-only transactions: transaction settings are reversible and do not enforce least privilege.
- Grant SELECT on all current/future schemas: overexposes metadata/results and future tables.
- Provision LOGIN/password in a migration: embeds credential lifecycle and cluster administration in routine deployment.
- Separate databases: stronger operational separation, but unnecessary for the current educational deployment.

## Trade-offs and security implications

PUBLIC revocations affect every identity relying on those grants; apply only after administration review of the dedicated database. Role creation requires cluster privileges that a hosted account may lack. Owner/admin remains powerful; this is a runtime identity boundary, not protection against the database administrator. Other future owners need separately reviewed defaults. Existing unsafe roles fail provisioning rather than being silently repurposed. Grant drift requires revalidation.

The [provisioning guide](../../apps/api/database/security/README.md) and live acceptance runner define the reproducible process. Production provisioning and secret issuance remain separate manual operational work.
