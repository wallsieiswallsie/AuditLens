import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { build } from 'vite';
import { readConfig, requireDatabaseUrl } from '../apps/api/src/config/env.js';
import { normalizeApiUrl, apiUrl } from '../apps/web/src/config/api.js';

const root = fileURLToPath(new URL('../', import.meta.url));
const connection = 'postgresql://dev:TEST_ONLY@127.0.0.1:5432/auditlens';

test('database URL validation is required only for database access and errors omit credentials', () => {
  assert.equal(readConfig({ DATABASE_URL: connection }).database, connection);
  assert.equal(requireDatabaseUrl({ DATABASE_URL: connection }), connection);
  assert.doesNotThrow(() => readConfig({}));
  for (const value of [undefined, '', ' ']) assert.throws(() => requireDatabaseUrl({ DATABASE_URL: value }), /Missing required environment variable: DATABASE_URL/);
  for (const value of ['invalid-TEST_ONLY', 'https://dev:TEST_ONLY@localhost']) {
    assert.throws(() => requireDatabaseUrl({ DATABASE_URL: value }), error => error.message.startsWith('Invalid DATABASE_URL') && !error.message.includes('TEST_ONLY'));
  }
});

test('Knex receives the exact PostgreSQL URL', () => {
  const result = spawnSync(process.execPath, ['--input-type=module', '-e',
    "import config from './apps/api/database/knexfile.js'; import knex from 'knex'; const db=knex(config); if(config.connection!==process.env.DATABASE_URL || db.client.connectionSettings.host!=='127.0.0.1' || db.client.connectionSettings.database!=='auditlens' || db.client.connectionSettings.password!=='TEST_ONLY') process.exit(1); await db.destroy();"],
    { cwd: root, env: { ...process.env, DATABASE_URL: connection }, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
});

test('all database command entry points fail clearly without the URL', () => {
  for (const args of [['scripts/check-database.js'], ['scripts/inspect-database.js'], ['scripts/rollback-database.js'], ['scripts/provision-reader.js'], ...['seed','reset','validate','status'].map(mode => ['scripts/dataset-database.js', mode]), ['node_modules/knex/bin/cli.js','--knexfile','apps/api/database/knexfile.js','migrate:latest']]) {
    const result = spawnSync(process.execPath, args, { cwd: root, env: { ...process.env, DATABASE_URL: '' }, encoding: 'utf8' });
    assert.notEqual(result.status, 0);
    assert.match(result.stdout + result.stderr, /Missing required environment variable: DATABASE_URL/);
  }
});

test('frontend URL normalization and path joining', () => {
  for (const value of ['http://localhost:3001', 'http://localhost:3001/', ' http://localhost:3001/// ']) {
    assert.equal(normalizeApiUrl(value), 'http://localhost:3001');
    assert.equal(apiUrl('/health', value), 'http://localhost:3001/health');
  }
  assert.equal(apiUrl('health','https://api.example.test/v1/'), 'https://api.example.test/v1/health');
  assert.throws(() => normalizeApiUrl(), /Missing required environment variable: API_URL/);
  for (const value of ['bad', 'ftp://example.test', 'https://user:secret@example.test', 'https://example.test?x=1']) assert.throws(() => normalizeApiUrl(value), /Invalid API_URL/);
});

test('production application and env probe expose public API_URL without server secrets', async () => {
  const values = { API_URL: 'https://public-api.example.test/', DATABASE_URL: connection, AUDIT_SOURCE_DATABASE_URL: 'postgresql://reader:READER_SENTINEL_98765@localhost/auditlens', JWT_ACCESS_SECRET: 'ACCESS_SENTINEL_98765', JWT_REFRESH_SECRET: 'REFRESH_SENTINEL_98765', VITE_UNRELATED_SECRET: 'UNRELATED_SENTINEL_98765' };
  const previous = Object.fromEntries(Object.keys(values).map(key => [key, process.env[key]]));
  Object.assign(process.env, values);
  try {
    const options = { root: fileURLToPath(new URL('../apps/web/', import.meta.url)), configFile: fileURLToPath(new URL('../apps/web/vite.config.js', import.meta.url)), logLevel: 'silent', build: { write: false } };
    const app = await build(options);
    const probe = await build({ ...options, plugins: [{ name: 'env-probe', resolveId: id => id === 'env-probe' ? id : undefined, load: id => id === 'env-probe' ? 'globalThis.probe = [import.meta.env, import.meta.env.API_URL, import.meta.env.DATABASE_URL, import.meta.env.AUDIT_SOURCE_DATABASE_URL, import.meta.env.JWT_ACCESS_SECRET, import.meta.env.JWT_REFRESH_SECRET];' : undefined }], build: { write: false, rollupOptions: { input: 'env-probe' } } });
    for (const result of [app, probe]) {
      const code = result.output.map(item => item.code || item.source).join('\n');
      assert.ok(code.includes('https://public-api.example.test'));
      for (const key of ['DATABASE_URL','AUDIT_SOURCE_DATABASE_URL','JWT_ACCESS_SECRET','JWT_REFRESH_SECRET','VITE_UNRELATED_SECRET']) assert.ok(!code.includes(values[key]), key + ' leaked');
      assert.ok(!code.includes('READER_SENTINEL_98765'));
    }
  } finally {
    for (const [key, value] of Object.entries(previous)) { if (value === undefined) delete process.env[key]; else process.env[key] = value; }
  }
});
