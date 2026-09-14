# Audit engine foundation

The local CLI creates deterministic PostgreSQL snapshots and executes policy-selected detectors against frozen context. The default remains framework.health; Audit Rule Pack v1 adds duplicate transaction reference detection. No source writes exist. Models, repositories and analyzers retain their existing package boundaries. See the [framework guide](../docs/AUDIT-FRAMEWORK.md) for contracts, connection setup, CLI commands, artifact integrity and limitations.

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
executes both framework examples. See [Audit Rule Pack v1](../docs/AUDIT-RULE-PACK.md) for the business policy and offline snapshot fixture.
Tests use `python -m pytest audit-engine/tests -v`; install the optional `[test]` extra
if pytest is unavailable. Existing framework unittest tests remain supported.
