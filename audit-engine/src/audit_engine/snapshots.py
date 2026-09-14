"""Canonical content, immutable publication, and independent validation."""
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import UUID, uuid4
from collections.abc import Mapping
from audit_engine.models.contracts import Snapshot, TableManifest, AuditContext
from audit_engine.versioning import SCHEMA_VERSION, FRAMEWORK_VERSION, POLICY_VERSION

SCHEMA = json.loads((Path(__file__).parent / 'repositories/source-schema.json').read_text())
TABLES = tuple(sorted(SCHEMA))
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / 'artifacts'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def safe_id(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError('Invalid artifact ID; expected canonical UUID')
    return value


def location(root, category, identifier):
    safe_id(identifier)
    root = Path(root).resolve()
    path = root / category / identifier
    if path.resolve() != path or not path.resolve().is_relative_to(root):
        raise ValueError('Artifact path escapes root or uses a link')
    return path


def normalize(value):
    if isinstance(value, Mapping):
        return {k: normalize(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError('Timestamp requires timezone')
        return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError('Non-finite decimal')
        return format(value, 'f')
    if value is None or type(value) in (str, bool, int):
        return value
    raise ValueError('Unsupported source value; floating point is not allowed')


def canonical(value):
    return json.dumps(normalize(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def table_bytes(table, rows):
    keys = {'user_roles': ('user_id', 'role_id'), 'role_permissions': ('role_id', 'permission_id')}.get(table, ('id',))
    normalized = []
    for source in rows:
        if set(source) != set(SCHEMA[table]):
            raise ValueError('Source fields do not match approved schema')
        row = dict(source)
        for key, value in row.items():
            if key.endswith('_at') and value is not None:
                row[key] = normalize(datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value)
        if 'amount' in row:
            amount = Decimal(row['amount'])
            if not amount.is_finite() or amount != amount.quantize(Decimal('0.01')):
                raise ValueError('Invalid money precision')
            row['amount'] = format(amount, '.2f')
        row = normalize(row)
        for key in keys:
            safe_id(row[key])
        normalized.append(row)
    normalized.sort(key=lambda r: tuple(r[k] for k in keys))
    ids = [tuple(r[k] for k in keys) for r in normalized]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate source primary key')
    return b''.join(canonical(r) + b'\n' for r in normalized)


def logical_hash(manifest):
    return sha256(canonical({'source_type': 'postgresql', 'schema_version': SCHEMA_VERSION,
                             'manifest': {k: v.to_dict() for k, v in manifest.items()}})).hexdigest()


def atomic_write(path, data, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError('Artifact link rejected')
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            # Atomic no-clobber publication on Windows and POSIX.
            os.link(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def create_snapshot(extraction, root=DEFAULT_ROOT):
    if extraction.source_type != 'postgresql' or extraction.schema_version != SCHEMA_VERSION or set(extraction.tables) != set(TABLES):
        raise ValueError('Unsupported extraction contract')
    payloads = {t: table_bytes(t, extraction.tables[t]) for t in TABLES}
    manifest = {t: TableManifest(len(extraction.tables[t]), sha256(payloads[t]).hexdigest()) for t in TABLES}
    snapshot = Snapshot(str(uuid4()), now(), 'postgresql', SCHEMA_VERSION, manifest, logical_hash(manifest))
    directory = location(root, 'snapshots', snapshot.snapshot_id)
    directory.mkdir(parents=True, exist_ok=False)
    for table, data in payloads.items():
        atomic_write(directory / (table + '.jsonl'), data)
    # Manifest is the commit marker; incomplete directories cannot be loaded.
    atomic_write(directory / 'manifest.json', snapshot.to_json().encode('utf-8'))
    return snapshot


def load_snapshot(identifier, root=DEFAULT_ROOT):
    directory = location(root, 'snapshots', identifier)
    expected = {'manifest.json'} | {t + '.jsonl' for t in TABLES}
    if {p.name for p in directory.iterdir()} != expected or any(p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise ValueError('Invalid snapshot artifact inventory')
    snapshot = Snapshot.from_json((directory / 'manifest.json').read_bytes())
    if snapshot.snapshot_id != identifier or snapshot.schema_version != SCHEMA_VERSION or snapshot.source_type != 'postgresql' or set(snapshot.manifest) != set(TABLES):
        raise ValueError('Invalid snapshot metadata')
    if normalize(datetime.fromisoformat(snapshot.created_at.replace('Z', '+00:00'))) != snapshot.created_at:
        raise ValueError('Invalid snapshot creation time')
    tables = {}
    for table in TABLES:
        data = (directory / (table + '.jsonl')).read_bytes()
        entry = snapshot.manifest[table]
        rows = [json.loads(line) for line in data.splitlines()]
        if entry.rows < 0 or len(rows) != entry.rows or sha256(data).hexdigest() != entry.sha256 or table_bytes(table, rows) != data:
            raise ValueError('Snapshot table integrity validation failed')
        tables[table] = rows
    if not re.fullmatch('[0-9a-f]{64}', snapshot.snapshot_hash) or logical_hash(snapshot.manifest) != snapshot.snapshot_hash:
        raise ValueError('Snapshot hash validation failed')
    return AuditContext(snapshot, tables, POLICY_VERSION, FRAMEWORK_VERSION, {})
