"""Completeness semantics, compatibility, reproducibility and real policy CLI."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import pytest
from test_business_rules import extraction, ROOT, SNAPSHOT_ID
from audit_engine.detectors import DEFAULT_DETECTORS, DetectorRegistry, resolve_config, validate_policy
from audit_engine.execution import execute_policy, logical_result
from audit_engine.models.contracts import RunStatus, ResultStatus, AuditResult
from audit_engine.policy import load_policy
from audit_engine.rules.missing_required_field import MissingRequiredFieldDetector
from audit_engine.snapshots import create_snapshot, load_snapshot

KEY = 'business.missing_required_field'
POLICY = 'audit-engine/policies/missing-required-field.json'
FIXTURE = Path('audit-engine/fixtures/missing-required-field')
FIXTURE_ID = '00000000-0000-4000-a000-000000000200'


def policy(**config):
    p = load_policy(POLICY)
    return replace(p, detector_configuration={KEY: {**p.detector_configuration[KEY], **config}})


def source(refs, reverse=False, offset=0):
    data = extraction(refs, reverse, offset)
    return replace(data, tables={**data.tables, 'invoices': [dict(r, vendor_id=None) for r in data.tables['invoices']]})


def run(root, refs, config=None, reverse=False, offset=0, registry=None):
    s = create_snapshot(source(refs, reverse, offset), root)
    audit, results = execute_policy(s.snapshot_id, root, operator=root.name, policy=policy(**(config or {})), registry=registry)
    logical = json.loads((root/'runs'/audit.audit_run_id/'logical-results.json').read_text())
    return audit, results[0], logical


@pytest.mark.parametrize('refs,config,sizes', [
    ([None], {'required_fields':['reference']}, [1]),
    ([''], {'required_fields':['reference']}, [1]),
    ([''], {'required_fields':['reference'], 'treat_empty_string_as_missing':False}, []),
    ([None], {}, [2]), ([None, None], {}, [2,2]),
    (['A'], {'required_fields':['reference']}, []),
    ([' ',0,False,[],{}], {'required_fields':['reference']}, []), ([], {}, [])])
def test_semantics(tmp_path, refs, config, sizes):
    audit, result, _ = run(tmp_path, refs, config)
    assert audit.status == RunStatus.COMPLETED
    assert [len(f.evidence) for f in result.findings] == sizes
    assert [f.entity_id for f in result.findings] == sorted(f.entity_id for f in result.findings)
    for f in result.findings:
        assert f.rule_id == 'MISSING_REQUIRED_FIELD' and f.entity_type == 'invoices'
        assert f.severity.value == 'medium'
        fields = [e.field for e in f.evidence]
        assert fields == sorted(fields)
        assert f.evidence[0].context['missing_fields'] == tuple(fields)
        assert f.evidence[0].context['missing_field_count'] == len(fields)
        for e in f.evidence:
            assert e.source_record_id == {'id':f.entity_id}
            assert e.context['missing_classification'] == ('null' if e.observed_value is None else 'empty_string')
            assert 'amount' not in e.to_json()


@pytest.mark.parametrize('config', [{'table':123}, {'required_fields':'reference'},
    {'required_fields':['reference',123]}, {'required_fields':[]},
    {'required_fields':['reference','reference']}, {'treat_empty_string_as_missing':1},
    {'treat_empty_string_as_missing':'false'}, {'required_fields':['bad field']},
    {'id_field':''}, {'unknown':True}, {'required_fields':[['reference']]}])
def test_invalid_config_before_execution(tmp_path, config):
    s = create_snapshot(source([None]), tmp_path)
    with patch.object(MissingRequiredFieldDetector, 'analyze') as analyze:
        errors = []
        for _ in range(2):
            with pytest.raises(ValueError) as error:
                execute_policy(s.snapshot_id, tmp_path, policy=policy(**config))
            errors.append(str(error.value))
        assert errors[0] == errors[1]
    analyze.assert_not_called()
    assert not (tmp_path/'runs').exists()


@pytest.mark.parametrize('refs', [[], [None]])
@pytest.mark.parametrize('config,reason', [({'table':'absent'},'missing_table'),
    ({'id_field':'absent'},'missing_field'), ({'required_fields':['reference','absent']},'missing_field')])
def test_requirements_before_analysis(tmp_path, refs, config, reason):
    with patch.object(MissingRequiredFieldDetector, 'analyze') as analyze:
        audit, result, _ = run(tmp_path, refs, config)
    analyze.assert_not_called()
    assert audit.status == RunStatus.FAILED and result.status == ResultStatus.SKIPPED
    assert result.summary == reason


def test_reproducibility_and_secrets(tmp_path):
    with patch.dict(os.environ, {'DATABASE_URL':'secret-sentinel', 'AUDIT_SOURCE_DATABASE_URL':'secret-sentinel'}):
        a, one, first = run(tmp_path/'first', [None,'', 'A'])
        with patch('audit_engine.execution.now', return_value='2030-01-01T00:00:00.000000Z'):
            b, two, second = run(tmp_path/'second', [None,'','A'], reverse=True)
    assert a.audit_run_id != b.audit_run_id and a.snapshot_id != b.snapshot_id
    assert one.started_at != two.started_at
    assert logical_result(one) == logical_result(two) and first == second
    d = MissingRequiredFieldDetector()
    c = resolve_config(d.metadata(), policy().detector_configuration[KEY])
    context = load_snapshot(a.snapshot_id, tmp_path/'first')
    shuffled = replace(context, tables={k:[dict(reversed(list(r.items()))) for r in reversed(rows)]
        for k,rows in reversed(list(context.tables.items()))})
    assert d.analyze(context,c).to_json() == d.analyze(shuffled,c).to_json()
    for p in tmp_path.rglob('*.json'):
        assert 'secret-sentinel' not in p.read_text()


def test_hash_mutations(tmp_path):
    class Variant(MissingRequiredFieldDetector):
        release = '1.0.0'
        mutation = None
        def metadata(self):
            return replace(super().metadata(), detector_version=self.release)
        def analyze(self, context, config):
            result = super().analyze(context, config)
            f = result.findings[0]
            if self.mutation == 'finding':
                f = replace(f, description='Changed content')
            if self.mutation == 'evidence':
                f = replace(f, evidence=(replace(f.evidence[0], context={'changed':True}), *f.evidence[1:]))
            return replace(result, findings=(f,))
    d, hashes, findings = Variant(), [], []
    variants = [([None],{},0,'1.0.0',None), (['A'],{},0,'1.0.0',None),
        ([None],{},1,'1.0.0',None), ([None],{'required_fields':['reference']},0,'1.0.0',None),
        ([None],{'treat_empty_string_as_missing':False},0,'1.0.0',None),
        ([None],{},0,'1.0.1',None), ([None],{},0,'1.0.0','finding'), ([None],{},0,'1.0.0','evidence')]
    for i,(refs,config,offset,d.release,d.mutation) in enumerate(variants):
        _, result, logical = run(tmp_path/str(i),refs,config,offset=offset,registry=DetectorRegistry([d]))
        hashes.append(logical['logical_result_hash']); findings.append(result.findings[0].finding_id)
    assert len(set(hashes)) == len(hashes)
    assert findings[0] != findings[1]  # Missing-field set changes finding identity.


@pytest.mark.parametrize('refs', [[None], ['same','same'], ['']])
def test_bad_custom_record_identity(tmp_path, refs):
    audit, result, _ = run(tmp_path,refs,{'id_field':'reference'})
    assert audit.status == RunStatus.FAILED and result.summary == 'detector_error'


def test_list_roundtrip_defaults_and_scalar_baseline(tmp_path):
    from audit_engine.detectors import DetectorMetadata
    d = DEFAULT_DETECTORS.get(KEY)
    m = d.metadata()
    assert m.detector_version == '1.0.0' and m.category == 'data_completeness'
    assert DetectorMetadata.from_json(m.to_json()) == m
    c = resolve_config(m,{})
    assert c.to_dict()['values'] == dict(table='transactions',id_field='id',required_fields=['reference'],treat_empty_string_as_missing=True)
    with pytest.raises(TypeError):
        c.values['required_fields'][0] = 'changed'
    validate_policy(policy(), DEFAULT_DETECTORS)
    baseline = json.loads((ROOT/'duplicate-baseline.json').read_text())
    p = load_policy('audit-engine/policies/business-rulepack-v1.json')
    assert p.to_json() == baseline['policy_json']
    prior = DEFAULT_DETECTORS.get('business.duplicate_transaction_reference')
    assert resolve_config(prior.metadata(),p.detector_configuration[prior.metadata().detector_id]).to_json() == baseline['config_json']
    s = create_snapshot(extraction(['INV-001','INV-002','INV-001']),tmp_path)
    a,_ = execute_policy(s.snapshot_id,tmp_path,policy=p)
    logical = json.loads((tmp_path/'runs'/a.audit_run_id/'logical-results.json').read_text())
    assert logical['logical_result_hash'] == baseline['hash']


@pytest.mark.parametrize('refs,config,code,count,reason', [([None],{},0,1,None),
    (['A'],{'required_fields':['reference']},0,0,None),
    ([None],{'required_fields':[]},1,None,None),
    ([None],{'required_fields':['absent']},1,0,'missing_field')])
def test_cli(tmp_path, refs, config, code, count, reason):
    s = create_snapshot(source(refs),tmp_path)
    p = tmp_path/'policy.json'; p.write_text(policy(**config).to_json())
    command = [sys.executable,'-m','audit_engine','--artifacts-dir',str(tmp_path)]
    result = subprocess.run([*command,'run','--snapshot',s.snapshot_id,'--policy',str(p)],capture_output=True,timeout=30)
    assert result.returncode == code
    if count is None:
        assert not (tmp_path/'runs').exists(); return
    run_id = next((tmp_path/'runs').iterdir()).name
    result = subprocess.run([*command,'result','inspect',run_id],capture_output=True,timeout=30)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data['finding_count'] == count
    if reason: assert data['summary'] == reason


def test_fixture_and_reordered_cli(tmp_path):
    expected = AuditResult.from_json((FIXTURE/'example-result.json').read_text())
    context = load_snapshot(FIXTURE_ID,FIXTURE)
    from audit_engine.models.contracts import SourceExtraction
    hashes=[]
    for reverse in (False,True):
        root = tmp_path/str(reverse)
        tables = {k:[dict(reversed(list(r.items()))) if reverse else dict(r) for r in (reversed(v) if reverse else v)] for k,v in context.tables.items()}
        s = create_snapshot(SourceExtraction('postgresql','1',tables),root)
        cli = subprocess.run([sys.executable,'-m','audit_engine','--artifacts-dir',str(root),'run','--snapshot',s.snapshot_id,'--policy',POLICY],capture_output=True,timeout=30)
        assert cli.returncode == 0
        a = next((root/'runs').iterdir())
        hashes.append(json.loads((a/'logical-results.json').read_text())['logical_result_hash'])
        actual = AuditResult.from_json((root/'results'/a.name/(KEY+'.json')).read_text())
        assert logical_result(actual) == logical_result(expected)
    assert hashes[0] == hashes[1]
