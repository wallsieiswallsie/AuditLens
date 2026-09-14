"""Local run lifecycle. Database-free execution from validated, frozen data."""
from dataclasses import replace
from uuid import uuid4, uuid5, UUID
import re
from audit_engine.analyzers.health import check
from audit_engine.models.contracts import AuditRun, Provenance, AuditResult, RunStatus, ResultStatus
from audit_engine.snapshots import load_snapshot, location, atomic_write, now, DEFAULT_ROOT
from audit_engine.versioning import FRAMEWORK_VERSION, POLICY_VERSION, HEALTH_VERSION


def execute(snapshot_id, root=DEFAULT_ROOT, operator='local'):
    if not re.fullmatch(r'[A-Za-z0-9_. -]{1,80}', operator):
        raise ValueError('Operator must be a short explicit label')
    context = load_snapshot(snapshot_id, root)
    identifier = str(uuid4())
    directory = location(root, 'runs', identifier)
    directory.mkdir(parents=True, exist_ok=False)
    run = AuditRun(identifier, now(), None, None, RunStatus.CREATED, FRAMEWORK_VERSION,
                   snapshot_id, context.snapshot.snapshot_hash, POLICY_VERSION, 'local-cli',
                   {'framework.health': HEALTH_VERSION}, {})
    def save():
        atomic_write(directory / 'run.json', run.to_json().encode(), replace=True)
    save()
    try:
        provenance = Provenance(identifier, snapshot_id, run.snapshot_hash, FRAMEWORK_VERSION,
                                POLICY_VERSION, run.created_at, operator, 'local-cli')
        atomic_write(directory / 'provenance.json', provenance.to_json().encode())
        run = replace(run, status=RunStatus.READY)
        save()
        run = replace(run, status=RunStatus.RUNNING, started_at=now())
        save()
        summary = check(context)
        result = AuditResult(str(uuid5(UUID(identifier), 'framework.health')), identifier,
                             'framework.health', HEALTH_VERSION, POLICY_VERSION, ResultStatus.PASSED,
                             summary, 0, run.started_at, now(), snapshot_id, run.snapshot_hash, (), {})
        result_dir = location(root, 'results', identifier)
        result_dir.mkdir(parents=True, exist_ok=False)
        atomic_write(result_dir / 'framework.health.json', result.to_json().encode())
        run = replace(run, status=RunStatus.COMPLETED, completed_at=now())
        save()
        return run, result
    except Exception:
        run = replace(run, status=RunStatus.FAILED, completed_at=now())
        save()
        raise ValueError('Audit run failed; inspect local run status') from None
