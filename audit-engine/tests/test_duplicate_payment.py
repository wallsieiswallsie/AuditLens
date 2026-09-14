"""Composite payment semantics, canonical artifacts and real policy CLI."""
from dataclasses import replace
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
from audit_engine.rules.duplicate_payment import DuplicatePaymentDetector
from audit_engine.snapshots import create_snapshot, load_snapshot, SCHEMA

KEY = 'business.duplicate_payment'
POLICY = 'audit-engine/policies/duplicate-payment.json'
FIXTURE = Path('audit-engine/fixtures/duplicate-payment')
FIXTURE_ID = '00000000-0000-4000-a000-000000000400'
BASE = [('I1',100,'P1'),('I2',200,'P2'),('I1',100,'P1')]


def policy(**config):
    p = load_policy(POLICY)
    return replace(p, detector_configuration={KEY: {**p.detector_configuration[KEY], **config}})


def extraction(values, reverse=False, offset=0):
    rows=[]
    for i,(invoice,amount,reference) in enumerate(values,1):
        row=dict.fromkeys(SCHEMA['payments'])
        row.update(id=f'00000000-0000-4000-a000-{i+offset:012d}', invoice_id=invoice,
                   amount=amount, reference=reference, currency='IDR', status='pending')
        rows.append(row)
    if reverse:
        rows=[dict(reversed(list(r.items()))) for r in reversed(rows)]
    return SourceExtraction('postgresql','1',{t: rows if t=='payments' else [] for t in SCHEMA})


def run(root,values=BASE,config=None,reverse=False,offset=0,registry=None):
    s=create_snapshot(extraction(values,reverse,offset),root)
    a,rs=execute_policy(s.snapshot_id,root,operator=root.name,policy=policy(**(config or {})),registry=registry)
    return a,rs[0],json.loads((root/'runs'/a.audit_run_id/'logical-results.json').read_text())


@pytest.mark.parametrize('values,config,sizes',[
    (BASE,{},[2]), ([BASE[0]]*3,{},[3]), (BASE+[BASE[1]],{},[2,2]),
    (BASE[:2],{},[]),([],{},[]),
    ([('VENDOR-A',100,'PAY-001'),('vendor-a',100,'pay-001')],{},[]),
    ([('VENDOR-A',100,'PAY-001'),('vendor-a',100,'pay-001')],{'case_sensitive_strings':False},[2]),
    ([('I',100,'Straße'),('I',100,'STRASSE')],{'case_sensitive_strings':False},[2]),
    ([('I',100,'P'),('I',100,' P ')],{'case_sensitive_strings':False},[]),
    ([('I',100,None)]*2,{},[]),([('I',100,'')]*2,{},[]),
    ([('I',100,None)]*2,{'ignore_if_any_match_field_empty':False},[2]),
    ([('I',100,'')]*2,{'ignore_if_any_match_field_empty':False},[2]),
    ([('I',100,None),('I',100,'')],{'ignore_if_any_match_field_empty':False},[]),
    ([(v,100,'P') for v in [1,True,'1',1,True,'1']],{},[2,2,2]),
    ([(v,100,'P') for v in [' ',0,False,[],{}]]*2,{},[2,2,2,2,2]),
    ([('I',100,{'b':[True,1],'a':'X'}),('I',100,{'a':'X','b':[True,1]})],{},[2]),
    ([('I',100,{'a':'X'}),('I',100,{'a':'x'})],{'case_sensitive_strings':False},[]),
    ([('I',100,[1,True]),('I',100,[True,1])],{},[]),
    ([('I',100,'P'),('I',101,'P')],{},[])])
def test_semantics(tmp_path,values,config,sizes):
    a,r,_=run(tmp_path,values,config)
    assert a.status.value=='completed'
    assert sorted(len(f.evidence) for f in r.findings)==sizes
    assert [f.entity_id for f in r.findings]==sorted(f.entity_id for f in r.findings)
    for f in r.findings:
        assert f.rule_id=='DUPLICATE_PAYMENT' and f.severity.value=='high'
        assert [e.source_record_id['id'] for e in f.evidence]==sorted(e.source_record_id['id'] for e in f.evidence)
        for e in f.evidence:
            assert e.source_table=='payments' and e.field is None and e.observed_value is None
            assert set(e.context['match_values'])=={'invoice_id','amount','currency','reference'}
            assert e.context['duplicate_count']==len(f.evidence)
            original=values[int(e.source_record_id['id'][-12:])-1]
            assert e.to_dict()['context']['match_values']['reference']==original[2]
            assert 'status' not in e.to_json() and 'created_by' not in e.to_json()


