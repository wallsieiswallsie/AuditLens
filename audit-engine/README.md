# Audit engine foundation

Only a dependency-aware health CLI exists. No audit rules, database access or source writes are implemented. Future analyzers, rules, repositories and models have separate packages.

From this directory:
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m audit_engine
.venv\Scripts\python -m unittest discover -s tests
```

On macOS/Linux use .venv/bin/python instead. Python 3.11+ is required. Pandas is declared in pyproject.toml; requirements.txt installs the package in editable mode. Before implementing analysis, freeze dependency versions for reproducible evidence and avoid float conversion of monetary decimals. See [architecture](../docs/03-SYSTEM-ARCHITECTURE.md).

