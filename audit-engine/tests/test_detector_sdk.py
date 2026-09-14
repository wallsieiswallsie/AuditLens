"""SDK behavior, reproducibility, CLI and authority boundary regression tests."""
from dataclasses import FrozenInstanceError, replace
import json
import os
from pathlib import Path
from unittest.mock import patch
import pytest
from test_framework import sample
from audit_engine.policy import AuditPolicy, DEFAULT_POLICY, load_policy
from audit_engine.detectors import (DetectorRegistry, DetectorMetadata, DetectorRequirements,
    ConfigField, DetectorConfig, DEFAULT_DETECTORS, FrameworkHealthDetector,
    SnapshotIntegrityDetector, resolve_config, validate_policy, compatibility, result_for)
from audit_engine.execution import execute_policy, logical_result
from audit_engine.models.contracts import RunStatus, ResultStatus, Severity
from audit_engine.snapshots import create_snapshot, load_snapshot
from audit_engine.__main__ import main


@pytest.fixture
def snapshot(tmp_path):
    return create_snapshot(sample(), tmp_path)


def policy(**changes):
    return replace(DEFAULT_POLICY, **changes)


class Probe:
    def __init__(self, key='example.probe', behavior=None, requirements=None):
        self.key, self.behavior = key, behavior
        self.requirements = requirements or DetectorRequirements('1', {'roles': ('id',)})
        self.calls = []

    def metadata(self):
        return DetectorMetadata(self.key, '1.0.0', 'Probe', 'Test-only framework probe',
            'framework', self.requirements, {'count': ConfigField('integer', 2, 'Test integer')})

    def analyze(self, context, config):
        self.calls.append((context, config))
        if self.behavior:
            return self.behavior(context, config)
        return result_for(self.metadata(), context, config, 'Probe complete')


def test_policy_roundtrip_and_canonical():
    one = policy(enabled_detectors=('z.probe', 'a.probe'))
    two = policy(enabled_detectors=('a.probe', 'z.probe'))
    assert one.to_json() == two.to_json()
    assert AuditPolicy.from_json(one.to_json()) == one
    assert load_policy('audit-engine/policies/default.json') == DEFAULT_POLICY


def test_deep_immutability():
    value = policy(detector_configuration={'framework.snapshot_integrity': {'emit_inventory': True}})
    with pytest.raises(FrozenInstanceError):
        value.policy_id = 'change'
    with pytest.raises(TypeError):
        value.detector_configuration['framework.snapshot_integrity']['emit_inventory'] = False
    with pytest.raises(TypeError):
        DetectorConfig({'nested': [1]}).values['nested'][0] = 2


@pytest.mark.parametrize('changes', [dict(contract_version='2'), dict(minimum_confidence=-0.1),
    dict(minimum_confidence=float('nan')), dict(minimum_confidence=True),
    dict(enabled_detectors=('framework.health', 'framework.health')), dict(fail_on_detector_error=1),
    dict(policy_id='../escape'), dict(policy_version=''), dict(name=3)])
def test_invalid_policy(changes):
    with pytest.raises((ValueError, TypeError)):
        policy(**changes)


@pytest.mark.parametrize('text', ['{}', '[]', '{', '{"x":1,"x":2}'])
def test_malformed_policy_file(tmp_path, text):
    path = tmp_path / 'policy.json'
    path.write_text(text)
    with pytest.raises(ValueError):
        load_policy(path)


@pytest.mark.parametrize('config', [{'unknown': 1}, {'count': True}, {'count': '2'}, {'count': 2.0}])
def test_config_rejected(config):
    with pytest.raises(ValueError):
        resolve_config(Probe().metadata(), config)


def test_unknown_detector_rejected():
    for changes in (dict(enabled_detectors=('unknown',)), dict(disabled_detectors=('unknown',)),
                    dict(detector_configuration={'unknown': {}})):
        with pytest.raises(ValueError, match='Unknown detector'):
            validate_policy(policy(**changes), DEFAULT_DETECTORS)


def test_registry():
    registry = DetectorRegistry((Probe('z.probe'), Probe('a.probe')))
    assert [m.detector_id for m in registry.list()] == ['a.probe', 'z.probe']
    assert registry.get('a.probe', '1.0.0').key == 'a.probe'
    for key, version in [('unknown', None), ('a.probe', '2')]:
        with pytest.raises(ValueError):
            registry.get(key, version)
    with pytest.raises(ValueError, match='Duplicate'):
        registry.register(Probe('a.probe'))
    registry.get('a.probe').key = 'changed'
    with pytest.raises(ValueError, match='mismatch'):
        registry.get('a.probe')