@pytest.mark.parametrize('config',[{'match_fields':[]},{'match_fields':['amount']},
    {'match_fields':['amount','amount']},{'table':123},{'match_fields':'invoice_id'},
    {'match_fields':['invoice_id',123]},{'ignore_if_any_match_field_empty':'true'},
    {'case_sensitive_strings':1},{'match_fields':['amount','']},{'id_field':''},{'unknown':True}])
def test_invalid_config(tmp_path,config):
    s=create_snapshot(extraction(BASE),tmp_path)
    with patch.object(DuplicatePaymentDetector,'analyze') as analyze:
        errors=[]
        for _ in range(2):
            with pytest.raises(ValueError) as error:
                execute_policy(s.snapshot_id,tmp_path,policy=policy(**config))
            errors.append(str(error.value))
        assert errors[0]==errors[1]
    analyze.assert_not_called()
    assert not (tmp_path/'runs').exists()


@pytest.mark.parametrize('values',[[],BASE])
@pytest.mark.parametrize('config,reason',[({'table':'absent'},'missing_table'),
    ({'id_field':'absent'},'missing_field'),({'match_fields':['amount','absent']},'missing_field')])
def test_compatibility(tmp_path,values,config,reason):
    with patch.object(DuplicatePaymentDetector,'analyze') as analyze:
        a,r,_=run(tmp_path,values,config)
    analyze.assert_not_called()
    assert a.status.value=='failed' and r.status.value=='skipped' and r.summary==reason


@pytest.mark.parametrize('field',['invoice_id','amount','confirmed_by'])
def test_invalid_record_identity(tmp_path,field):
    a,r,_=run(tmp_path,config={'id_field':field})
    assert a.status.value=='failed' and r.summary=='detector_error' and not r.findings


def test_reproducibility(tmp_path):
    with patch.dict(os.environ,{'DATABASE_URL':'secret-sentinel','AUDIT_SOURCE_DATABASE_URL':'secret-sentinel'}):
        a,one,first=run(tmp_path/'first',BASE+[BASE[1]])
        with patch('audit_engine.execution.now',return_value='2030-01-01T00:00:00.000000Z'), patch('audit_engine.snapshots.now',return_value='2030-01-01T00:00:00.000000Z'):
            b,two,second=run(tmp_path/'second',BASE+[BASE[1]],reverse=True)
    assert a.audit_run_id!=b.audit_run_id and a.snapshot_id!=b.snapshot_id
    assert one.started_at!=two.started_at
    assert logical_result(one)==logical_result(two) and first==second
    d=DuplicatePaymentDetector(); c=load_snapshot(a.snapshot_id,tmp_path/'first')
    config=resolve_config(d.metadata(),policy().detector_configuration[KEY])
    shuffled=replace(c,tables={k:[dict(reversed(list(r.items()))) for r in reversed(rows)] for k,rows in reversed(list(c.tables.items()))})
    assert d.analyze(c,config).to_json()==d.analyze(shuffled,config).to_json()
    for path in tmp_path.rglob('*.json'):
        assert 'secret-sentinel' not in path.read_text()


def test_hash_sensitivity(tmp_path):
    class Variant(DuplicatePaymentDetector):
        release='1.0.0'
        mutation=None
        def metadata(self):
            return replace(super().metadata(),detector_version=self.release)
        def analyze(self,context,config):
            r=super().analyze(context,config); f=r.findings[0]
            if self.mutation=='finding': f=replace(f,description='Changed content')
            if self.mutation=='evidence': f=replace(f,evidence=(replace(f.evidence[0],context={'changed':True}),*f.evidence[1:]))
            return replace(r,findings=(f,))
    d=Variant(); hashes=[]; entities=[]
    for i,(values,config,offset,d.release,d.mutation) in enumerate([
        (BASE,{},0,'1.0.0',None),(BASE,{},10,'1.0.0',None),
        ([('I1',101,'P1')]*2,{},0,'1.0.0',None),
        (BASE,{'match_fields':['reference','currency','amount','invoice_id']},0,'1.0.0',None),
        (BASE,{'ignore_if_any_match_field_empty':False},0,'1.0.0',None),
        (BASE,{'case_sensitive_strings':False},0,'1.0.0',None),
        (BASE,{},0,'1.0.1',None),(BASE,{},0,'1.0.0','finding'),(BASE,{},0,'1.0.0','evidence')]):
        _,r,logical=run(tmp_path/str(i),values,config,offset=offset,registry=DetectorRegistry([d]))
        hashes.append(logical['logical_result_hash']); entities.append(r.findings[0].entity_id)
    assert len(set(hashes))==len(hashes)
    assert entities[0]==entities[1]  # Group identity is independent of participating IDs.
    assert entities[0]!=entities[3]  # Configured field order is identity-significant.


