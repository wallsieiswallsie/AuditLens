"""Local/operator-only Rule Pack readiness. No database access or detector execution."""
import argparse
from pathlib import Path
import tempfile
from audit_engine.detectors import DEFAULT_DETECTORS, compatibility, resolve_requirements, validate_policy
from audit_engine.policy import load_policy
from audit_engine.snapshots import atomic_write, load_snapshot

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--artifacts-dir', required=True)
parser.add_argument('--snapshot', required=True)
args = parser.parse_args()
try:
    policy = load_policy(Path(__file__).resolve().parents[1] / 'audit-engine/policies/rulepack-v1.json')
    selected = validate_policy(policy, DEFAULT_DETECTORS)
    context = load_snapshot(args.snapshot, args.artifacts_dir)
    if any(compatibility(context, resolve_requirements(d, c)) for d, c in selected):
        raise ValueError('Incompatible snapshot')
    # Exercise actual atomic hard-link publication on the selected filesystem.
    with tempfile.TemporaryDirectory(prefix='.readiness-', dir=args.artifacts_dir) as directory:
        atomic_write(Path(directory) / 'probe', b'ready')
    print('READY: engine, registry, Rule Pack policy, snapshot integrity/schema, atomic artifact output')
    print('Data semantics still require audit execution; invoice references must be integers or null.')
except (ValueError, OSError, TypeError, KeyError):
    parser.exit(1, 'NOT READY: check policy, snapshot integrity/requirements and artifact filesystem permissions\n')