@pytest.mark.parametrize('key', ['../escape', 'a/b', 'C:\\private', '', 'bad name'])
def test_registry_bad_metadata(key):
    with pytest.raises(ValueError):
        DetectorRegistry([Probe(key)])


@pytest.mark.parametrize('requirement,reason', [
    (DetectorRequirements('2', {}), 'unsupported_schema_version'),
    (DetectorRequirements('1', {'absent': ()}), 'missing_table'),
    (DetectorRequirements('1', {'roles': ('absent',)}), 'missing_field'),
    (DetectorRequirements('1', {'users': ('absent',)}), 'missing_field')])
def test_requirements(snapshot, tmp_path, requirement, reason):
    detector = Probe(requirements=requirement)
    assert compatibility(load_snapshot(snapshot.snapshot_id, tmp_path), requirement) == reason
    run, results = execute_policy(snapshot.snapshot_id, tmp_path,
        policy=policy(enabled_detectors=(detector.key,)), registry=DetectorRegistry([detector]))
    assert run.status == RunStatus.FAILED
    assert results[0].status == ResultStatus.SKIPPED and results[0].summary == reason
    assert not detector.calls


def test_empty_table_required_field_supported(snapshot, tmp_path):
    assert compatibility(load_snapshot(snapshot.snapshot_id, tmp_path),
                         DetectorRequirements('1', {'users': ('id',)})) is None


def test_execution_order_config_disabled(snapshot, tmp_path):
    order = []
    a, b, c = Probe('a.probe'), Probe('b.probe'), Probe('c.probe')
    for d in (a, b, c):
        def behavior(context, config, detector=d):
            order.append(detector.key)
            return result_for(detector.metadata(), context, config, 'complete')
        d.behavior = behavior
    run, results = execute_policy(snapshot.snapshot_id, tmp_path, policy=policy(
        enabled_detectors=('c.probe', 'b.probe', 'a.probe'), disabled_detectors=('b.probe',),
        detector_configuration={'c.probe': {'count': 9}}), registry=DetectorRegistry([c, b, a]))
    assert order == ['a.probe', 'c.probe']
    assert run.status == RunStatus.COMPLETED and len(results) == 2
    assert a.calls[0][1].values['count'] == 2 and c.calls[0][1].values['count'] == 9
    assert run.detector_configuration['c.probe']['count'] == 9
    assert not b.calls


@pytest.mark.parametrize('strict,partial,executed', [(False, True, True), (True, True, False),
    (True, False, False), (False, False, False)])
def test_failure_isolation(snapshot, tmp_path, strict, partial, executed):
    sentinel = 'credential-sentinel-7249'
    def fail(context, config):
        raise RuntimeError('DATABASE_URL AUDIT_SOURCE_DATABASE_URL password C:\\private\\secret ' + sentinel)
    a, b = Probe('a.probe', fail), Probe('b.probe')
    with patch.dict(os.environ, {'DATABASE_URL': sentinel, 'AUDIT_SOURCE_DATABASE_URL': sentinel}):
        run, results = execute_policy(snapshot.snapshot_id, tmp_path,
            policy=policy(enabled_detectors=(a.key, b.key), fail_on_detector_error=strict,
                          allow_partial_results=partial), registry=DetectorRegistry([a, b]))
    assert run.status == RunStatus.FAILED
    assert results[0].status == ResultStatus.ERROR
    assert bool(b.calls) == executed
    assert results[1].status == (ResultStatus.PASSED if executed else ResultStatus.SKIPPED)
    for category in ('runs', 'results'):
        for path in (tmp_path / category).rglob('*.json'):
            for secret in ('DATABASE_URL', 'AUDIT_SOURCE_DATABASE_URL', 'password', sentinel, 'C:\\private'):
                assert secret not in path.read_text()


def test_context_authority_and_mutation(snapshot, tmp_path):
    def mutation(context, config):
        assert set(context.__dataclass_fields__) == {'snapshot', 'tables', 'policy_version',
                                                   'framework_version', 'detector_configuration'}
        assert not any(hasattr(context, key) for key in ('connection', 'adapter', 'repository', 'path', 'DATABASE_URL'))
        context.tables['roles'][0]['name'] = 'mutated'
    d = Probe(behavior=mutation)
    _, results = execute_policy(snapshot.snapshot_id, tmp_path, policy=policy(enabled_detectors=(d.key,)),
                                registry=DetectorRegistry([d]))
    assert results[0].status == ResultStatus.ERROR
    assert load_snapshot(snapshot.snapshot_id, tmp_path).tables['roles'][0]['name'] == 'Example'


def read_logical(tmp_path, run):
    return json.loads((tmp_path / 'runs' / run.audit_run_id / 'logical-results.json').read_text())


