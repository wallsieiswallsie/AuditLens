# ADR-009: Snapshot-Based Audit Execution

Status: Accepted. Date: 2026-09-15.

## Context

ADR-002 established source read-only access and ADR-008 defined reader privileges.
Neither froze the execution boundary, serialization or local persistence contract.
Live detector queries would couple rules to PostgreSQL and allow changing populations
between checks, making findings difficult to reproduce and explain.

## Decision

Audit detectors operate on frozen snapshots rather than directly querying the
operational source database. Extract eleven approved business tables in one
read-only repeatable-read transaction using the existing restricted role. Use a
dedicated AUDIT_SOURCE_DATABASE_URL when supplied; DATABASE_URL remains the server
default, with mandatory restricted-role selection even on fallback.

Use the installed Node pg driver as a private extraction transport and retain Python
ownership of typed contracts, deterministic normalization, validation, context,
execution and local artifacts. Add no dependencies. Publish canonical JSONL and a
versioned manifest with table and logical snapshot SHA-256 hashes. Detectors receive
only frozen context. Record versions/configuration and explicit neutral-default
operator provenance. Persist results locally; an audit database writer is deferred.

## Benefits

Reproducible populations, offline execution, narrower source privileges and portable
evidence. Findings can reference table/primary key/field plus snapshot/run/detector/
policy identities without depending on mutable source rows. Ground truth stays in
the evaluation harness. No browser database credentials or new API surface is needed.

## Trade-offs

Snapshot storage duplicates data and needs operator-controlled permissions/retention.
Initial extraction is memory-bound and needs both repository runtimes. Hashes detect
changes relative to a trusted identity; they do not authenticate the source or stop
an administrator rewriting files and hashes. Snapshot UUIDs/times differ on exports
while content hashes remain stable. Source completeness and trusted code remain
assumptions. Database result storage, signed manifests, scalable extraction and
untrusted-plugin isolation require later decisions.

## Alternatives

Direct detector SQL was rejected for privilege coupling and inconsistent populations.
API extraction would require premature authentication/endpoints. A new Python driver
would duplicate the installed transport dependency for this repository-local scope.
Immediate database result tables would require a writer identity and extra migrations.

See [framework specification](../AUDIT-FRAMEWORK.md) and [verification](../VERIFICATION.md).
