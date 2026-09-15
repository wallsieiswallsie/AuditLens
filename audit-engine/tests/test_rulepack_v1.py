"""Composition regressions; detector algorithms and legacy goldens live in their own suites."""
from dataclasses import replace
import json
from pathlib import Path
import random
import subprocess
import sys
from unittest.mock import patch

import pytest

from audit_engine.detectors import DEFAULT_DETECTORS, DetectorRegistry, validate_policy
from audit_engine.execution import execute_policy, logical_result
from audit_engine.models.contracts import SourceExtraction
from audit_engine.policy import load_policy
from audit_engine.rules.duplicate_payment import DuplicatePaymentDetector
from audit_engine.snapshots import SCHEMA, atomic_write, create_snapshot, load_snapshot

POLICY = Path('audit-engine/policies/rulepack-v1.json')
FIXTURE = Path('audit-engine/fixtures/rulepack-v1')
FIXTURE_ID = '00000000-0000-4000-a000-000000000600'
EXPECTED = {'business.amount_outlier': 1, 'business.duplicate_payment': 1,
            'business.duplicate_transaction_reference': 1,
            'business.missing_required_field': 2, 'business.sequence_gap': 1}
INDIVIDUAL = ['amount-outlier.json', 'duplicate-payment.json', 'business-rulepack-v1.json',
              'missing-required-field.json', 'sequence-gap.json']


def extraction(shuffle=False, changed=False):
    tables = {table: [] for table in SCHEMA}
    for i, ref in enumerate([1, 2, 2, 4, None], 1):
        row = dict.fromkeys(SCHEMA['invoices'])
        row.update(id=f'00000000-0000-4000-a000-{i:012d}', reference=ref,
                   vendor_id=None if i == 4 else 'vendor', amount='10.00')
        tables['invoices'].append(row)
    for i, amount in enumerate(['10', '10', '11', '12', '13', '14', '15', '101' if changed else '100'], 1):
        row = dict.fromkeys(SCHEMA['payments'])
        row.update(id=f'00000000-0000-4000-a000-{i+100:012d}', amount=amount,
                   invoice_id='invoice', reference='payment', currency='IDR')
        tables['payments'].append(row)
    if shuffle:
        rng = random.Random(42)
        for rows in tables.values():
            rng.shuffle(rows)
            for i, row in enumerate(rows):
                rows[i] = dict(reversed(list(row.items())))
        tables = dict(reversed(list(tables.items())))
    return SourceExtraction('postgresql', '1', tables)


def run(root, policy=None, registry=None, **kwargs):
    s = create_snapshot(extraction(**kwargs), root)
    a, results = execute_policy(s.snapshot_id, root, operator=root.name,
                                policy=policy or load_policy(POLICY), registry=registry)
    logical = json.loads((root / 'runs' / a.audit_run_id / 'logical-results.json').read_text())
    return a, results, logical


def test_policy_fixture_and_counts(tmp_path):
    p = load_policy(POLICY)
    assert p.policy_id == 'business.rulepack.v1'
    assert p.fail_on_detector_error and not p.allow_partial_results
    assert {d.metadata().detector_id for d, _ in validate_policy(p, DEFAULT_DETECTORS)} == set(EXPECTED)
    for name in INDIVIDUAL:
        old = load_policy(POLICY.with_name(name))
        for key, config in old.detector_configuration.items():
            assert p.detector_configuration[key] == config
    c = load_snapshot(FIXTURE_ID, FIXTURE)
    assert len(c.tables) == 11 and sum(c.snapshot.record_counts.values()) == 13
    a, results, logical = run(tmp_path)
    assert a.status.value == 'completed'
    assert [r.detector_id for r in results] == sorted(EXPECTED)
    assert {r.detector_id: r.finding_count for r in results} == EXPECTED
    assert len(results) == 5 and sum(r.finding_count for r in results) == 6
    assert sum(len(f.evidence) for r in results for f in r.findings) == 9
    assert logical['logical_result_hash'] == json.loads((FIXTURE / 'logical-baseline.json').read_text())['hash']
    assert c.snapshot.snapshot_hash == a.snapshot_hash


