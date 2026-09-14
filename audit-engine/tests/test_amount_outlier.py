"""Exact statistics, population semantics, CLI and compatibility regressions."""
from dataclasses import replace
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from audit_engine.detectors import DEFAULT_DETECTORS, DetectorRegistry, resolve_config
from audit_engine.execution import execute_policy, logical_result
from audit_engine.models.contracts import AuditResult, SourceExtraction
from audit_engine.policy import load_policy
from audit_engine.rules.amount_outlier import AmountOutlierDetector, decimal_string, parse_amount, quartiles
from audit_engine.snapshots import create_snapshot, load_snapshot, SCHEMA

KEY = 'business.amount_outlier'
POLICY = 'audit-engine/policies/amount-outlier.json'
FIXTURE = Path('audit-engine/fixtures/amount-outlier')
FIXTURE_ID = '00000000-0000-4000-a000-000000000500'
BASE = ['10', '11', '12', '13', '14', '15', '16', '100']


def policy(**config):
    p = load_policy(POLICY)
    return replace(p, detector_configuration={KEY: {**p.detector_configuration[KEY], **config}})


def extraction(values=BASE, groups=None, reverse=False, offset=0, alternate=False):
    rows = []
    for i, value in enumerate(values, 1):
        row = dict.fromkeys(SCHEMA['payments'])
        row.update(id=f'00000000-0000-4000-a000-{i+offset:012d}', amount='1.00' if alternate else value,
                   reference=value if alternate else 'P', currency='IDR', invoice_id='I', status='pending')
        if groups is not None:
            row.update(groups[i - 1])
        rows.append(row)
    if reverse:
        rows = [dict(reversed(list(row.items()))) for row in reversed(rows)]
    return SourceExtraction('postgresql', '1', {table: rows if table == 'payments' else [] for table in SCHEMA})


def run(root, values=BASE, config=None, registry=None, **kwargs):
    s = create_snapshot(extraction(values, **kwargs), root)
    a, results = execute_policy(s.snapshot_id, root, operator=root.name, policy=policy(**(config or {})), registry=registry)
    logical = json.loads((root / 'runs' / a.audit_run_id / 'logical-results.json').read_text())
    return a, results[0], logical


@pytest.mark.parametrize('values,expected', [
    ([str(i) for i in range(1, 9)], ('2.5', '6.5')),
    ([str(i) for i in range(1, 10)], ('2.5', '7.5')),
    ([str(i) for i in range(1, 8)], ('2', '6')),
    (['0.10', '0.20', '0.30', '0.40'], ('0.15', '0.35')),
    (['0.01', '0.02', '0.03', '0.04'], ('0.015', '0.035'))])
def test_exact_quartiles(values, expected):
    assert quartiles(list(map(Decimal, values))) == tuple(map(Decimal, expected))


@pytest.mark.parametrize('value,expected', [('100.00', '100.00'), ('2.5', '2.50'),
    ('0.0150', '0.015'), ('-0.000', '0.00'), ('1E+30', '1000000000000000000000000000000.00'),
    ('0.300000000000000000000000000001', '0.300000000000000000000000000001')])
def test_decimal_serializer(value, expected):
    assert decimal_string(Decimal(value)) == expected


@pytest.mark.parametrize('values,config,count,direction', [
    (BASE, {}, 1, 'upper'),
    ([str(i) for i in range(10, 20)] + ['100', '200'], {}, 2, 'upper'),
    (['-100', '10', '11', '12', '13', '14', '15', '16'], {'detect_lower_outliers': True}, 1, 'lower'),
    (['-100', '10', '11', '12', '13', '14', '15', '16'], {}, 0, None),
    (['-100', '10', '11', '12', '13', '14', '15', '16'], {'detect_lower_outliers': True, 'detect_upper_outliers': False}, 1, 'lower'),
    (BASE[:6] + ['100'], {}, 0, None), (BASE, {}, 1, 'upper'),
    (['100'] * 8, {}, 0, None), (['100'] * 7 + ['1000'], {}, 0, None),
    ([], {}, 0, None),
    (['-2', '1', '1', '2', '3', '3', '3', '6'], {'detect_lower_outliers': True}, 0, None),
    (['-2.01', '1', '1', '2', '3', '3', '3', '6.01'], {'detect_lower_outliers': True}, 2, None),
    (['0'] + BASE, {'detect_lower_outliers': True}, 2, None),
    (['0'] + BASE, {'detect_lower_outliers': True, 'ignore_zero': True}, 1, 'upper'),
    (['-100'] + BASE, {'detect_lower_outliers': True}, 2, None),
    (['-100'] + BASE, {'detect_lower_outliers': True, 'ignore_negative': True}, 1, 'upper')])
