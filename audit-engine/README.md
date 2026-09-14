# Audit engine foundation

The local CLI creates deterministic PostgreSQL snapshots and executes framework.health against frozen context. No business audit rules or source writes exist. Models, repositories and analyzers retain their existing package boundaries. See the [framework guide](../docs/AUDIT-FRAMEWORK.md) for contracts, connection setup, CLI commands, artifact integrity and limitations.

From this directory:
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m audit_engine
.venv\Scripts\python -m unittest discover -s tests
```

On macOS/Linux use .venv/bin/python instead. Python 3.11+ is required. Pandas remains declared in pyproject.toml; requirements.txt installs the package in editable mode. Extraction also requires root npm ci and Node on PATH, reusing pg without a new dependency. Framework serialization uses the standard library and exact decimal strings. No arguments preserves the original health CLI. See [architecture](../docs/03-SYSTEM-ARCHITECTURE.md).
