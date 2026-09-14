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
    parser = argparse.ArgumentParser(description='AuditLens local snapshot framework (no business detectors)')
    parser.add_argument('--artifacts-dir', default=str(DEFAULT_ROOT), help='Local artifact root')
    commands = parser.add_subparsers(dest='command')
    commands.add_parser('health', help='Database-free dependency health')
    snapshot = commands.add_parser('snapshot', help='Create or validate a snapshot')
    snapshot.add_argument('action', nargs='?', choices=['inspect'])
    snapshot.add_argument('snapshot_id', nargs='?')
    run = commands.add_parser('run', help='Execute framework.health on a frozen snapshot')
    run.add_argument('--snapshot', required=True)
    run.add_argument('--operator', default=os.environ.get('AUDIT_OPERATOR') or 'local')
    result = commands.add_parser('result', help='Inspect a local framework result')
    result.add_argument('action', choices=['inspect'])
    result.add_argument('audit_run_id')
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
            from audit_engine.execution import execute
            value, result = execute(args.snapshot, args.artifacts_dir, args.operator)
            print(f'Audit run completed\nAudit Run ID: {value.audit_run_id}\nSnapshot: {value.snapshot_id}\nFramework: {value.framework_version}\nPolicy: {value.policy_version}\nResults: 1 ({result.status.value}; framework smoke only)')
        else:
            path = location(args.artifacts_dir, 'results', args.audit_run_id) / 'framework.health.json'
            if path.is_symlink():
                raise ValueError('Result link rejected')
            value = AuditResult.from_json(path.read_bytes())
            if value.audit_run_id != args.audit_run_id:
                raise ValueError('Result identity mismatch')
            print(value.to_json())
        return 0
    except (ValueError, OSError, TypeError, KeyError, ArithmeticError):
        # No raw exception details: filesystem paths and source values can be private.
        print('AuditLens command failed: check configuration, artifact ID and integrity. Source extraction also requires Node dependencies and the provisioned reader role.', file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
