"""Local snapshot and audit CLI. No arguments preserves the health contract."""
import argparse
import json
import os
import sys
import pandas as pd
from audit_engine.snapshots import DEFAULT_ROOT, create_snapshot, load_snapshot, location
from audit_engine.models.contracts import AuditResult

def health():
    return {"status": "ok", "service": "auditlens-engine", "pandas_version": pd.__version__}

def main(argv=None):
    parser = argparse.ArgumentParser(description='AuditLens local snapshot framework and Audit Rule Pack v1')
    parser.add_argument('--artifacts-dir', default=str(DEFAULT_ROOT), help='Local artifact root')
    commands = parser.add_subparsers(dest='command')
    commands.add_parser('health', help='Database-free dependency health')
    snapshot = commands.add_parser('snapshot', help='Create or validate a snapshot')
    snapshot.add_argument('action', nargs='?', choices=['inspect'])
    snapshot.add_argument('snapshot_id', nargs='?')
    run = commands.add_parser('run', help='Execute policy-selected detectors on a frozen snapshot')
    run.add_argument('--snapshot', required=True)
    run.add_argument('--policy', help='JSON policy; default: framework.default (health only)')
    run.add_argument('--operator', default=os.environ.get('AUDIT_OPERATOR') or 'local')
    result = commands.add_parser('result', help='Inspect a local framework result')
    result.add_argument('action', choices=['inspect'])
    result.add_argument('audit_run_id')
    detectors = commands.add_parser('detectors', help='Explicit registered detector metadata')
    detectors.add_argument('action', choices=['list', 'inspect'])
    detectors.add_argument('detector_id', nargs='?')
    policy = commands.add_parser('policy', help='Validate JSON policy and detector configuration')
    policy.add_argument('action', choices=['validate'])
    policy.add_argument('path')
    args = parser.parse_args(argv)
    try:
        if args.command in (None, 'health'):
            print(json.dumps(health()))
        elif args.command == 'snapshot':
            if args.action:
                if not args.snapshot_id:
                    parser.error('snapshot inspect requires a snapshot ID')
                print(load_snapshot(args.snapshot_id, args.artifacts_dir).snapshot.to_json())
            else:
                from audit_engine.repositories.source import extract
                value = create_snapshot(extract(), args.artifacts_dir)
                print(f'Snapshot created\nSnapshot ID: {value.snapshot_id}\nTables: {len(value.manifest)}\nRecords: {sum(value.record_counts.values())}\nSHA256: {value.snapshot_hash}')
        elif args.command == 'run':
            from audit_engine.execution import execute_policy
            value, results = execute_policy(args.snapshot, args.artifacts_dir, args.operator, args.policy)
            suffix = ' (framework smoke only)' if args.policy is None else ''
            print(f'Audit run {value.status.value}\nAudit Run ID: {value.audit_run_id}\nSnapshot: {value.snapshot_id}\nFramework: {value.framework_version}\nPolicy: {value.policy_version}\nResults: {len(results)}{suffix}')
            return 1 if value.status.value == 'failed' else 0
        elif args.command == 'detectors':
            from audit_engine.detectors import DEFAULT_DETECTORS
            if args.action == 'inspect':
                print(DEFAULT_DETECTORS.get(args.detector_id).metadata().to_json())
            else:
                print(json.dumps([item.to_dict() for item in DEFAULT_DETECTORS.list()], sort_keys=True))
        elif args.command == 'policy':
            from audit_engine.policy import load_policy
            from audit_engine.detectors import DEFAULT_DETECTORS, validate_policy
            value = load_policy(args.path)
            validate_policy(value, DEFAULT_DETECTORS)
            print(value.to_json())
        else:
            directory = location(args.artifacts_dir, 'results', args.audit_run_id)
            values = []
            for path in sorted(directory.iterdir()):
                if path.is_symlink() or not path.is_file() or path.suffix != '.json':
                    raise ValueError('Result inventory rejected')
                value = AuditResult.from_json(path.read_bytes())
                if value.audit_run_id != args.audit_run_id or path.name != value.detector_id + '.json':
                    raise ValueError('Result identity mismatch')
                values.append(value.to_dict())
            from audit_engine.models.contracts import AuditRun
            run_path = location(args.artifacts_dir, 'runs', args.audit_run_id) / 'run.json'
            if run_path.is_symlink():
                raise ValueError('Run link rejected')
            audit_run = AuditRun.from_json(run_path.read_bytes())
            if audit_run.audit_run_id != args.audit_run_id or set(audit_run.detector_versions) != {v['detector_id'] for v in values}:
                raise ValueError('Incomplete result inventory')
            print(json.dumps(values[0] if len(values) == 1 else values, sort_keys=True))
        return 0
    except (ValueError, OSError, TypeError, KeyError, ArithmeticError):
        # No raw exception details: filesystem paths and source values can be private.
        print('AuditLens command failed: check configuration, artifact ID and integrity. Source extraction also requires Node dependencies and the provisioned reader role.', file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