def test_populations(tmp_path, values, config, count, direction):
    a, r, _ = run(tmp_path, values, config)
    assert a.status.value == 'completed' and r.finding_count == count
    for f in r.findings:
        assert f.rule_id == 'AMOUNT_OUTLIER' and f.severity.value == 'medium'
        assert f.entity_type == 'payments' and len(f.evidence) == 1
        e = f.evidence[0]
        assert e.source_record_id == {'id': f.entity_id} and e.field == 'amount'
        assert e.observed_value == e.context['amount']
        assert set(e.context) == {'amount_field', 'amount', 'direction', 'q1', 'q3', 'iqr',
            'iqr_multiplier', 'lower_fence', 'upper_fence', 'sample_size', 'group_by_fields', 'group_values'}
        assert 'status' not in e.to_json() and 'created_by' not in e.to_json()
        if direction:
            assert e.context['direction'] == direction


def test_exact_fences_and_sample(tmp_path):
    _, r, _ = run(tmp_path)
    c = r.findings[0].evidence[0].context
    assert {k: c[k] for k in ('q1', 'q3', 'iqr', 'lower_fence', 'upper_fence', 'sample_size')} == {
        'q1': '11.50', 'q3': '15.50', 'iqr': '4.00', 'lower_fence': '5.50', 'upper_fence': '21.50', 'sample_size': 8}
    for key in ('ignore_zero', 'ignore_negative'):
        values = ['0' if key == 'ignore_zero' else '-100'] + BASE
        for ignore in (False, True):
            _, result, _ = run(tmp_path / (key + str(ignore)), values, {key: ignore})
            assert result.findings[0].evidence[0].context['sample_size'] == (8 if ignore else 9)


def test_null_and_exact_zero(tmp_path):
    # Approved payments.amount is non-null/fixed-cent. A configurable text field
    # exercises nullable/high-precision inputs without weakening snapshot validation.
    _, r, _ = run(tmp_path, [None, '0', '0.01', '-0.01'] + BASE,
                  {'amount_field': 'reference', 'ignore_zero': True}, alternate=True)
    assert r.findings[-1].evidence[0].context['sample_size'] == 10
    assert all(f.evidence[0].observed_value is not None for f in r.findings)


@pytest.mark.parametrize('fields', [[], ['currency'], ['currency', 'invoice_id']])
def test_grouping(tmp_path, fields):
    values = BASE + [str(Decimal(v) * 1000) for v in BASE]
    groups = [{'currency': 'IDR', 'invoice_id': 'I1'}] * 8 + [
        {'currency': 'USD' if len(fields) < 2 else 'IDR', 'invoice_id': 'I2'}] * 8
    _, r, _ = run(tmp_path, values, {'group_by_fields': fields}, groups=groups)
    assert r.finding_count == (1 if not fields else 2)
    if fields:
        assert [f.evidence[0].context['sample_size'] for f in r.findings] == [8, 8]
        assert [f.evidence[0].context['q1'] for f in r.findings] == ['11.50', '11500.00']


