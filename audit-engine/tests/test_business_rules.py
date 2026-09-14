"""Business rule semantics through the unchanged snapshot and execution contracts."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from audit_engine.detectors import DEFAULT_DETECTORS, DetectorRegistry, resolve_config, validate_policy
from audit_engine.execution import execute_policy, logical_result
from audit_engine.models.contracts import SourceExtraction, RunStatus, ResultStatus
from audit_engine.policy import load_policy
from audit_engine.rules.duplicate_transaction_reference import DuplicateTransactionReferenceDetector
from audit_engine.snapshots import create_snapshot, load_snapshot

KEY = 'business.duplicate_transaction_reference'
ROOT = Path('audit-engine/fixtures/business-rulepack-v1')
SNAPSHOT_ID = '00000000-0000-4000-a000-000000000100'
POLICY_PATH = 'audit-engine/policies/business-rulepack-v1.json'


def policy(**config):
    p = load_policy(POLICY_PATH)
    return replace(p, detector_configuration={KEY: {**p.detector_configuration[KEY], **config}})


def extraction(references, reverse=False, offset=0):
    context = load_snapshot(SNAPSHOT_ID, ROOT)
    rows = [dict(context.tables['invoices'][0], id=f'00000000-0000-4000-a000-{i+offset:012d}', reference=value)
            for i, value in enumerate(references, 1)]
    if reverse:
        rows = [dict(reversed(list(row.items()))) for row in reversed(rows)]
    return SourceExtraction('postgresql', '1', {**context.tables, 'invoices': rows})


def run(root, references, config=None, reverse=False, offset=0, registry=None):
    snapshot = create_snapshot(extraction(references, reverse, offset), root)
    audit, results = execute_policy(snapshot.snapshot_id, root, operator=root.name,
                                   policy=policy(**(config or {})), registry=registry)
    logical = json.loads((root / 'runs' / audit.audit_run_id / 'logical-results.json').read_text())
    return audit, results[0], logical


@pytest.mark.parametrize('references,config,sizes', [
    (['INV-001', 'INV-002', 'INV-001'], {}, [2]),
    (['A', 'B', 'A', 'C', 'B'], {}, [2, 2]),
    (['A', 'A', 'A'], {}, [3]),
    (['A', 'B', 'C'], {}, []),
    ([None, '', None, ''], {}, []),
    (['INV-001', 'inv-001'], {'case_sensitive': False}, [2]),
    (['INV-001', 'inv-001'], {'case_sensitive': True}, []),
    (['Straße', 'STRASSE'], {'case_sensitive': False}, [2]),
    (['A', ' A', 'A ', ' ', ' '], {}, [2]),
    ([None, '', None, ''], {'ignore_empty': False}, [2, 2]),
    ([1, True, '1', 1, True], {}, [2, 2]),
    ([], {}, []),
])
def test_semantics(tmp_path, references, config, sizes):
    audit, result, _ = run(tmp_path, references, config)
    assert audit.status == RunStatus.COMPLETED
    assert result.finding_count == len(sizes)
    assert sorted(len(f.evidence) for f in result.findings) == sizes
    assert [f.entity_id for f in result.findings] == sorted(f.entity_id for f in result.findings)
    for finding in result.findings:
        assert finding.rule_id == 'DUPLICATE_TRANSACTION_REFERENCE'
        assert finding.severity.value == 'medium'
        assert [e.source_record_id['id'] for e in finding.evidence] == sorted(e.source_record_id['id'] for e in finding.evidence)
        for evidence in finding.evidence:
            assert evidence.source_table == 'invoices' and evidence.field == 'reference'
            assert evidence.observed_value == references[int(evidence.source_record_id['id'][-12:]) - 1]
            assert set(evidence.context) == {'comparison_value', 'group_size'}
            assert 'amount' not in evidence.to_json()


def test_reproducibility_and_minimal_evidence(tmp_path):
    refs = ['B', 'A', 'B', 'A', 'A']
    with patch.dict(os.environ, {'DATABASE_URL': 'secret-sentinel', 'AUDIT_SOURCE_DATABASE_URL': 'secret-sentinel'}):
        a, one, first = run(tmp_path / 'first', refs)
        with patch('audit_engine.execution.now', return_value='2030-01-01T00:00:00.000000Z'):
            b, two, second = run(tmp_path / 'second', refs, reverse=True)
    assert a.audit_run_id != b.audit_run_id and a.snapshot_id != b.snapshot_id
    assert one.started_at != two.started_at
    assert logical_result(one) == logical_result(two)
    assert first == second
    for path in tmp_path.rglob('*.json'):
        assert 'secret-sentinel' not in path.read_text()
    # Also exercise the detector directly: loader sorting must not conceal order bugs.
    d = DuplicateTransactionReferenceDetector()
    config = resolve_config(d.metadata(), policy().detector_configuration[KEY])
    context = load_snapshot(a.snapshot_id, tmp_path / 'first')
    shuffled = replace(context, tables=dict(reversed(list(context.tables.items()))))
    shuffled = replace(shuffled, tables={**shuffled.tables, 'invoices': tuple(reversed(shuffled.tables['invoices']))})
    assert d.analyze(context, config).to_json() == d.analyze(shuffled, config).to_json()


@pytest.mark.parametrize('config,reason', [({'table': 'absent'}, 'missing_table'),
    ({'reference_field': 'absent'}, 'missing_field'), ({'id_field': 'absent'}, 'missing_field')])
def test_missing_requirements_before_analyze(tmp_path, config, reason):
    with patch.object(DuplicateTransactionReferenceDetector, 'analyze', side_effect=AssertionError('must not execute')) as analyze:
        audit, result, _ = run(tmp_path, [], config)
    analyze.assert_not_called()
    assert audit.status == RunStatus.FAILED and result.status == ResultStatus.SKIPPED
    assert result.summary == reason


@pytest.mark.parametrize('config', [{'table': 123}, {'case_sensitive': 'false'}, {'id_field': ''},
    {'reference_field': 'bad field'}, {'table': []}, {'ignore_empty': 1}, {'unknown': True}])
def test_invalid_configuration_before_execution(tmp_path, config):
    snapshot = create_snapshot(extraction(['A', 'A']), tmp_path)
    with patch.object(DuplicateTransactionReferenceDetector, 'analyze') as analyze:
        with pytest.raises(ValueError):
            execute_policy(snapshot.snapshot_id, tmp_path, policy=policy(**config))
    analyze.assert_not_called()
    assert not (tmp_path / 'runs').exists()


def test_hash_relevant_mutations(tmp_path):
    class Variant(DuplicateTransactionReferenceDetector):
        release = '1.0.0'
        mutation = None
        def metadata(self):
            return replace(super().metadata(), detector_version=self.release)
        def analyze(self, context, config):
            result = super().analyze(context, config)
            f = result.findings[0]
            if self.mutation == 'finding':
                f = replace(f, description='Changed finding content')
            if self.mutation == 'evidence':
                f = replace(f, evidence=(replace(f.evidence[0], context={'changed': True}), *f.evidence[1:]))
            return replace(result, findings=(f,))
    d, hashes = Variant(), []
    variants = [(['A', 'A'], {}, 0, '1.0.0', None),
                (['B', 'B'], {}, 0, '1.0.0', None),
                (['A', 'A'], {}, 1, '1.0.0', None),
                (['A', 'A'], {'ignore_empty': False}, 0, '1.0.0', None),
                (['A', 'A'], {}, 0, '1.0.1', None),
                (['A', 'A'], {}, 0, '1.0.0', 'finding'),
                (['A', 'A'], {}, 0, '1.0.0', 'evidence')]
    for i, (refs, config, offset, d.release, d.mutation) in enumerate(variants):
        _, _, logical = run(tmp_path / str(i), refs, config, offset=offset, registry=DetectorRegistry([d]))
        hashes.append(logical['logical_result_hash'])
    assert len(set(hashes)) == len(variants)


@pytest.mark.parametrize('refs,config', [([{}, {}], {}), (['A', 'A'], {'id_field': 'reference'})])
def test_unsupported_values_are_sanitized_errors(tmp_path, refs, config):
    audit, result, _ = run(tmp_path, refs, config)
    assert audit.status == RunStatus.FAILED and result.summary == 'detector_error'


@pytest.mark.parametrize('refs,config,exit_code,count,reason', [
    (['A', 'A'], {}, 0, 1, None), (['A', 'B'], {}, 0, 0, None),
    (['A', 'A'], {'table': 123}, 1, None, None),
    (['A', 'A'], {'reference_field': 'absent'}, 1, 0, 'missing_field')])
def test_real_cli(tmp_path, refs, config, exit_code, count, reason):
    snapshot = create_snapshot(extraction(refs), tmp_path)
    path = tmp_path / 'policy.json'
    path.write_text(policy(**config).to_json())
    command = [sys.executable, '-m', 'audit_engine', '--artifacts-dir', str(tmp_path)]
    executed = subprocess.run([*command, 'run', '--snapshot', snapshot.snapshot_id, '--policy', str(path)],
                              capture_output=True, text=True, timeout=30)
    assert executed.returncode == exit_code
    if count is None:
        assert not (tmp_path / 'runs').exists()
        return
    run_id = next((tmp_path / 'runs').iterdir()).name
    inspected = subprocess.run([*command, 'result', 'inspect', run_id], capture_output=True, text=True, timeout=30)
    assert inspected.returncode == 0
    result = json.loads(inspected.stdout)
    assert result['finding_count'] == count
    if reason:
        assert result['summary'] == reason


def test_registration_defaults():
    d = DEFAULT_DETECTORS.get(KEY)
    metadata = d.metadata()
    assert metadata.detector_version == '1.0.0' and metadata.category == 'transaction_integrity'
    assert resolve_config(metadata, {}).values == dict(table='transactions', id_field='id',
        reference_field='reference_number', ignore_empty=True, case_sensitive=True)
    validate_policy(policy(), DEFAULT_DETECTORS)


def test_legacy_serialization_and_hashes_from_pre_rule_revision(tmp_path):
    from test_framework import sample
    from test_detector_sdk import Probe, policy as old_policy
    baseline = json.loads((ROOT / 'legacy-baseline.json').read_text())
    snapshot = create_snapshot(sample(), tmp_path)
    for name, p, registry in [('default', load_policy(), None),
        ('boolean', load_policy('audit-engine/policies/examples.json'), None),
        ('integer', old_policy(enabled_detectors=('example.probe',)), DetectorRegistry([Probe()]))]:
        audit, _ = execute_policy(snapshot.snapshot_id, tmp_path, policy=p, registry=registry)
        logical = json.loads((tmp_path / 'runs' / audit.audit_run_id / 'logical-results.json').read_text())
        assert p.to_json() == baseline[name]['policy_json']
        assert logical['logical_result_hash'] == baseline[name]['hash']
    assert resolve_config(Probe().metadata(), {}).to_json() == baseline['integer_config_json']


def test_reordered_cli_and_checked_in_result(tmp_path):
    expected = json.loads((ROOT / 'example-result.json').read_text())
    hashes = []
    for reverse in (False, True):
        root = tmp_path / str(reverse)
        snapshot = create_snapshot(extraction(['INV-001', 'INV-002', 'INV-001'], reverse), root)
        completed = subprocess.run([sys.executable, '-m', 'audit_engine', '--artifacts-dir', str(root),
            'run', '--snapshot', snapshot.snapshot_id, '--policy', POLICY_PATH], capture_output=True, timeout=30)
        assert completed.returncode == 0
        run_dir = next((root / 'runs').iterdir())
        logical = json.loads((run_dir / 'logical-results.json').read_text())
        hashes.append(logical['logical_result_hash'])
        from audit_engine.models.contracts import AuditResult
        result = AuditResult.from_json((root / 'results' / run_dir.name / (KEY + '.json')).read_bytes())
        assert logical_result(result) == logical_result(AuditResult.from_dict(expected))
    assert hashes[0] == hashes[1]
