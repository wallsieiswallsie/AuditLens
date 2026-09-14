import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import pg from 'pg';
import { randomBytes } from 'node:crypto';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { generate } from './generators/index.js';
import { TABLES } from './generators/core.js';
import { validate } from './validation/validate.js';
import { inspectDatabase } from './inspect.js';
import { provisionReader, READER } from './security/source-reader.js';

// Called only by the runner after it creates a new private PostgreSQL cluster.
export async function acceptDatabase(db, connection) {
  const results = {};
  const root = fileURLToPath(new URL('../../../', import.meta.url));
  const command = (script, args = []) => {
    const result = spawnSync(process.execPath, [script, ...args], { cwd: root, encoding: 'utf8', timeout: 120000,
      env: { ...process.env, NODE_ENV: 'development', DATABASE_URL: connection, AUDITLENS_DATA_SEED: '20260914', AUDITLENS_ALLOW_LOCAL_RESET: 'YES' } });
    assert.equal(result.status, 0, `Acceptance command failed: ${script} ${args.join(' ')} (output suppressed)`);
  };
  const readFixture = async () => db.transaction(async trx => {
    await trx.raw('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');
    const tables = {};
    for (const name of TABLES) tables[name] = JSON.parse(JSON.stringify(await trx.withSchema('business').table(name).select('*')));
    return tables;
  });
  const fixture = generate();
  for (const [file, key] of [['dataset-manifest', 'manifest'], ['ground-truth', 'groundTruth'], ['fixture-policy', 'policy']]) {
    assert.deepEqual(JSON.parse(await readFile(new URL(`./sample-data/${file}.json`, import.meta.url))), fixture[key]);
  }
  console.log('Acceptance: empty inspection and migration workflow');
  const before = await inspectDatabase(db);
  assert.equal(before.ready, false); assert.deepEqual(before.metadata, { migrations: false, lock: false });
  assert.deepEqual(await inspectDatabase(db), before);
  command('scripts/check-database.js'); command('scripts/inspect-database.js');
  assert.deepEqual(await inspectDatabase(db), before);
  results.emptyInspection = 'PASS: no schema or migration metadata created';
  await db.migrate.latest();
  assert.equal((await inspectDatabase(db)).ready, true);
  command('scripts/dataset-database.js', ['status']);
  command('scripts/dataset-database.js', ['seed']);
  command('scripts/dataset-database.js', ['validate']);
  const first = validate({ ...fixture, tables: await readFixture() });
  command('scripts/rollback-database.js');
  assert.deepEqual((await inspectDatabase(db)).schemas, []);
  await db.migrate.latest();
  command('scripts/dataset-database.js', ['seed']);
  const second = validate({ ...fixture, tables: await readFixture() });
  assert.deepEqual(second, first);
  command('scripts/dataset-database.js', ['reset']);
  for (const name of TABLES) assert.equal(Number((await db.withSchema('business').table(name).count('* AS n').first()).n), 0);
  command('scripts/dataset-database.js', ['seed']);
  command('scripts/dataset-database.js', ['validate']);
  assert.deepEqual(validate({ ...fixture, tables: await readFixture() }), first);
  results.workflow = 'PASS: migrate, seed, validate, rollback/reapply, reseed, reset/reseed and deterministic parity';
  results.fixture = { ...first, tableHashes: fixture.manifest.tableHashes };

  const constraints = [
    ['foreign key', '23503', trx => trx('business.users').where({ id: fixture.tables.users[0].id }).update({ employee_id: '00000000-0000-4000-a000-000000000000' })],
    ['status', '23514', trx => trx('business.invoices').where({ id: fixture.tables.invoices[0].id }).update({ status: 'invalid' })],
    ['amount', '23514', trx => trx('business.payments').where({ id: fixture.tables.payments[0].id }).update({ amount: '-1.00' })],
    ['payment confirmation', '23514', trx => trx('business.payments').where({ id: fixture.tables.payments[0].id }).update({ confirmed_by: null })],
    ['unique business key', '23505', trx => trx('business.employees').where({ id: fixture.tables.employees[0].id }).update({ employee_number: fixture.tables.employees[1].employee_number })],
    ['employment dates', '23514', trx => trx('business.employees').where({ id: fixture.tables.employees[0].id }).update({ status: 'inactive', ended_at: '2000-01-01T00:00:00Z' })],
    ['not null', '23502', trx => trx('business.vendors').where({ id: fixture.tables.vendors[0].id }).update({ name: null })],
  ];
  console.log('Acceptance: real constraint rejections');
  results.constraints = {};
  for (const [name, code, operation] of constraints) {
    await assert.rejects(db.transaction(async trx => { await operation(trx); throw new Error('Constraint unexpectedly accepted'); }), error => error.code === code);
    results.constraints[name] = `PASS (${code})`;
  }
  console.log('Acceptance: reader provisioning and permission rejections');
  await provisionReader(db); await provisionReader(db); // Reprovisioning is idempotent.
  const password = randomBytes(24).toString('hex');
  await db.raw(`CREATE ROLE auditlens_acceptance_login LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD ${pg.escapeLiteral(password)}`);
  await db.raw('GRANT ?? TO auditlens_acceptance_login WITH INHERIT FALSE, SET TRUE', [READER]);
  const readerUrl = new URL(connection); readerUrl.username = 'auditlens_acceptance_login'; readerUrl.password = password;
  const reader = new pg.Client({ connectionString: readerUrl.href });
  await reader.connect();
  results.reader = {};
  try {
    await reader.query('SET ROLE auditlens_source_reader');
    const identity = (await reader.query('SELECT current_user, session_user')).rows[0];
    assert.equal(identity.current_user, READER); assert.equal(identity.session_user, 'auditlens_acceptance_login');
    for (const name of TABLES) assert.equal(Number((await reader.query(`SELECT count(*) AS n FROM business.${name}`)).rows[0].n), fixture.manifest.counts[name]);
    results.reader.SELECT = 'PASS: all eleven approved tables via non-superuser login and SET ROLE';
    console.log('Acceptance: local CLI snapshots and database-free audit execution');
    const localPython = join(root, 'audit-engine', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
    const framework = spawnSync(process.env.AUDITLENS_TEST_PYTHON || (existsSync(localPython) ? localPython : 'python'),
      ['audit-engine/tests/accept_snapshot.py'], { cwd: root, encoding: 'utf8', timeout: 240000, windowsHide: true,
        env: { ...process.env, AUDIT_SOURCE_DATABASE_URL: readerUrl.href, DATABASE_URL: 'disabled-admin-fallback',
          PYTHONPATH: join(root, 'audit-engine/src') } });
    assert.equal(framework.status, 0, 'Acceptance command failed: Python snapshot framework (output suppressed)');
    results.framework = JSON.parse(framework.stdout);
    assert.deepEqual(validate({ ...fixture, tables: await readFixture() }), first);
    results.framework.sourceUnchanged = 'PASS: all existing fixture hashes unchanged after extraction';
    const denied = async (name, sql) => {
      await reader.query('BEGIN');
      try { await assert.rejects(reader.query(sql), error => error.code === '42501'); results.reader[name] = 'PASS: denied (42501)'; }
      finally { await reader.query('ROLLBACK'); }
    };
    for (const [name, sql] of [
      ['INSERT', 'INSERT INTO business.vendors SELECT * FROM business.vendors LIMIT 1'],
      ['UPDATE', 'UPDATE business.users SET status=status'],
      ['DELETE', 'DELETE FROM business.payments'],
      ['TRUNCATE', 'TRUNCATE business.audit_logs'],
      ['CREATE business', 'CREATE TABLE business.reader_probe(id integer)'],
      ['CREATE public', 'CREATE TABLE public.reader_probe(id integer)'],
      ['CREATE audit', 'CREATE TABLE audit.reader_probe(id integer)'],
      ['CREATE SCHEMA', 'CREATE SCHEMA reader_probe'],
      ['CREATE TEMP', 'CREATE TEMP TABLE reader_probe(id integer)'],
      ['ALTER', 'ALTER TABLE business.users ADD COLUMN reader_probe integer'],
      ['DROP', 'DROP TABLE business.audit_logs'],
      ['migration metadata', 'SELECT * FROM public.knex_migrations'],
    ]) await denied(name, sql);
    // Newly created tables are not automatically added to the extraction allowlist.
    await db.raw('CREATE TABLE business.future_probe(id integer)');
    await db.raw('CREATE TABLE audit.future_probe(id integer)');
    await db.raw('CREATE FUNCTION business.future_probe_fn() RETURNS integer LANGUAGE sql SECURITY DEFINER AS $$ SELECT 1 $$');
    await denied('future table SELECT', 'SELECT * FROM business.future_probe');
    await denied('audit SELECT', 'SELECT * FROM audit.future_probe');
    await denied('audit UPDATE', 'UPDATE audit.future_probe SET id=1');
    await denied('audit DROP', 'DROP TABLE audit.future_probe');
    await denied('function EXECUTE', 'SELECT business.future_probe_fn()');
    await db.raw('DROP FUNCTION business.future_probe_fn()');
    await db.raw('DROP TABLE business.future_probe');
    await db.raw('DROP TABLE audit.future_probe');
  } finally { await reader.end(); }
  assert.deepEqual(validate({ ...fixture, tables: await readFixture() }), first);
  assert.equal((await db.raw("SELECT count(*)::int AS n FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='audit' AND c.relkind IN ('r','p')")).rows[0].n, 0);
  assert.equal((await inspectDatabase(db)).ready, true);
  results.integrityAfterDenials = 'PASS: source hashes unchanged; audit has no tables';
  return results;
}