def test_isolation_and_order_invariance(tmp_path):
    a, results, logical = run(tmp_path / 'first')
    b, reordered, second = run(tmp_path / 'second', shuffle=True)
    assert a.audit_run_id != b.audit_run_id and a.snapshot_id != b.snapshot_id
    assert a.created_at != b.created_at
    assert logical == second
    assert [logical_result(r) for r in results] == [logical_result(r) for r in reordered]
    c = load_snapshot(a.snapshot_id, tmp_path / 'first')
    before = c.to_json() if hasattr(c, 'to_json') else repr(c)
    # Execute each control alone on exactly the same snapshot and compare all findings/evidence.
    for name in INDIVIDUAL:
        _, alone = execute_policy(a.snapshot_id, tmp_path / 'first', policy=load_policy(POLICY.with_name(name)))
        assert logical_result(alone[0]) == logical_result(next(r for r in results if r.detector_id == alone[0].detector_id))
    assert (c.to_json() if hasattr(c, 'to_json') else repr(c)) == before
    # Bypass canonical source acquisition to exercise shared frozen context row ordering too.
    shuffled = replace(c, tables={k: [dict(reversed(list(r.items()))) for r in reversed(rows)] for k, rows in c.tables.items()})
    before_shared = repr(shuffled)
    reordered_policy = json.loads(load_policy(POLICY).to_json(), object_pairs_hook=lambda pairs: dict(reversed(pairs)))
    policy_path = tmp_path / 'reordered-policy.json'
    policy_path.write_text(json.dumps(reordered_policy))
    with patch('audit_engine.execution.load_snapshot', return_value=shuffled):
        direct_run, direct = execute_policy(a.snapshot_id, tmp_path / 'first', policy=load_policy(policy_path))
    assert repr(shuffled) == before_shared
    assert [logical_result(r) for r in direct] == [logical_result(r) for r in results]
    assert json.loads((tmp_path / 'first' / 'runs' / direct_run.audit_run_id / 'logical-results.json').read_text()) == logical


@pytest.mark.parametrize('partial', [False, True])
@pytest.mark.parametrize('failure', ['exception', 'missing_field'])
def test_failure_artifacts(tmp_path, partial, failure):
    p = replace(load_policy(POLICY), fail_on_detector_error=not partial, allow_partial_results=partial)
    if failure == 'missing_field':
        configs = {k: dict(v) for k, v in p.detector_configuration.items()}
        configs['business.duplicate_payment']['id_field'] = 'absent'
        p = replace(p, detector_configuration=configs)
    with patch.object(DuplicatePaymentDetector, 'analyze', side_effect=ValueError('secret-sentinel')):
        a, results, _ = run(tmp_path, p)
    assert a.status.value == 'failed' and results[0].finding_count == 1
    assert results[1].summary == ('detector_error' if failure == 'exception' else 'missing_field')
    assert results[1].status.value == ('error' if failure == 'exception' else 'skipped')
    assert all(r.status.value == ('findings' if partial else 'skipped') for r in results[2:])
    if not partial:
        assert all(r.summary == 'strict_failure' for r in results[2:])
    for path in (tmp_path / 'runs' / a.audit_run_id).glob('*.json'):
        assert 'secret-sentinel' not in path.read_text()
    assert len(list((tmp_path / 'results' / a.audit_run_id).glob('*.json'))) == 5
    assert json.loads((tmp_path / 'runs' / a.audit_run_id / 'run.json').read_text())['status'] == 'failed'


