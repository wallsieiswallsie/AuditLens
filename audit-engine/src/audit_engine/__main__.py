"""Run a dependency-aware health check without reading or changing data."""
import json
import pandas as pd

def health():
    return {"status": "ok", "service": "auditlens-engine", "pandas_version": pd.__version__}

def main():
    print(json.dumps(health()))

if __name__ == "__main__":
    main()