def test_typed_empty_groups_and_per_group_minimum(tmp_path):
    keys = [None, '', 0, False, '0', {'b': 2, 'a': 1}, [1, True]]
    groups = [{'currency': key} for key in keys for _ in BASE]
    _, r, _ = run(tmp_path, BASE * len(keys), groups=groups)
    assert r.finding_count == len(keys)
    assert all(f.evidence[0].context['sample_size'] == 8 for f in r.findings)
    _, r, _ = run(tmp_path / 'short', BASE + BASE[:7], groups=[{'currency': 'A'}] * 8 + [{'currency': 'B'}] * 7)
    assert r.finding_count == 1


@pytest.mark.parametrize('value', ['abc', 'NaN', 'Infinity', '-Infinity', True, False, [], {},
    '1e2', '1,5', ' 1', '1 ', '+1', '01', 1, 'secret-sentinel'])
def test_invalid_amount_sanitized(tmp_path, value):
    a, r, _ = run(tmp_path, BASE + [value], {'amount_field': 'reference', 'minimum_sample_size': 100}, alternate=True)
    assert a.status.value == 'failed' and r.summary == 'detector_error' and not r.findings
    assert 'secret-sentinel' not in r.to_json()


@pytest.mark.parametrize('config', [{'table': 1}, {'amount_field': []}, {'group_by_fields': 'currency'},
    {'group_by_fields': [1]}, {'group_by_fields': ['currency', 'currency']}, {'group_by_fields': ['bad name']},
    {'iqr_multiplier': 'NaN'}, {'iqr_multiplier': 'Infinity'}, {'iqr_multiplier': '-Infinity'},
    {'iqr_multiplier': '1e2'}, {'iqr_multiplier': '1,5'}, {'iqr_multiplier': '1.50'}, {'iqr_multiplier': 1},
    {'iqr_multiplier': '0'}, {'iqr_multiplier': '-1'}, {'minimum_sample_size': 3}, {'minimum_sample_size': True},
    {'detect_lower_outliers': False, 'detect_upper_outliers': False}, {'detect_lower_outliers': 1},
    {'detect_upper_outliers': 'true'}, {'ignore_zero': 0}, {'ignore_negative': 'false'}, {'unknown': True}])
def test_invalid_config_before_analysis(tmp_path, config):
    s = create_snapshot(extraction(), tmp_path)
    with patch.object(AmountOutlierDetector, 'analyze') as analyze:
        for _ in range(2):
            with pytest.raises(ValueError):
                execute_policy(s.snapshot_id, tmp_path, policy=policy(**config))
    analyze.assert_not_called()
    assert not (tmp_path / 'runs').exists()


@pytest.mark.parametrize('config,reason', [({'table': 'absent'}, 'missing_table'),
    ({'id_field': 'absent'}, 'missing_field'), ({'amount_field': 'absent'}, 'missing_field'),
    ({'group_by_fields': ['vendor_id']}, 'missing_field')])
@pytest.mark.parametrize('values', [[], BASE])
def test_requirements(tmp_path, config, reason, values):
    with patch.object(AmountOutlierDetector, 'analyze') as analyze:
        a, r, _ = run(tmp_path, values, config)
    analyze.assert_not_called()
    assert a.status.value == 'failed' and r.summary == reason and not r.findings


def test_precision_and_hostile_decimal_context(tmp_path):
    values = ['0.10', '0.20', '0.30', '0.40', '0.50', '0.60', '0.70', '999999999999999999.99']
    a, result, _ = run(tmp_path, values)
    assert a.status.value == 'completed'
    c = result.findings[0].evidence[0].context
    assert (c['q1'], c['q3'], c['iqr'], c['upper_fence']) == ('0.25', '0.65', '0.40', '1.25')
    assert c['amount'] == '999999999999999999.99'
    precise = ['0.' + '0' * 35 + str(i) for i in range(1, 8)] + ['999999999999999999.99']
    _, first, _ = run(tmp_path / 'precise', precise, {'amount_field': 'reference'}, alternate=True)
    context = load_snapshot(first.snapshot_id, tmp_path / 'precise')
    d = AmountOutlierDetector(); config = resolve_config(d.metadata(), policy(amount_field='reference').detector_configuration[KEY])
    normal = d.analyze(context, config)
    with localcontext() as dc:
        dc.prec = 3; dc.rounding = ROUND_DOWN; dc.Emax = 4; dc.Emin = -4; dc.traps[Inexact] = True
        assert d.analyze(context, config).to_json() == normal.to_json()
        assert decimal_string(Decimal('100.00100')) == '100.001'
    assert first.findings[0].evidence[0].context['q1'] == '0.' + '0' * 35 + '25'


