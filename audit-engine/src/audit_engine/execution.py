"""Policy-driven local execution from validated frozen data."""
from dataclasses import replace
from hashlib import sha256
from uuid import uuid4, uuid5, UUID
import json
import re
from audit_engine.analyzers.health import check
from audit_engine.models.contracts import AuditRun, Provenance, AuditResult, RunStatus, ResultStatus, Severity
from audit_engine.snapshots import load_snapshot, location, atomic_write, now, DEFAULT_ROOT
from audit_engine.versioning import FRAMEWORK_VERSION
from audit_engine.policy import load_policy, AuditPolicy
from audit_engine.detectors import DEFAULT_DETECTORS, validate_policy, compatibility, result_for, resolve_requirements


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def logical_result(result):
    value = result.to_dict()
    for key in ('result_id', 'audit_run_id', 'started_at', 'completed_at', 'snapshot_id'):
        value.pop(key)
    for finding in value['findings']:
        for key in ('audit_run_id', 'snapshot_id'):
            finding.pop(key)
    return value


def normalize_result(result, metadata, context, config, policy, identifier, started):
    result = AuditResult.from_json(result.to_json())
    if (result.detector_id != metadata.detector_id or result.detector_version != metadata.detector_version
            or result.snapshot_hash != context.snapshot.snapshot_hash
            or result.snapshot_id != context.snapshot.snapshot_id
            or result.policy_version != policy.policy_version
            or result.detector_configuration != config.values
            or result.finding_count != len(result.findings)):
        raise ValueError('Invalid detector output identity')
    if (result.status == ResultStatus.FINDINGS) != bool(result.findings):
        raise ValueError('Invalid detector output status')
    findings = []
    for finding in result.findings:
        if (finding.detector_id != metadata.detector_id or finding.snapshot_id != context.snapshot.snapshot_id
                or not 0 <= finding.confidence <= 1):
            raise ValueError('Invalid finding')
        evidence = []
        for item in finding.evidence:
            if item.source_table not in context.tables:
                raise ValueError('Unknown evidence table')
            value = item.to_dict()
            value.pop('evidence_id')
            evidence.append(replace(item, evidence_id=sha256(canonical_json(value).encode()).hexdigest()))
        evidence.sort(key=lambda e: (e.source_table, canonical_json(dict(e.source_record_id)), e.field or '', e.to_json()))
        finding = replace(finding, evidence=tuple(evidence), audit_run_id='', snapshot_id='')
        value = finding.to_dict()
        value.pop('finding_id')
        finding = replace(finding, finding_id=sha256(canonical_json(value).encode()).hexdigest(),
                          audit_run_id=identifier, snapshot_id=context.snapshot.snapshot_id)
        if list(Severity).index(finding.severity) >= list(Severity).index(policy.minimum_severity) and finding.confidence >= policy.minimum_confidence:
            findings.append(finding)
    findings.sort(key=lambda f: (-list(Severity).index(f.severity), f.rule_id, f.entity_type, f.entity_id, f.finding_id))
    status = result.status
    if status in (ResultStatus.PASSED, ResultStatus.FINDINGS):
        status = ResultStatus.FINDINGS if findings else ResultStatus.PASSED
    return replace(result, result_id=str(uuid5(UUID(identifier), metadata.detector_id)), audit_run_id=identifier,
                   started_at=started, completed_at=now(), findings=tuple(findings), finding_count=len(findings), status=status)


def execute_policy(snapshot_id, root=DEFAULT_ROOT, operator='local', policy=None, registry=None):
    if not re.fullmatch(r'[A-Za-z0-9_. -]{1,80}', operator):
        raise ValueError('Operator must be a short explicit label')
    context = load_snapshot(snapshot_id, root)
    policy = load_policy(policy) if not isinstance(policy, AuditPolicy) else AuditPolicy.from_json(policy.to_json())
    registry = DEFAULT_DETECTORS if registry is None else registry
    selected = validate_policy(policy, registry)
    configurations = {d.metadata().detector_id: c.values for d, c in selected}
    context = replace(context, policy_version=policy.policy_version, detector_configuration=configurations)
    identifier = str(uuid4())
    directory = location(root, 'runs', identifier)
    directory.mkdir(parents=True, exist_ok=False)
    run = AuditRun(identifier, now(), None, None, RunStatus.CREATED, FRAMEWORK_VERSION,
                   snapshot_id, context.snapshot.snapshot_hash, policy.policy_version, 'local-cli',
                   {d.metadata().detector_id: d.metadata().detector_version for d, _ in selected}, configurations)
    def save():
        atomic_write(directory / 'run.json', run.to_json().encode(), replace=True)
    save()
    try:
        atomic_write(directory / 'policy.json', policy.to_json().encode())
        provenance = Provenance(identifier, snapshot_id, run.snapshot_hash, FRAMEWORK_VERSION,
                                policy.policy_version, run.created_at, operator, 'local-cli')
        atomic_write(directory / 'provenance.json', provenance.to_json().encode())
        run = replace(run, status=RunStatus.READY)
        save()
        run = replace(run, status=RunStatus.RUNNING, started_at=now())
        save()
        results = []
        failed = False
        for detector, config in selected:
            metadata = detector.metadata()
            started = now()
            try:
                reason = 'strict_failure' if failed and (policy.fail_on_detector_error or not policy.allow_partial_results) else compatibility(context, resolve_requirements(detector, config))
                if reason:
                    result = replace(result_for(metadata, context, config, reason), status=ResultStatus.SKIPPED)
                else:
                    registry.get(metadata.detector_id, metadata.detector_version)
                    result = detector.analyze(context, config)
                result = normalize_result(result, metadata, context, config, policy, identifier, started)
                if result.status == ResultStatus.ERROR:
                    result = replace(result, summary='detector_error')
            except Exception:
                result = normalize_result(replace(result_for(metadata, context, config, 'detector_error'),
                    status=ResultStatus.ERROR), metadata, context, config, policy, identifier, started)
            failed = failed or result.status in (ResultStatus.ERROR, ResultStatus.SKIPPED)
            results.append(result)
        result_dir = location(root, 'results', identifier)
        result_dir.mkdir(parents=True, exist_ok=False)
        for result in results:
            atomic_write(result_dir / (result.detector_id + '.json'), result.to_json().encode())
        logical = {'framework_version': FRAMEWORK_VERSION, 'policy': policy.to_dict(),
                   'snapshot_hash': run.snapshot_hash, 'results': [logical_result(r) for r in results]}
        atomic_write(directory / 'logical-results.json', canonical_json({
            'logical_result_hash': sha256(canonical_json(logical).encode()).hexdigest(),
            'content': logical}).encode())
        run = replace(run, status=RunStatus.FAILED if failed else RunStatus.COMPLETED, completed_at=now())
        save()
        return run, tuple(results)
    except Exception:
        run = replace(run, status=RunStatus.FAILED, completed_at=now())
        save()
        raise ValueError('Audit run failed; inspect local run status') from None


def execute(snapshot_id, root=DEFAULT_ROOT, operator='local'):
    """Backward-compatible single-health Python API."""
    run, results = execute_policy(snapshot_id, root, operator)
    if run.status == RunStatus.FAILED:
        raise ValueError('Audit run failed; inspect local run status')
    return run, results[0]
