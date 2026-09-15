# Audit engine foundation

## Integrated Rule Pack v1

From repository root, validate `audit-engine/policies/rulepack-v1.json` using
`python -m audit_engine policy validate audit-engine/policies/rulepack-v1.json`.
The canonical policy selects all five existing business detectors in strict mode.
See [integration and controlled fixture](../docs/RULE-PACK-V1.md) and
[operations](../docs/PRODUCTION-RUNBOOK.md). The controlled baseline is five results,
six findings and nine evidence items. The current PostgreSQL dataset's text invoice
references deliberately fail integer sequence validation; this is not a complete
five-control business run on that source. No detector semantics were changed.

The local CLI creates deterministic PostgreSQL snapshots and executes policy-selected detectors against frozen context. The default remains framework.health; Audit Rule Pack v1 adds duplicate transaction reference, required-field completeness, sequence-gap, duplicate-payment and Decimal-only Tukey IQR amount-outlier detection. No source writes exist. Models, repositories and analyzers retain their existing package boundaries. See the [framework guide](../docs/AUDIT-FRAMEWORK.md) for contracts, connection setup, CLI commands, artifact integrity and limitations.

From this directory:
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m audit_engine
.venv\Scripts\python -m unittest discover -s tests
```

On macOS/Linux use .venv/bin/python instead. Python 3.11+ is required. Pandas remains declared in pyproject.toml; requirements.txt installs the package in editable mode. Extraction also requires root npm ci and Node on PATH, reusing pg without a new dependency. Framework serialization uses the standard library and exact decimal strings. No arguments preserves the original health CLI. See [architecture](../docs/03-SYSTEM-ARCHITECTURE.md).

## Audit Policy and Detector SDK

Framework 0.3.0 preserves snapshot artifacts and the no-argument/health CLI.
See [Detector SDK](../docs/DETECTOR-SDK.md) for policy, registry, authoring and limitations.
Run `python -m audit_engine detectors list` to inspect the explicit registry and
`python -m audit_engine policy validate audit-engine/policies/default.json` from the
repository root. `run --policy audit-engine/policies/examples.json --snapshot <id>`
executes both framework examples. See [Audit Rule Pack v1](../docs/AUDIT-RULE-PACK.md) for business policies and offline snapshot fixtures.
Tests use `python -m pytest audit-engine/tests -v`; install the optional `[test]` extra
if pytest is unavailable. Existing framework unittest tests remain supported.

## Amount outlier control

Validate `audit-engine/policies/amount-outlier.json` with the normal policy CLI. The
controlled snapshot is `00000000-0000-4000-a000-000000000500` under
`audit-engine/fixtures/amount-outlier`; it produces one upper payment outlier. See
[statistics, population semantics and runnable commands](../docs/AUDIT-RULE-PACK.md#statistical-control-businessamount_outlier).
Framework remains 0.3.0. The new detector is 1.0.0; dependencies are unchanged.