def test_reproducibility_and_secrets(tmp_path):
    with patch.dict(os.environ, {'DATABASE_URL': 'secret-sentinel', 'AUDIT_SOURCE_DATABASE_URL': 'secret-sentinel'}):
        a, one, first = run(tmp_path / 'first')
        with patch('audit_engine.execution.now', return_value='2030-01-01T00:00:00.000000Z'), patch(
                'audit_engine.snapshots.now', return_value='2030-01-01T00:00:00.000000Z'):
            b, two, second = run(tmp_path / 'second', reverse=True)
    assert a.audit_run_id != b.audit_run_id and a.snapshot_id != b.snapshot_id
    assert one.started_at != two.started_at and logical_result(one) == logical_result(two) and first == second
    d = AmountOutlierDetector(); c = load_snapshot(a.snapshot_id, tmp_path / 'first')
    config = resolve_config(d.metadata(), policy().detector_configuration[KEY])
    shuffled = replace(c, tables={k: [dict(reversed(list(r.items()))) for r in reversed(rows)] for k, rows in reversed(list(c.tables.items()))})
    assert d.analyze(c, config).to_json() == d.analyze(shuffled, config).to_json()
    for path in tmp_path.rglob('*.json'):
        assert 'secret-sentinel' not in path.read_text()


def test_hash_sensitivity(tmp_path):
    class Variant(AmountOutlierDetector):
        release = '1.0.0'
        mutation = None
        def metadata(self):
            return replace(super().metadata(), detector_version=self.release)
        def analyze(self, context, config):
            r = super().analyze(context, config); f = r.findings[0]
            if self.mutation == 'finding':
                f = replace(f, description='Changed content')
            if self.mutation == 'evidence':
                f = replace(f, evidence=(replace(f.evidence[0], context={'changed': True}),))
            return replace(r, findings=(f,))
    d = Variant(); hashes = []
    cases = [(BASE, {}, 0, '1.0.0', None), (BASE[:-1] + ['101'], {}, 0, '1.0.0', None),
        (BASE, {}, 10, '1.0.0', None), (BASE, {'group_by_fields': []}, 0, '1.0.0', None),
        (BASE, {'iqr_multiplier': '2'}, 0, '1.0.0', None), (BASE, {'minimum_sample_size': 7}, 0, '1.0.0', None),
        (BASE, {'ignore_zero': True}, 0, '1.0.0', None), (BASE, {'ignore_negative': True}, 0, '1.0.0', None),
        (BASE, {'detect_lower_outliers': True}, 0, '1.0.0', None),
        (BASE, {}, 0, '1.0.1', None), (BASE, {}, 0, '1.0.0', 'finding'), (BASE, {}, 0, '1.0.0', 'evidence')]
    for i, (values, config, offset, d.release, d.mutation) in enumerate(cases):
        _, _, logical = run(tmp_path / str(i), values, config, offset=offset, registry=DetectorRegistry([d]))
        hashes.append(logical['logical_result_hash'])
    assert len(set(hashes)) == len(hashes)
    _, _, lower_only = run(tmp_path / 'lower', config={'detect_lower_outliers': True, 'detect_upper_outliers': False})
    assert lower_only['logical_result_hash'] not in hashes