@pytest.mark.parametrize('values,config,code,count,reverse',[
    (BASE,{},0,1,False),(BASE,{},0,1,True),(BASE[:2],{},0,0,False),
    ([('I',100,'P'),('i',100,'p')],{},0,0,False),
    ([('I',100,'P'),('i',100,'p')],{'case_sensitive_strings':False},0,1,False),
    ([('I',100,None)]*2,{},0,0,False),
    ([('I',100,None)]*2,{'ignore_if_any_match_field_empty':False},0,1,False),
    (BASE,{'match_fields':['amount']},1,None,False),
    (BASE,{'match_fields':['amount','absent']},1,0,False)])
def test_cli(tmp_path,values,config,code,count,reverse):
    s=create_snapshot(extraction(values,reverse),tmp_path)
    path=tmp_path/'policy.json'; path.write_text(policy(**config).to_json())
    command=[sys.executable,'-m','audit_engine','--artifacts-dir',str(tmp_path)]
    validate=subprocess.run([*command,'policy','validate',str(path)],capture_output=True,timeout=30)
    assert validate.returncode==(1 if count is None else 0)
    executed=subprocess.run([*command,'run','--snapshot',s.snapshot_id,'--policy',str(path)],capture_output=True,timeout=30)
    assert executed.returncode==code
    if count is None:
        assert not (tmp_path/'runs').exists(); return
    a=next((tmp_path/'runs').iterdir())
    inspected=subprocess.run([*command,'result','inspect',a.name],capture_output=True,timeout=30)
    assert inspected.returncode==0
    actual=AuditResult.from_json(inspected.stdout)
    assert actual.finding_count==count
    if values==BASE and not config:
        expected=AuditResult.from_json((FIXTURE/'example-result.json').read_text())
        assert logical_result(actual)==logical_result(expected)
        baseline=json.loads((FIXTURE/'logical-baseline.json').read_text())
        assert json.loads((a/'logical-results.json').read_text())['logical_result_hash']==baseline['hash']


def test_fixture_and_previous_golden(tmp_path):
    expected=AuditResult.from_json((FIXTURE/'example-result.json').read_text())
    hashes=[]
    for reverse in (False,True):
        _,r,logical=run(tmp_path/str(reverse),reverse=reverse)
        assert logical_result(r)==logical_result(expected)
        hashes.append(logical['logical_result_hash'])
    assert hashes[0]==hashes[1]
    c=load_snapshot(FIXTURE_ID,FIXTURE)
    assert sum(c.snapshot.record_counts.values())==3
    from test_sequence_gap import FIXTURE as old_root, FIXTURE_ID as old_id, POLICY as old_policy
    baseline=json.loads((old_root/'sequence-baseline.json').read_text())
    p=load_policy(old_policy); m=DEFAULT_DETECTORS.get('business.sequence_gap').metadata()
    assert p.to_json()==baseline['policy_json']
    assert resolve_config(m,p.detector_configuration[m.detector_id]).to_json()==baseline['config_json']
    c=load_snapshot(old_id,old_root); root=tmp_path/'old'
    s=create_snapshot(SourceExtraction('postgresql','1',c.tables),root)
    a,_=execute_policy(s.snapshot_id,root,policy=p)
    assert json.loads((root/'runs'/a.audit_run_id/'logical-results.json').read_text())['logical_result_hash']==baseline['hash']


def test_registration_and_defaults():
    m=DEFAULT_DETECTORS.get(KEY).metadata()
    assert m.detector_version=='1.0.0' and m.category=='payment_integrity'
    assert resolve_config(m,{}).values==policy().detector_configuration[KEY]
