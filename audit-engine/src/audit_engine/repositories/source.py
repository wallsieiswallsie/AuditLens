"""Fixed PostgreSQL transport. Never imported by the executor or detector."""
import json
from pathlib import Path
import subprocess
from decimal import Decimal
from audit_engine.models.contracts import SourceExtraction


def extract():
    try:
        result = subprocess.run(
            ['node', str(Path(__file__).with_name('extract.mjs'))],
            capture_output=True, timeout=180, check=True,
        )
        data = json.loads(result.stdout)
        for row in data['tables']['audit_logs']:
            for field in ('before_data', 'after_data'):
                if row[field] is not None:
                    row[field] = json.loads(row[field], parse_float=Decimal)
        return SourceExtraction(data['source_type'], data['schema_version'], data['tables'])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        raise ValueError('Source extraction failed; check connection and reader provisioning') from None