@pytest.mark.parametrize('values,config,count,alternate,reverse', [
    (BASE, {}, 1, False, False), (BASE, {}, 1, False, True),
    (['-100'] + BASE[1:], {'detect_lower_outliers': True}, 2, False, False),
    (BASE[:7], {}, 0, False, False), (['100'] * 7 + ['1000'], {}, 0, False, False),
    (['0'] + BASE, {'ignore_zero': True}, 1, False, False),
    (['-100'] + BASE, {'ignore_negative': True}, 1, False, False),
    (['0.10', '0.20', '0.30', '0.40', '0.50', '0.60', '0.70', '99'], {}, 1, False, False),
    ([None] + BASE, {'amount_field': 'reference'}, 1, True, False),
    (['abc'] + BASE, {'amount_field': 'reference'}, 0, True, False),
    (BASE, {'minimum_sample_size': 3}, None, False, False)])
def test_cli(tmp_path, values, config, count, alternate, reverse):
    s = create_snapshot(extraction(values, reverse=reverse, alternate=alternate), tmp_path)
    path = tmp_path / 'policy.json'; path.write_text(policy(**config).to_json())
    command = [sys.executable, '-m', 'audit_engine', '--artifacts-dir', str(tmp_path)]
    validated = subprocess.run([*command, 'policy', 'validate', str(path)], capture_output=True, timeout=30)
    assert validated.returncode == (1 if count is None else 0)
    executed = subprocess.run([*command, 'run', '--snapshot', s.snapshot_id, '--policy', str(path)], capture_output=True, timeout=30)
    assert executed.returncode == (1 if count is None or values[0] == 'abc' else 0)
    if count is None:
        assert not (tmp_path / 'runs').exists()
        return
    a = next((tmp_path / 'runs').iterdir())
    inspected = subprocess.run([*command, 'result', 'inspect', a.name], capture_output=True, timeout=30)
    assert inspected.returncode == 0
    actual = AuditResult.from_json(inspected.stdout)
    assert actual.finding_count == count
    if values == BASE and not config:
        expected = AuditResult.from_json((FIXTURE / 'example-result.json').read_text())
        assert logical_result(actual) == logical_result(expected)
        assert json.loads((a / 'logical-results.json').read_text())['logical_result_hash'] == json.loads((FIXTURE / 'logical-baseline.json').read_text())['hash']


def test_previous_payment_golden_and_fixture(tmp_path):
    from test_duplicate_payment import FIXTURE as old_root, FIXTURE_ID as old_id, POLICY as old_policy
    golden = json.loads((FIXTURE / 'previous-payment-baseline.json').read_text())
    p = load_policy(old_policy); m = DEFAULT_DETECTORS.get('business.duplicate_payment').metadata()
    assert p.to_json() == golden['policy_json']
    assert resolve_config(m, p.detector_configuration[m.detector_id]).to_json() == golden['config_json']
    c = load_snapshot(old_id, old_root)
    s = create_snapshot(SourceExtraction('postgresql', '1', c.tables), tmp_path)
    a, _ = execute_policy(s.snapshot_id, tmp_path, policy=p)
    assert json.loads((tmp_path / 'runs' / a.audit_run_id / 'logical-results.json').read_text())['logical_result_hash'] == golden['hash']
    c = load_snapshot(FIXTURE_ID, FIXTURE)
    assert c.snapshot.record_counts['payments'] == 8


def test_registration_defaults_and_input_boundary(tmp_path):
    m = DEFAULT_DETECTORS.get(KEY).metadata()
    assert m.detector_version == '1.0.0' and m.category == 'monetary_anomaly'
    assert resolve_config(m, {}).values == {**policy().detector_configuration[KEY], 'group_by_fields': ()}
    with pytest.raises(ValueError):
        parse_amount(1.5)
    # Direct frozen context protects identities even when called outside the loader.
    s = create_snapshot(extraction(), tmp_path); c = load_snapshot(s.snapshot_id, tmp_path)
    d = AmountOutlierDetector(); config = resolve_config(m, {})
    for value in (None, '', False, c.tables['payments'][1]['id']):
        rows = [dict(row) for row in c.tables['payments']]; rows[0]['id'] = value
        with pytest.raises(ValueError):
            d.analyze(replace(c, tables={**c.tables, 'payments': rows}), config)
