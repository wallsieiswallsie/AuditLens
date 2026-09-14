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
    # Business policy uses the same exported snapshot, with no live source authority.
    from collections import Counter
    business_policy = policy_path.with_name('business-rulepack-v1.json')
    prior_runs = {p.name for p in (Path(directory) / 'runs').iterdir()}
    cli('run', '--snapshot', ids[0], '--policy', str(business_policy),
        env={**os.environ, 'AUDIT_SOURCE_DATABASE_URL': 'unusable', 'DATABASE_URL': 'unusable'})
    business_id = next(p.name for p in (Path(directory) / 'runs').iterdir() if p.name not in prior_runs)
    business = json.loads(cli('result', 'inspect', business_id))
    counts = Counter(row['reference'] for row in one.tables['invoices'] if row['reference'] not in (None, ''))
    expected = {ref: count for ref, count in counts.items() if count > 1}
    assert business['detector_id'] == 'business.duplicate_transaction_reference'
    # Existing fixture anomalies change both case and whitespace. This rule deliberately
    # does not trim, so those benchmark groups are not exact-reference duplicates.
    assert business['finding_count'] == len(expected)
    assert business['status'] == ('findings' if expected else 'passed')
    actual = {f['evidence'][0]['observed_value']: len(f['evidence']) for f in business['findings']}
    assert actual == expected
    for finding in business['findings']:
        ref = finding['evidence'][0]['observed_value']
        assert {e['source_record_id']['id'] for e in finding['evidence']} == {
            row['id'] for row in one.tables['invoices'] if row['reference'] == ref}
    completeness_policy = policy_path.with_name('missing-required-field.json')
    prior_runs = {p.name for p in (Path(directory) / 'runs').iterdir()}
    cli('run', '--snapshot', ids[0], '--policy', str(completeness_policy),
        env={**os.environ, 'AUDIT_SOURCE_DATABASE_URL': 'unusable', 'DATABASE_URL': 'unusable'})
    completeness_id = next(p.name for p in (Path(directory) / 'runs').iterdir() if p.name not in prior_runs)
    completeness = json.loads(cli('result', 'inspect', completeness_id))
    expected_missing = {row['id']: sorted(field for field in ('reference', 'vendor_id')
        if row[field] is None or row[field] == '') for row in one.tables['invoices']}
    expected_missing = {key: fields for key, fields in expected_missing.items() if fields}
    assert completeness['detector_id'] == 'business.missing_required_field'
    assert completeness['finding_count'] == len(expected_missing)
    assert completeness['status'] == ('findings' if expected_missing else 'passed')
    assert {f['entity_id']: [e['field'] for e in f['evidence']] for f in completeness['findings']} == expected_missing
    # Production-shaped references are strings, not numeric document sequences.
    # Check registration/policy/schema compatibility only; positive detection is offline.
    sequence_policy = policy_path.with_name('sequence-gap.json')
    sequence = json.loads(cli('detectors', 'inspect', 'business.sequence_gap'))
    assert sequence['detector_version'] == '1.0.0'
    cli('policy', 'validate', str(sequence_policy))
    from audit_engine.detectors import DEFAULT_DETECTORS, validate_policy, compatibility, resolve_requirements
    from audit_engine.policy import load_policy
    detector, config = validate_policy(load_policy(sequence_policy), DEFAULT_DETECTORS)[0]
    assert compatibility(one, resolve_requirements(detector, config)) is None
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
    print(json.dumps({'status': 'PASS', 'checks': 11, 'tables': 11,
                      'records': sum(one.snapshot.record_counts.values()),
                      'snapshot_hash': one.snapshot.snapshot_hash,
                      'coverage': 'reader CLI extraction twice, deterministic hashes, inspect, offline run/result, multi-detector policy run, business duplicate groups and record evidence, completeness records and fields, sequence registration/policy/schema compatibility only (positive sequence detection uses offline fixture), secret exclusion, tamper rejection'}))
