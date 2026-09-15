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
    # Payments have an actual obligation, amount/currency and payment reference.
    payment_policy = policy_path.with_name('duplicate-payment.json')
    payment_metadata = json.loads(cli('detectors', 'inspect', 'business.duplicate_payment'))
    assert payment_metadata['detector_version'] == '1.0.0'
    cli('policy', 'validate', str(payment_policy))
    detector, config = validate_policy(load_policy(payment_policy), DEFAULT_DETECTORS)[0]
    assert compatibility(one, resolve_requirements(detector, config)) is None
    fields = config.values['match_fields']
    from audit_engine.execution import canonical_json
    expected_payments = {}
    for row in one.tables['payments']:
        values = [row[field] for field in fields]
        if any(value is None or value == '' for value in values):
            continue
        expected_payments.setdefault(canonical_json(values), set()).add(row['id'])
    expected_payments = {key: ids for key, ids in expected_payments.items() if len(ids) > 1}
    prior_runs = {p.name for p in (Path(directory) / 'runs').iterdir()}
    cli('run', '--snapshot', ids[0], '--policy', str(payment_policy),
        env={**os.environ, 'AUDIT_SOURCE_DATABASE_URL': 'unusable', 'DATABASE_URL': 'unusable'})
    payment_run = next(p.name for p in (Path(directory) / 'runs').iterdir() if p.name not in prior_runs)
    payment = json.loads(cli('result', 'inspect', payment_run))
    assert payment['detector_id'] == 'business.duplicate_payment'
    assert payment['finding_count'] == len(expected_payments)
    assert payment['status'] == ('findings' if expected_payments else 'passed')
    assert {canonical_json(f['evidence'][0]['context']['normalized_match_values']):
            {e['source_record_id']['id'] for e in f['evidence']} for f in payment['findings']} == expected_payments
    # Inspect the actual monetary population; currency is an approved payment
    # dimension. Default 1.5 multiplier is never tuned to manufacture findings.
    from decimal import Decimal, localcontext
    amount_policy = policy_path.with_name('amount-outlier.json')
    cli('policy', 'validate', str(amount_policy))
    populations = {}
    for row in one.tables['payments']:
        assert type(row['amount']) is str
        populations.setdefault(row['currency'], []).append(row)
    eligible_groups = sum(len(rows) >= 8 for rows in populations.values())
    expected_outliers = set()
    with localcontext() as decimal_context:
        decimal_context.prec = 80  # Actual source NUMERIC(18,2), multiplier 1.5.
        for rows in populations.values():
            if len(rows) < 8:
                continue
            values = sorted(Decimal(row['amount']) for row in rows)
            middle = len(values) // 2
            halves = (values[:middle], values[middle + len(values) % 2:])
            q1, q3 = [half[len(half)//2] if len(half) % 2 else
                      (half[len(half)//2 - 1] + half[len(half)//2]) / Decimal(2) for half in halves]
            if q3 == q1:
                continue
            upper = q3 + Decimal('1.5') * (q3 - q1)
            expected_outliers.update(row['id'] for row in rows if Decimal(row['amount']) > upper)
    prior_runs = {p.name for p in (Path(directory) / 'runs').iterdir()}
    cli('run', '--snapshot', ids[0], '--policy', str(amount_policy),
        env={**os.environ, 'AUDIT_SOURCE_DATABASE_URL': 'unusable', 'DATABASE_URL': 'unusable'})
    amount_run = next(p.name for p in (Path(directory) / 'runs').iterdir() if p.name not in prior_runs)
    amount_result = json.loads(cli('result', 'inspect', amount_run))
    assert amount_result['detector_id'] == 'business.amount_outlier'
    assert amount_result['status'] == ('findings' if expected_outliers else 'passed')
    assert {f['entity_id'] for f in amount_result['findings']} == expected_outliers
    assert amount_result['finding_count'] == len(expected_outliers)
    for f in amount_result['findings']:
        assert len(f['evidence']) == 1
        evidence = f['evidence'][0]
        assert evidence['source_record_id'] == {'id': f['entity_id']}
        row = next(row for row in one.tables['payments'] if row['id'] == f['entity_id'])
        assert evidence['observed_value'] == row['amount']
        assert evidence['context']['group_values'] == [row['currency']]
    # The canonical pack retains the approved integer-reference configuration.
    # The real dataset has text references: all four compatible controls execute,
    # then sequence fails closed. Never coerce source data or claim a complete run.
    from audit_engine.execution import execute_policy, logical_result
    pack = load_policy(policy_path.with_name('rulepack-v1.json'))
    integrated_run, integrated = execute_policy(ids[0], directory, policy=pack)
    assert integrated_run.status.value == 'failed'
    expected_individual = {r['detector_id']: r for r in [business, completeness, payment, amount_result]}
    from audit_engine.models.contracts import AuditResult, SourceExtraction
    for r in integrated:
        if r.detector_id in expected_individual:
            assert logical_result(r) == logical_result(AuditResult.from_json(json.dumps(expected_individual[r.detector_id])))
        else:
            assert r.detector_id == 'business.sequence_gap' and r.summary == 'detector_error'
    integrated_report = {r.detector_id: {
        'input_records': len(one.tables[pack.detector_configuration[r.detector_id]['table']]),
        'evaluated_population': None if r.summary == 'detector_error' else len(one.tables[pack.detector_configuration[r.detector_id]['table']]),
        'finding_count': r.finding_count, 'status': r.status.value, 'summary': r.summary
    } for r in integrated}
    # Safe positive end-to-end run in this same process/environment, using the
    # committed approved-format fixture. It does not write to PostgreSQL.
    from audit_engine.snapshots import create_snapshot
    fixture_root = Path(__file__).resolve().parents[1] / 'fixtures/rulepack-v1'
    controlled = load_snapshot('00000000-0000-4000-a000-000000000600', fixture_root)
    controlled_snapshot = create_snapshot(SourceExtraction('postgresql', '1', controlled.tables), directory)
    controlled_run, controlled_results = execute_policy(controlled_snapshot.snapshot_id, directory, policy=pack)
    assert controlled_run.status.value == 'completed'
    baseline = json.loads((fixture_root / 'logical-baseline.json').read_text())
    assert {r.detector_id: r.finding_count for r in controlled_results} == baseline['findings']
    assert json.loads((Path(directory) / 'runs' / controlled_run.audit_run_id / 'logical-results.json').read_text())['logical_result_hash'] == baseline['hash']
    assert len(json.loads(cli('result', 'inspect', controlled_run.audit_run_id))) == 5
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
    print(json.dumps({'status': 'PASS', 'checks': 15, 'tables': 11,
                      'rulepack_v1': {'source_run_status': integrated_run.status.value,
                          'detectors': integrated_report, 'controlled_run_status': controlled_run.status.value,
                          'controlled_logical_hash': baseline['hash']},
                      'records': sum(one.snapshot.record_counts.values()),
                      'duplicate_payment_findings': payment['finding_count'],
                      'payment_match_fields': list(fields),
                      'amount_outlier': {'records_evaluated': len(one.tables['payments']),
                          'eligible_records': sum(len(rows) for rows in populations.values()),
                          'groups': len(populations), 'groups_meeting_minimum_sample_size': eligible_groups,
                          'findings': amount_result['finding_count'], 'group_by_fields': ['currency'], 'iqr_multiplier': '1.5'},
                      'snapshot_hash': one.snapshot.snapshot_hash,
                      'coverage': 'reader CLI extraction twice, deterministic hashes, inspect, offline run/result, multi-detector policy run, business duplicate groups and record evidence, completeness records and fields, sequence registration/policy/schema compatibility only (positive sequence detection uses offline fixture), payment registration/policy/schema/execution and exact group evidence, secret exclusion, tamper rejection'}))