def test_artifacts_no_clobber(tmp_path):
    a, results, logical = run(tmp_path)
    directory = tmp_path / 'runs' / a.audit_run_id
    assert {p.name for p in directory.iterdir()} == {'run.json', 'policy.json', 'provenance.json', 'logical-results.json'}
    p = json.loads((directory / 'policy.json').read_text())
    assert p['policy_id'] == 'business.rulepack.v1' and p['policy_version'] == 'auditlens-policy-v1'
    metadata = json.loads((directory / 'run.json').read_text())
    assert metadata['detector_versions'] == {k: '1.0.0' for k in EXPECTED}
    assert metadata['detector_configuration'] == {r.detector_id: r.to_dict()['detector_configuration'] for r in results}
    provenance = json.loads((directory / 'provenance.json').read_text())
    assert provenance['snapshot_hash'] == metadata['snapshot_hash'] == logical['content']['snapshot_hash']
    assert provenance['snapshot_id'] == a.snapshot_id and provenance['policy_version'] == p['policy_version']
    assert metadata['status'] == 'completed'
    for path in [*directory.glob('*.json'), *(tmp_path / 'results' / a.audit_run_id).glob('*.json')]:
        original = path.read_bytes()
        with pytest.raises(FileExistsError):
            atomic_write(path, b'overwrite')
        assert path.read_bytes() == original
    with patch('audit_engine.execution.uuid4', return_value=a.audit_run_id):
        with pytest.raises(FileExistsError):
            execute_policy(a.snapshot_id, tmp_path, policy=load_policy(POLICY))
    assert not list(tmp_path.rglob('.pending-*'))


def test_hash_sensitivity(tmp_path):
    class Variant(DuplicatePaymentDetector):
        release = '1.0.0'
        mutation = None
        def metadata(self):
            return replace(super().metadata(), detector_version=self.release)
        def analyze(self, context, config):
            result = super().analyze(context, config)
            f = result.findings[0]
            if self.mutation == 'finding':
                f = replace(f, description='Changed finding')
            if self.mutation == 'evidence':
                f = replace(f, evidence=(replace(f.evidence[0], context={'changed': True}), *f.evidence[1:]))
            return replace(result, findings=(f,))
    variant = Variant()
    hashes = []
    for case in ['baseline', 'source', 'config', 'version', 'finding', 'evidence']:
        variant.release = '1.0.1' if case == 'version' else '1.0.0'
        variant.mutation = case
        p = load_policy(POLICY)
        if case == 'config':
            configs = {k: dict(v) for k, v in p.detector_configuration.items()}
            configs['business.amount_outlier']['iqr_multiplier'] = '2'
            p = replace(p, detector_configuration=configs)
        registry = DetectorRegistry([variant if k == 'business.duplicate_payment' else DEFAULT_DETECTORS.get(k) for k in EXPECTED])
        _, _, logical = run(tmp_path / case, p, registry, changed=case == 'source')
        hashes.append(logical['logical_result_hash'])
    assert len(set(hashes)) == 6


def test_cli(tmp_path):
    command = [sys.executable, '-m', 'audit_engine', '--artifacts-dir', str(tmp_path)]
    for args in [[], ['health'], ['detectors', 'list'], ['policy', 'validate', str(POLICY)]]:
        assert subprocess.run([*command, *args], capture_output=True, timeout=30).returncode == 0
    s = create_snapshot(extraction(shuffle=True), tmp_path)
    readiness = [sys.executable, 'scripts/audit-readiness.py', '--artifacts-dir', str(tmp_path), '--snapshot']
    assert subprocess.run([*readiness, s.snapshot_id], capture_output=True, timeout=30).returncode == 0
    assert subprocess.run([*readiness, 'invalid'], capture_output=True, timeout=30).returncode == 1
    assert not list(tmp_path.glob('.readiness-*'))
    for args in [['snapshot', 'inspect', s.snapshot_id], ['run', '--snapshot', s.snapshot_id, '--policy', str(POLICY)]]:
        assert subprocess.run([*command, *args], capture_output=True, timeout=30).returncode == 0
    run_id = next((tmp_path / 'runs').iterdir()).name
    inspected = subprocess.run([*command, 'result', 'inspect', run_id], capture_output=True, timeout=30)
    assert inspected.returncode == 0
    assert {r['detector_id']: r['finding_count'] for r in json.loads(inspected.stdout)} == EXPECTED
