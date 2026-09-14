"""Invoked ONLY by disposable PostgreSQL acceptance; no fixture/label imports."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from audit_engine.snapshots import load_snapshot


with tempfile.TemporaryDirectory(prefix='auditlens-framework-') as directory:
    def cli(*args, env=None):
        result = subprocess.run([sys.executable, '-m', 'audit_engine', '--artifacts-dir', directory, *args],
                                capture_output=True, text=True, timeout=180, env=env)
        if result.returncode:
            raise AssertionError('Framework acceptance CLI failed (output suppressed)')
        return result.stdout

    cli('snapshot')
    cli('snapshot')
    ids = [p.name for p in (Path(directory) / 'snapshots').iterdir()]
    one, two = [load_snapshot(i, directory) for i in ids]
    assert one.snapshot.snapshot_hash == two.snapshot.snapshot_hash
    assert len(one.tables) == 11
    assert sum(one.snapshot.record_counts.values()) > 0
    cli('snapshot', 'inspect', ids[0])
    # Run with deliberately invalid source settings: analysis must remain database-free.
    cli('run', '--snapshot', ids[0], env={**os.environ, 'AUDIT_SOURCE_DATABASE_URL': 'unusable', 'DATABASE_URL': 'unusable'})
    run_id = next((Path(directory) / 'runs').iterdir()).name
    result = json.loads(cli('result', 'inspect', run_id))
    assert result['status'] == 'passed' and result['finding_count'] == 0
    policy_path = Path(__file__).resolve().parents[1] / 'policies' / 'examples.json'
    cli('run', '--snapshot', ids[0], '--policy', str(policy_path),
        env={**os.environ, 'AUDIT_SOURCE_DATABASE_URL': 'unusable', 'DATABASE_URL': 'unusable'})
    multi_id = next(p.name for p in (Path(directory) / 'runs').iterdir() if p.name != run_id)
    results = json.loads(cli('result', 'inspect', multi_id))
    assert [r['detector_id'] for r in results] == ['framework.health', 'framework.snapshot_integrity']
    assert results[1]['finding_count'] == 1 and len(results[1]['findings'][0]['evidence']) == 11
    for path in Path(directory).rglob('*'):
        if path.is_file():
            content = path.read_text()
            for key in ('AUDIT_SOURCE_DATABASE_URL', 'DATABASE_URL'):
                value = os.environ.get(key)
                if value:
                    from urllib.parse import urlparse, unquote
                    url = urlparse(value)
                    assert value not in content
                    if url.password:
                        assert unquote(url.password) not in content
            assert 'groundTruth' not in content and 'anomaly_label' not in content
    file = Path(directory) / 'snapshots' / ids[0] / 'roles.jsonl'
    file.write_bytes(file.read_bytes().replace(b'code', b'CODE', 1))
    rejected = subprocess.run([sys.executable, '-m', 'audit_engine', '--artifacts-dir', directory,
                               'run', '--snapshot', ids[0]], capture_output=True, timeout=30)
    assert rejected.returncode != 0
    print(json.dumps({'status': 'PASS', 'checks': 8, 'tables': 11,
                      'records': sum(one.snapshot.record_counts.values()),
                      'snapshot_hash': one.snapshot.snapshot_hash,
                      'coverage': 'reader CLI extraction twice, deterministic hashes, inspect, offline run/result, multi-detector policy run, secret exclusion, tamper rejection'}))
