"""Sequence continuity semantics and integration through the existing policy CLI."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tracemalloc
from unittest.mock import patch
import pytest
from test_business_rules import extraction
from audit_engine.detectors import DEFAULT_DETECTORS, DetectorRegistry, DetectorMetadata, resolve_config
from audit_engine.execution import execute_policy, logical_result
from audit_engine.models.contracts import AuditResult, SourceExtraction
from audit_engine.policy import load_policy
from audit_engine.rules.sequence_gap import SequenceGapDetector
from audit_engine.snapshots import create_snapshot, load_snapshot

KEY = 'business.sequence_gap'
POLICY = 'audit-engine/policies/sequence-gap.json'
FIXTURE = Path('audit-engine/fixtures/sequence-gap')
FIXTURE_ID = '00000000-0000-4000-a000-000000000300'


def policy(**config):
    p = load_policy(POLICY)
    return replace(p, detector_configuration={KEY: {**p.detector_configuration[KEY], **config}})


def run(root, refs, config=None, reverse=False, registry=None):
    s = create_snapshot(extraction(refs, reverse), root)
    a, results = execute_policy(s.snapshot_id, root, operator=root.name, policy=policy(**(config or {})), registry=registry)
    logical = json.loads((root/'runs'/a.audit_run_id/'logical-results.json').read_text())
    return a, results[0], logical


def gaps(result):
    return [(c['missing_start'], c['missing_end'], c['missing_count'])
            for c in (json.loads(f.entity_id) for f in result.findings)]


@pytest.mark.parametrize('refs,config,expected', [
    ([1,2,4],{},[(3,3,1)]), ([1,2,6],{},[(3,5,3)]),
    ([1,3,5],{},[(2,2,1),(4,4,1)]), ([6,1,2],{},[(3,5,3)]),
    ([1,2,None,4],{},[(3,3,1)]), ([1,2,2,3],{},[]),
    ([3,4],{'minimum_value':1},[(1,2,2)]),
    ([1,2],{'maximum_value':4},[(3,4,2)]),
    ([3,5],{'minimum_value':1,'maximum_value':7},[(1,2,2),(4,4,1),(6,7,2)]),
    ([None,None],{'minimum_value':1,'maximum_value':5},[(1,5,5)]),
    ([],{'minimum_value':1,'maximum_value':5},[(1,5,5)]),
    ([1,2,3,4],{},[]), ([None,None],{},[]), ([],{},[]), ([3],{},[]),
    ([],{'minimum_value':1},[]), ([],{'maximum_value':1},[]),
    ([1],{'minimum_value':5},[]), ([5],{'maximum_value':1},[]),
    ([0,2],{'minimum_value':1,'maximum_value':1},[(1,1,1)]),
    ([1],{'minimum_value':1,'maximum_value':1},[]),
    ([-15,-12,-2,0,4,12],{},[(-14,-13,2),(-11,-3,9),(-1,-1,1),(1,3,3),(5,11,7)]),
    ([0,3,5,10],{'minimum_value':2,'maximum_value':6},[(2,2,1),(4,4,1),(6,6,1)])])
def test_semantics(tmp_path, refs, config, expected):
    a,r,_ = run(tmp_path,refs,config)
    assert a.status.value == 'completed'
    assert gaps(r) == expected
    for f in r.findings:
        assert f.rule_id == 'SEQUENCE_GAP' and f.severity.value == 'medium'
        assert len(f.evidence) <= 2
        for e in f.evidence:
            assert e.observed_value in refs and e.field == 'reference'
            assert 'amount' not in e.to_json()


@pytest.mark.parametrize('config', [{'table':12},{'minimum_value':'1'},{'maximum_value':1.0},
    {'minimum_value':True},{'maximum_value':False},{'allow_duplicates':'true'},
    {'minimum_value':10,'maximum_value':5},{'sequence_field':''},{'unknown':None}])
def test_config_before_analysis(tmp_path, config):
    s=create_snapshot(extraction([1,3]),tmp_path)
    with patch.object(SequenceGapDetector,'analyze') as analyze:
        errors=[]
        for _ in range(2):
            with pytest.raises(ValueError) as error:
                execute_policy(s.snapshot_id,tmp_path,policy=policy(**config))
            errors.append(str(error.value))
        assert errors[0] == errors[1]
    analyze.assert_not_called()
    assert not (tmp_path/'runs').exists()


@pytest.mark.parametrize('refs',[[],[1,3]])
@pytest.mark.parametrize('config,reason',[({'table':'absent'},'missing_table'),
    ({'id_field':'absent'},'missing_field'),({'sequence_field':'absent'},'missing_field')])
def test_compatibility(tmp_path,refs,config,reason):
    with patch.object(SequenceGapDetector,'analyze') as analyze:
        a,r,_=run(tmp_path,refs,config)
    analyze.assert_not_called()
    assert a.status.value == 'failed' and r.status.value == 'skipped' and r.summary == reason


@pytest.mark.parametrize('refs,config', [([1,True,3],{}),([1,'2',3],{}),([1,{},3],{}),
    ([1,[],3],{}),([1,2,2,4],{'allow_duplicates':False}),
    ([0,0,3],{'minimum_value':2,'allow_duplicates':False}),
    ([1,None,3],{'id_field':'reference'})])
def test_input_error(tmp_path,refs,config):
    a,r,_=run(tmp_path,refs,config)
    assert a.status.value == 'failed' and r.status.value == 'error'
    assert r.summary == 'detector_error' and r.findings == ()


def test_float_rejected_by_loader_and_detector(tmp_path):
    with pytest.raises(ValueError):
        create_snapshot(extraction([1,2.0,3]),tmp_path)
    s=create_snapshot(extraction([1,2,3]),tmp_path)
    c=load_snapshot(s.snapshot_id,tmp_path)
    c=replace(c,tables={**c.tables,'invoices':[dict(c.tables['invoices'][0],reference=2.0)]})
    d=SequenceGapDetector()
    with pytest.raises(ValueError):
        d.analyze(c,resolve_config(d.metadata(),policy().detector_configuration[KEY]))


def test_boundary_evidence(tmp_path):
    _,r,_=run(tmp_path,[10,10,12],{'minimum_value':8,'maximum_value':14})
    assert gaps(r)==[(8,9,2),(11,11,1),(13,14,2)]
    assert [[(e.observed_value,e.context['sequence_role']) for e in f.evidence] for f in r.findings]==[
        [(10,'after_gap')],[(10,'before_gap'),(12,'after_gap')],[(12,'before_gap')]]
    assert r.findings[1].evidence[0].source_record_id['id'].endswith('000000000001')
    _,empty,_=run(tmp_path/'empty',[],{'minimum_value':1,'maximum_value':5})
    assert empty.findings[0].evidence == ()
    assert json.loads(empty.findings[0].entity_id)['missing_count']==5


def test_large_range_memory(tmp_path):
    s=create_snapshot(extraction([1,1000000000]),tmp_path)
    c=load_snapshot(s.snapshot_id,tmp_path); d=SequenceGapDetector()
    config=resolve_config(d.metadata(),policy(minimum_value=1,maximum_value=1000000000).detector_configuration[KEY])
    tracemalloc.start()
    try:
        r=d.analyze(c,config)
        _,peak=tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert gaps(r)==[(2,999999999,999999998)]
    assert peak < 1_000_000  # Observed records/gaps only; a billion-value expansion cannot pass.


def test_reproducibility(tmp_path):
    with patch.dict(os.environ,{'DATABASE_URL':'secret-sentinel','AUDIT_SOURCE_DATABASE_URL':'secret-sentinel'}):
        a,one,first=run(tmp_path/'first',[1,2,2,6,8])
        with patch('audit_engine.execution.now',return_value='2030-01-01T00:00:00.000000Z'):
            b,two,second=run(tmp_path/'second',[1,2,2,6,8],reverse=True)
    assert a.audit_run_id != b.audit_run_id and a.snapshot_id != b.snapshot_id
    assert one.started_at != two.started_at
    assert logical_result(one)==logical_result(two) and first==second
    d=SequenceGapDetector(); c=load_snapshot(a.snapshot_id,tmp_path/'first')
    config=resolve_config(d.metadata(),policy().detector_configuration[KEY])
    shuffled=replace(c,tables={k:[dict(reversed(list(r.items()))) for r in reversed(rows)]
        for k,rows in reversed(list(c.tables.items()))})
    assert d.analyze(c,config).to_json()==d.analyze(shuffled,config).to_json()
    for path in tmp_path.rglob('*.json'):
        assert 'secret-sentinel' not in path.read_text()


def test_hash_mutations(tmp_path):
    class Variant(SequenceGapDetector):
        release='1.0.0'
        mutation=None
        def metadata(self):
            return replace(super().metadata(),detector_version=self.release)
        def analyze(self,context,config):
            r=super().analyze(context,config); f=r.findings[0]
            if self.mutation=='finding': f=replace(f,description='Changed content')
            if self.mutation=='evidence': f=replace(f,evidence=(replace(f.evidence[0],context={'changed':True}),*f.evidence[1:]))
            return replace(r,findings=(f,*r.findings[1:]))
    d=Variant(); hashes=[]
    for i,(refs,config,d.release,d.mutation) in enumerate([
        ([1,4],{},'1.0.0',None),([1,5],{},'1.0.0',None),
        ([1,4,4],{},'1.0.0',None),([1,4],{'minimum_value':0},'1.0.0',None),
        ([1,4],{'maximum_value':6},'1.0.0',None),([1,4],{'allow_duplicates':False},'1.0.0',None),
        ([1,4],{},'1.0.1',None),([1,4],{},'1.0.0','finding'),([1,4],{},'1.0.0','evidence')]):
        _,_,logical=run(tmp_path/str(i),refs,config,registry=DetectorRegistry([d]))
        hashes.append(logical['logical_result_hash'])
    assert len(set(hashes))==len(hashes)


def test_optional_integer_and_completeness_baseline(tmp_path):
    m=DEFAULT_DETECTORS.get(KEY).metadata()
    assert m.category=='sequence_integrity' and m.detector_version=='1.0.0'
    assert DetectorMetadata.from_json(m.to_json())==m
    assert resolve_config(m,{}).to_dict()['values']==dict(table='transactions',id_field='id',sequence_field='sequence_number',minimum_value=None,maximum_value=None,allow_duplicates=True)
    from test_completeness import FIXTURE as old_root, FIXTURE_ID as old_id, POLICY as old_policy
    baseline=json.loads((old_root/'completeness-baseline.json').read_text())
    p=load_policy(old_policy); prior=DEFAULT_DETECTORS.get('business.missing_required_field').metadata()
    assert p.to_json()==baseline['policy_json']
    assert resolve_config(prior,p.detector_configuration[prior.detector_id]).to_json()==baseline['config_json']
    c=load_snapshot(old_id,old_root)
    s=create_snapshot(SourceExtraction('postgresql','1',c.tables),tmp_path)
    a,_=execute_policy(s.snapshot_id,tmp_path,policy=p)
    assert json.loads((tmp_path/'runs'/a.audit_run_id/'logical-results.json').read_text())['logical_result_hash']==baseline['hash']


@pytest.mark.parametrize('refs,config,code,count', [([1,2,4,8],{},0,2),([1,2,3],{},0,0),
    ([1,3],{'minimum_value':0,'maximum_value':5},0,3),
    ([1,3],{'minimum_value':10,'maximum_value':5},1,None),([1,True,3],{},1,0),
    ([1,'2',3],{},1,0),([1,2,2,4],{'allow_duplicates':False},1,0),
    ([1,1000000000],{},0,1)])
def test_cli(tmp_path,refs,config,code,count):
    s=create_snapshot(extraction(refs),tmp_path)
    path=tmp_path/'policy.json'; path.write_text(policy(**config).to_json())
    command=[sys.executable,'-m','audit_engine','--artifacts-dir',str(tmp_path)]
    validate=subprocess.run([*command,'policy','validate',str(path)],capture_output=True,timeout=30)
    assert validate.returncode==(1 if count is None else 0)
    result=subprocess.run([*command,'run','--snapshot',s.snapshot_id,'--policy',str(path)],capture_output=True,timeout=30)
    assert result.returncode==code
    if count is None:
        assert not (tmp_path/'runs').exists(); return
    a=next((tmp_path/'runs').iterdir())
    inspected=subprocess.run([*command,'result','inspect',a.name],capture_output=True,timeout=30)
    assert inspected.returncode==0
    data=json.loads(inspected.stdout)
    assert data['finding_count']==count
    if code: assert data['summary']=='detector_error'


def test_fixture_reordered_cli(tmp_path):
    expected=AuditResult.from_json((FIXTURE/'example-result.json').read_text())
    c=load_snapshot(FIXTURE_ID,FIXTURE); hashes=[]
    for reverse in (False,True):
        root=tmp_path/str(reverse)
        tables={k:[dict(reversed(list(r.items()))) if reverse else dict(r) for r in (reversed(rows) if reverse else rows)] for k,rows in c.tables.items()}
        s=create_snapshot(SourceExtraction('postgresql','1',tables),root)
        cli=subprocess.run([sys.executable,'-m','audit_engine','--artifacts-dir',str(root),'run','--snapshot',s.snapshot_id,'--policy',POLICY],capture_output=True,timeout=30)
        assert cli.returncode==0
        a=next((root/'runs').iterdir())
        hashes.append(json.loads((a/'logical-results.json').read_text())['logical_result_hash'])
        actual=AuditResult.from_json((root/'results'/a.name/(KEY+'.json')).read_text())
        assert logical_result(actual)==logical_result(expected)
    assert hashes[0]==hashes[1]
