"""Offline contract, determinism, integrity, isolation and CLI regression tests."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
from audit_engine.models.contracts import (
    SourceExtraction, Snapshot, AuditContext, AuditRun, Provenance, AuditResult,
    Finding, Evidence, Severity, RunStatus, ResultStatus,
)
from audit_engine.snapshots import (
    SCHEMA, TABLES, canonical, table_bytes, create_snapshot, load_snapshot,
    location, safe_id, atomic_write,
)
from audit_engine.execution import execute
from audit_engine.repositories.source import extract

ID = '00000000-0000-4000-a000-000000000001'
TIME = '2026-09-14T00:00:00.000000Z'


def sample():
    tables = {t: [] for t in TABLES}
    tables['roles'] = [dict(id=ID, created_at=TIME, updated_at=TIME, code='example', name='Example')]
    return SourceExtraction('postgresql', '1', tables)


class FrameworkTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.snapshot = create_snapshot(sample(), self.root)

    def cli(self, *args, env=None):
        return subprocess.run([sys.executable, '-m', 'audit_engine', '--artifacts-dir', str(self.root), *args],
                              capture_output=True, text=True, env=env, timeout=30)

    def test_all_contract_round_trips(self):
        run, result = execute(self.snapshot.snapshot_id, self.root)
        provenance = Provenance.from_json((self.root / 'runs' / run.audit_run_id / 'provenance.json').read_bytes())
        evidence = Evidence(str(uuid4()), 'roles', {'id': ID}, 'code', 'example', {})
        finding = Finding(str(uuid4()), 'example', 'example.rule', 'Example', 'Contract only',
                          Severity.INFO, 1.0, 'role', ID, (evidence,), self.snapshot.snapshot_id, run.audit_run_id)
        result = replace(result, findings=(finding,), finding_count=1, status=ResultStatus.FINDINGS)
        context = load_snapshot(self.snapshot.snapshot_id, self.root)
        for value in (sample(), self.snapshot, run, provenance, result, finding, evidence, context):
            with self.subTest(contract=type(value).__name__):
                self.assertEqual(type(value).from_json(value.to_json()), value)

    def test_contract_rejects_missing_extra_wrong_type_and_enum(self):
        value = self.snapshot.to_dict()
        for modified in ({}, {**value, 'host': 'private'}, {**value, 'schema_version': 1}):
            with self.assertRaises(ValueError):
                Snapshot.from_dict(modified)
        run, _ = execute(self.snapshot.snapshot_id, self.root)
        with self.assertRaises(ValueError):
            AuditRun.from_dict({**run.to_dict(), 'status': 'bogus'})

    def test_context_deeply_frozen(self):
        context = load_snapshot(self.snapshot.snapshot_id, self.root)
        with self.assertRaises(TypeError):
            context.tables['roles'][0]['name'] = 'changed'
        with self.assertRaises(TypeError):
            context.snapshot.manifest['roles'] = None
        with self.assertRaises(FrozenInstanceError):
            context.policy_version = 'changed'

    def test_hashes_ignore_dictionary_and_row_order_and_snapshot_identity(self):
        row = sample().tables['roles'][0]
        second = {**row, 'id': '00000000-0000-4000-a000-000000000002'}
        tables = dict(sample().tables)
        tables['roles'] = [second, dict(reversed(list(row.items())))]
        one = create_snapshot(SourceExtraction('postgresql', '1', tables), self.root)
        tables['roles'] = list(reversed(tables['roles']))
        two = create_snapshot(SourceExtraction('postgresql', '1', dict(reversed(list(tables.items())))), self.root)
        self.assertEqual(one.snapshot_hash, two.snapshot_hash)
        self.assertEqual(one.table_hashes, two.table_hashes)
        self.assertNotEqual(one.snapshot_id, two.snapshot_id)

    def test_timestamp_offsets_normalized_without_losing_microseconds(self):
        row = dict(sample().tables['roles'][0])
        row['created_at'] = '2026-09-14T07:00:00.123456+07:00'
        data = table_bytes('roles', [row])
        self.assertIn(b'2026-09-14T00:00:00.123456Z', data)
        row['created_at'] = '2026-09-14T00:00:00.123456Z'
        self.assertEqual(data, table_bytes('roles', [row]))

    def test_exact_decimal_and_nested_key_normalization(self):
        self.assertEqual(canonical({'z': {'b': Decimal('1234567890123456.78'), 'a': True}}),
                         b'{"z":{"a":true,"b":"1234567890123456.78"}}')
        for bad in (1.2, float('nan'), Decimal('Infinity')):
            with self.assertRaises(ValueError):
                canonical(bad)

    def test_money_normalization(self):
        row = {field: None for field in SCHEMA['invoices']}
        row.update(id=ID, amount='1234567890123456.7')
        self.assertIn(b'1234567890123456.70', table_bytes('invoices', [row]))
        row['amount'] = '1.001'
        with self.assertRaises(ValueError):
            table_bytes('invoices', [row])

    def test_duplicate_primary_keys_rejected(self):
        with self.assertRaises(ValueError):
            table_bytes('roles', sample().tables['roles'] * 2)

    def test_composite_primary_key_order(self):
        row = dict(user_id=ID, role_id=ID, created_at=TIME)
        other = {**row, 'role_id': '00000000-0000-4000-a000-000000000002'}
        self.assertEqual(table_bytes('user_roles', [row, other]), table_bytes('user_roles', [other, row]))

    def test_unapproved_table_or_column_rejected(self):
        with self.assertRaises(ValueError):
            create_snapshot(SourceExtraction('postgresql', '1', {**sample().tables, 'extra': []}), self.root)
        with self.assertRaises(ValueError):
            table_bytes('roles', [{**sample().tables['roles'][0], 'hidden_label': True}])

    def test_tampered_value_rejected(self):
        path = self.root / 'snapshots' / self.snapshot.snapshot_id / 'roles.jsonl'
        path.write_bytes(path.read_bytes().replace(b'Example', b'Changed'))
        with self.assertRaises(ValueError):
            load_snapshot(self.snapshot.snapshot_id, self.root)

    def test_missing_table_rejected(self):
        (self.root / 'snapshots' / self.snapshot.snapshot_id / 'roles.jsonl').unlink()
        with self.assertRaises(ValueError):
            load_snapshot(self.snapshot.snapshot_id, self.root)

    def test_missing_manifest_rejected(self):
        (self.root / 'snapshots' / self.snapshot.snapshot_id / 'manifest.json').unlink()
        with self.assertRaises(ValueError):
            load_snapshot(self.snapshot.snapshot_id, self.root)

    def test_counts_hash_and_metadata_tampering_rejected(self):
        path = self.root / 'snapshots' / self.snapshot.snapshot_id / 'manifest.json'
        original = self.snapshot.to_dict()
        variants = [{**original, 'snapshot_hash': '0' * 64}, {**original, 'schema_version': '2'},
                    {**original, 'snapshot_id': str(uuid4())}, {**original, 'created_at': ''}]
        counts = json.loads(json.dumps(original))
        counts['manifest']['roles']['rows'] = 5
        variants.append(counts)
        for value in variants:
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                load_snapshot(self.snapshot.snapshot_id, self.root)

    def test_unsafe_ids_rejected(self):
        for value in ('../../test', '..\\..\\test', '/foo', 'C:\\foo', '', ID.upper(), '../' + ID):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_id(value)

    def test_no_overwrite(self):
        path = self.root / 'immutable.json'
        atomic_write(path, b'original')
        with self.assertRaises(FileExistsError):
            atomic_write(path, b'replaced')
        self.assertEqual(path.read_bytes(), b'original')
        with patch('audit_engine.snapshots.uuid4', return_value=self.snapshot.snapshot_id):
            with self.assertRaises(FileExistsError):
                create_snapshot(sample(), self.root)

    def test_link_path_rejected(self):
        with patch('audit_engine.snapshots.Path.resolve', side_effect=[self.root, self.root / 'outside']):
            with self.assertRaises(ValueError):
                location(self.root, 'snapshots', ID)

    def test_run_result_and_neutral_provenance(self):
        run, result = execute(self.snapshot.snapshot_id, self.root)
        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual(result.finding_count, 0)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.status, ResultStatus.PASSED)
        p = Provenance.from_json((self.root / 'runs' / run.audit_run_id / 'provenance.json').read_bytes())
        self.assertEqual(p.operator, 'local')
        self.assertEqual(p.execution_environment, 'local-cli')
        self.assertEqual(result.snapshot_hash, run.snapshot_hash)
        self.assertEqual(AuditResult.from_json((self.root / 'results' / run.audit_run_id / 'framework.health.json').read_bytes()), result)

    def test_repeat_execution_reproduces_semantic_result(self):
        _, one = execute(self.snapshot.snapshot_id, self.root)
        _, two = execute(self.snapshot.snapshot_id, self.root)
        for field in ('summary', 'status', 'findings', 'snapshot_hash', 'detector_version', 'policy_version', 'detector_configuration'):
            self.assertEqual(getattr(one, field), getattr(two, field))

    def test_failed_detector_records_failed_run(self):
        with patch('audit_engine.execution.check', side_effect=RuntimeError('private detail')):
            with self.assertRaisesRegex(ValueError, 'Audit run failed'):
                execute(self.snapshot.snapshot_id, self.root)
        paths = list((self.root / 'runs').glob('*/run.json'))
        self.assertEqual(len(paths), 1)
        run = AuditRun.from_json(paths[0].read_bytes())
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertIsNotNone(run.completed_at)
        self.assertNotIn('private detail', paths[0].read_text())

    def test_operator_is_explicit_and_bounded(self):
        run, _ = execute(self.snapshot.snapshot_id, self.root, 'reviewer-1')
        self.assertIn('reviewer-1', (self.root / 'runs' / run.audit_run_id / 'provenance.json').read_text())
        with self.assertRaises(ValueError):
            execute(self.snapshot.snapshot_id, self.root, 'postgres://user:password@host')

    def test_cli_help_health_and_default(self):
        for args in (('--help',), ('health',), ()):
            result = self.cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cli_snapshot_inspect_run_result_inspect(self):
        result = self.cli('snapshot', 'inspect', self.snapshot.snapshot_id)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['snapshot_hash'], self.snapshot.snapshot_hash)
        result = self.cli('run', '--snapshot', self.snapshot.snapshot_id)
        self.assertEqual(result.returncode, 0, result.stderr)
        run_id = next((self.root / 'runs').iterdir()).name
        self.assertEqual(self.cli('result', 'inspect', run_id).returncode, 0)

    def test_cli_invalid_snapshot(self):
        for identifier in ('../../test', str(uuid4())):
            self.assertNotEqual(self.cli('run', '--snapshot', identifier).returncode, 0)

    def test_cli_extraction_failure_sanitized(self):
        result = self.cli('snapshot', env={**os.environ, 'AUDIT_SOURCE_DATABASE_URL': 'invalid-secret-sentinel'})
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('invalid-secret-sentinel', result.stdout + result.stderr)

    def test_source_transport_failure_sanitized(self):
        with patch('audit_engine.repositories.source.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'private')):
            with self.assertRaisesRegex(ValueError, 'Source extraction failed') as error:
                extract()
        self.assertNotIn('private', str(error.exception))

    def test_source_transport_exact_event_numbers_and_fixed_command(self):
        payload = sample().to_dict()
        payload['tables']['audit_logs'] = [{'before_data': '{"amount":1234567890123456.78}', 'after_data': None}]
        with patch('audit_engine.repositories.source.subprocess.run', return_value=subprocess.CompletedProcess([], 0, json.dumps(payload).encode())) as transport:
            extracted = extract()
        self.assertEqual(extracted.tables['audit_logs'][0]['before_data']['amount'], Decimal('1234567890123456.78'))
        self.assertEqual(len(transport.call_args.args[0]), 2)
        self.assertEqual(transport.call_args.args[0][0], 'node')

    def test_bridge_dotenv_uses_repository_root(self):
        import re
        package = Path(importlib.import_module('audit_engine').__file__).parent
        bridge = package / 'repositories/extract.mjs'
        relative = re.search(r"dotenv.config\(\{ path: new URL\('([^']+)'", bridge.read_text()).group(1)
        self.assertEqual((bridge.parent / relative).resolve(), package.parents[2] / '.env')

    def test_ground_truth_and_database_isolation(self):
        package = Path(importlib.import_module('audit_engine').__file__).parent
        for path in list(package.rglob('*.py')) + list(package.rglob('*.mjs')):
            content = path.read_text()
            for forbidden in ('ground-truth', 'groundTruth', 'generators/', 'sample-data', 'fixture-policy', 'anomalies.js'):
                self.assertNotIn(forbidden, content, str(path))
        for path in [package / 'execution.py', package / 'analyzers/health.py']:
            content = path.read_text()
            for forbidden in ('repositories.source', 'subprocess', 'DATABASE_URL', 'import pg', 'psycopg'):
                self.assertNotIn(forbidden, content)
        bridge = (package / 'repositories/extract.mjs').read_text()
        self.assertIn('REPEATABLE READ READ ONLY', bridge)
        self.assertIn('SET LOCAL ROLE auditlens_source_reader', bridge)
        for statement in ('INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'ALTER ', 'DROP ', 'GRANT ', 'TRUNCATE ', 'SELECT *'):
            self.assertNotIn(statement, bridge)


if __name__ == '__main__':
    unittest.main()
