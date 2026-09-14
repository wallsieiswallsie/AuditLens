# ADR-010: Detector SDK and Audit Policy

Status: Accepted (local framework scope)
Date: 2026-09-15

## Context

ADR-009 established validated snapshots and frozen context. The single health analyzer
needed a formal versioned extension boundary before introducing business rules.
Existing snapshot hashes, artifact contracts, CLI health behavior and source isolation
must remain compatible.

## Decision

Use a frozen AuditPolicy and explicit DetectorRegistry of trusted repository modules.
An AuditDetector Protocol receives only AuditContext and frozen validated DetectorConfig
and returns the existing AuditResult. Frozen metadata owns detector identity, version,
schema/table/field requirements and deterministic configuration defaults. No filesystem
plugin discovery or user-directed imports are permitted.

Incrementally add execute_policy for multiple detectors, retaining execute as the
single-health compatibility API. Persist complete policy once at run level, preserve
existing run/result provenance fields, and add a separate logical-results checksum
artifact without changing historical JSON contract shapes. Framework version is 0.3.0.

Requirements failures produce stable skipped statuses; detector exceptions produce a
fixed error status without exception text. Strict policies stop further calls and
record skips. Partial policies continue. Any incomplete run is marked failed, while
its completed results remain available. Deterministic ordering and normalized content
IDs support logical equivalence across runs.

## Consequences

No new runtime dependency, source adapter, migration, authentication, Railway change,
or business audit logic is introduced. Configuration types are currently boolean and
integer. Empty-table requirements use the loader's schema inventory. Registry versions
can be checked explicitly and all resolved versions are recorded, but policies do not
yet pin an expected version map. The caller must use the recorded registry release to
reproduce a historical run.

The boundary is for trusted in-process code; it is not a Python or OS sandbox. Future
isolation can transport the same serializable context/config/result contracts. Runtime
timeouts and resource limits, external plugins, workers, signatures, business detectors,
and production scheduling remain outside this decision.

See [Detector SDK](../DETECTOR-SDK.md) for lifecycle, policy examples, canonical ordering,
error semantics, security limits and authoring instructions. Business audit logic is
not part of this phase; Audit Rule Pack v1 is a subsequent milestone.