def test_identical_audits_and_hash_sensitivity(snapshot, tmp_path):
    p = load_policy('audit-engine/policies/examples.json')
    a, one = execute_policy(snapshot.snapshot_id, tmp_path, policy=p)
    b, two = execute_policy(snapshot.snapshot_id, tmp_path, policy=p)
    assert a.audit_run_id != b.audit_run_id
    assert [logical_result(r) for r in one] == [logical_result(r) for r in two]
    assert read_logical(tmp_path, a) == read_logical(tmp_path, b)
    c, _ = execute_policy(snapshot.snapshot_id, tmp_path, policy=replace(p, detector_configuration={}))
    assert read_logical(tmp_path, a)['logical_result_hash'] != read_logical(tmp_path, c)['logical_result_hash']
    assert one[1].finding_count == 1 and len(one[1].findings[0].evidence) == 11
    assert [e.source_table for e in one[1].findings[0].evidence] == sorted(snapshot.manifest)
    assert load_snapshot(snapshot.snapshot_id, tmp_path).snapshot.snapshot_hash == snapshot.snapshot_hash


@pytest.mark.parametrize('changes', [dict(minimum_severity=Severity.LOW), dict(minimum_confidence=1.0)])
def test_thresholds(snapshot, tmp_path, changes):
    p = replace(load_policy('audit-engine/policies/examples.json'), **changes)
    _, results = execute_policy(snapshot.snapshot_id, tmp_path, policy=p)
    assert results[1].finding_count == (0 if 'minimum_severity' in changes else 1)


def test_invalid_output_isolated(snapshot, tmp_path):
    d = Probe()
    d.behavior = lambda context, config: replace(result_for(d.metadata(), context, config, 'invalid'), detector_id='wrong')
    _, results = execute_policy(snapshot.snapshot_id, tmp_path, policy=policy(enabled_detectors=(d.key,)),
                                registry=DetectorRegistry([d]))
    assert results[0].summary == 'detector_error'


def test_invalid_config_before_artifacts(snapshot, tmp_path):
    with pytest.raises(ValueError):
        execute_policy(snapshot.snapshot_id, tmp_path, policy=policy(detector_configuration={'framework.health': {'bad': True}}))
    assert not (tmp_path / 'runs').exists()


def test_cli_commands_and_e2e(snapshot, tmp_path, capsys):
    for args in (['detectors', 'list'], ['detectors', 'inspect', 'framework.snapshot_integrity'],
                 ['policy', 'validate', 'audit-engine/policies/default.json']):
        assert main(args) == 0
        json.loads(capsys.readouterr().out)
    assert main(['detectors', 'inspect', 'unknown']) == 1
    capsys.readouterr()
    assert main(['--artifacts-dir', str(tmp_path), 'run', '--snapshot', snapshot.snapshot_id,
                 '--policy', 'audit-engine/policies/examples.json']) == 0
    capsys.readouterr()
    run_id = next((tmp_path / 'runs').iterdir()).name
    assert main(['--artifacts-dir', str(tmp_path), 'result', 'inspect', run_id]) == 0
    values = json.loads(capsys.readouterr().out)
    assert len(values) == 2 and values[1]['finding_count'] == 1


def test_reordered_findings_evidence_and_generated_ids(snapshot, tmp_path):
    from audit_engine.models.contracts import Evidence, Finding
    from uuid import uuid4
    d = Probe()
    reverse = False
    def produce(context, config):
        evidence = [Evidence(str(uuid4()), 'roles', {'id': 'one'}, 'id', 'one', {}),
                    Evidence(str(uuid4()), 'roles', {'id': 'two'}, 'id', 'two', {})]
        if reverse:
            evidence.reverse()
        findings = [Finding(str(uuid4()), d.key, 'example.inventory', 'Inventory', 'Test only',
                    severity, 0.8, 'snapshot', context.snapshot.snapshot_hash, tuple(evidence),
                    context.snapshot.snapshot_id, '') for severity in (Severity.INFO, Severity.HIGH)]
        if reverse:
            findings.reverse()
        return result_for(d.metadata(), context, config, 'Inventory', tuple(findings))
    d.behavior = produce
    p = policy(enabled_detectors=(d.key,))
    a, one = execute_policy(snapshot.snapshot_id, tmp_path, policy=p, registry=DetectorRegistry([d]))
    reverse = True
    b, two = execute_policy(snapshot.snapshot_id, tmp_path, policy=p, registry=DetectorRegistry([d]))
    assert read_logical(tmp_path, a) == read_logical(tmp_path, b)
    assert one[0].findings[0].severity == Severity.HIGH
    assert one[0].findings[0].evidence[0].source_record_id['id'] == 'one'
    d.behavior = lambda context, config: replace(produce(context, config), findings=())
    _, bad = execute_policy(snapshot.snapshot_id, tmp_path, policy=p, registry=DetectorRegistry([d]))
    assert bad[0].status == ResultStatus.ERROR


def test_version_and_evidence_change_logical_hash(snapshot, tmp_path):
    class Versioned(SnapshotIntegrityDetector):
        release = '1.0.0'
        observed = 1
        def metadata(self):
            return replace(super().metadata(), detector_version=self.release)
        def analyze(self, context, config):
            result = super().analyze(context, config)
            finding = result.findings[0]
            evidence = (replace(finding.evidence[0], observed_value=self.observed), *finding.evidence[1:])
            return replace(result, findings=(replace(finding, evidence=evidence),))
    d = Versioned()
    p = policy(enabled_detectors=('framework.snapshot_integrity',),
               detector_configuration={'framework.snapshot_integrity': {'emit_inventory': True}})
    hashes = []
    for release, observed in [('1.0.0', 1), ('2.0.0', 1), ('2.0.0', 2)]:
        d.release, d.observed = release, observed
        run, _ = execute_policy(snapshot.snapshot_id, tmp_path, policy=p, registry=DetectorRegistry([d]))
        hashes.append(read_logical(tmp_path, run)['logical_result_hash'])
    assert len(set(hashes)) == 3


def test_all_disabled_noop_and_missing_result_inventory(snapshot, tmp_path, capsys):
    run, results = execute_policy(snapshot.snapshot_id, tmp_path,
        policy=policy(disabled_detectors=('framework.health',)))
    assert results == () and run.status == RunStatus.COMPLETED
    assert main(['--artifacts-dir', str(tmp_path), 'result', 'inspect', run.audit_run_id]) == 0
    assert json.loads(capsys.readouterr().out) == []
    run, _ = execute_policy(snapshot.snapshot_id, tmp_path)
    (tmp_path / 'results' / run.audit_run_id / 'framework.health.json').unlink()
    assert main(['--artifacts-dir', str(tmp_path), 'result', 'inspect', run.audit_run_id]) == 1


def test_finding_change_changes_hash(snapshot, tmp_path):
    class Described(SnapshotIntegrityDetector):
        description = 'First framework explanation'
        def analyze(self, context, config):
            result = super().analyze(context, config)
            return replace(result, findings=(replace(result.findings[0], description=self.description),))
    detector = Described()
    p = policy(enabled_detectors=('framework.snapshot_integrity',),
               detector_configuration={'framework.snapshot_integrity': {'emit_inventory': True}})
    one, _ = execute_policy(snapshot.snapshot_id, tmp_path, policy=p, registry=DetectorRegistry([detector]))
    detector.description = 'Changed framework explanation'
    two, _ = execute_policy(snapshot.snapshot_id, tmp_path, policy=p, registry=DetectorRegistry([detector]))
    assert read_logical(tmp_path, one)['logical_result_hash'] != read_logical(tmp_path, two)['logical_result_hash']


def test_logical_hash_ignores_artifact_root_operator_snapshot_identity(tmp_path):
    p = load_policy('audit-engine/policies/examples.json')
    hashes = []
    for label in ('first', 'second'):
        root = tmp_path / label
        snapshot = create_snapshot(sample(), root)
        run, _ = execute_policy(snapshot.snapshot_id, root, operator=label, policy=p)
        hashes.append(read_logical(root, run))
    assert hashes[0] == hashes[1]


def test_cli_error_secret_exclusion(snapshot, tmp_path, capsys):
    sentinel = 'auditlens-super-secret-password-123'
    with patch('audit_engine.execution.check', side_effect=RuntimeError(
            'DATABASE_URL AUDIT_SOURCE_DATABASE_URL token credential C:\\private\\file ' + sentinel)):
        assert main(['--artifacts-dir', str(tmp_path), 'run', '--snapshot', snapshot.snapshot_id]) == 1
    output = capsys.readouterr()
    run_id = next((tmp_path / 'runs').iterdir()).name
    assert main(['--artifacts-dir', str(tmp_path), 'result', 'inspect', run_id]) == 0
    inspected = capsys.readouterr()
    content = output.out + output.err + inspected.out + inspected.err
    content += ''.join(path.read_text() for category in ('runs', 'results')
                       for path in (tmp_path / category).rglob('*.json'))
    for secret in (sentinel, 'DATABASE_URL', 'AUDIT_SOURCE_DATABASE_URL', 'password', 'token', 'credential', 'C:\\private'):
        assert secret not in content
