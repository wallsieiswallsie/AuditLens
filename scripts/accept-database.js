import { mkdtemp, writeFile, unlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createServer } from 'node:net';
import { randomBytes } from 'node:crypto';
import knex from 'knex';
import { acceptDatabase } from '../apps/api/database/acceptance.js';

// Deliberately accepts NO target URL. Every invocation owns a brand-new cluster.
// PG_BIN is a directory of PostgreSQL 17+ binaries; otherwise use PATH.
const binary = name => process.env.PG_BIN ? join(process.env.PG_BIN, name + (process.platform === 'win32' ? '.exe' : '')) : name;
const run = (name, args, silent = false) => {
  const result = spawnSync(binary(name), args, { encoding: 'utf8', timeout: 60000, windowsHide: true, stdio: silent ? 'ignore' : 'pipe' });
  if (result.status !== 0) {
    // PostgreSQL utility diagnostics do not include the password-file contents.
    if (!silent) console.error(result.stderr || result.error?.code || `${name} exited ${result.status}`);
    throw new Error(`${name} failed; inspect the temporary cluster log (no existing target was used)`);
  }
};
let db, started = false, directory;
try {
  if (process.env.NODE_ENV === 'production') throw new Error('Disposable acceptance refuses NODE_ENV=production');
  run('initdb', ['--version']);
  directory = await mkdtemp(join(tmpdir(), 'auditlens-acceptance-'));
  const data = join(directory, 'data');
  const password = randomBytes(24).toString('hex');
  const passwordFile = join(directory, 'password');
  await writeFile(passwordFile, password, { mode: 0o600 });
  try { run('initdb', ['-D', data, '-U', 'auditlens_acceptance_admin', '--pwfile', passwordFile, '--auth=scram-sha-256', '--encoding=UTF8', '--locale=C']); }
  finally { await unlink(passwordFile); }
  const socket = createServer();
  await new Promise(resolve => socket.listen(0, '127.0.0.1', resolve));
  const port = socket.address().port;
  await new Promise(resolve => socket.close(resolve));
  run('pg_ctl', ['-D', data, '-l', join(directory, 'postgres.log'), '-o', `-h 127.0.0.1 -p ${port}`, '-w', 'start'], true);
  started = true;
  const connection = `postgresql://auditlens_acceptance_admin:${password}@127.0.0.1:${port}/auditlens`;
  const adminUrl = new URL(connection); adminUrl.pathname = '/postgres';
  const admin = knex({ client: 'pg', connection: adminUrl.href, pool: { min: 0, max: 1 }, log: { error: () => {} } });
  try { await admin.raw('CREATE DATABASE auditlens'); } finally { await admin.destroy(); }
  db = knex({ client: 'pg', connection, log: { error: () => {} }, pool: { min: 0, max: 5 }, migrations: {
    directory: fileURLToPath(new URL('../apps/api/database/migrations/', import.meta.url)), schemaName: 'public', tableName: 'knex_migrations' } });
  const version = (await db.raw('SELECT version() AS version')).rows[0].version;
  console.log('Confirmed disposable target: newly initialized private cluster, loopback, random port; ignores DATABASE_URL.');
  const result = await acceptDatabase(db, connection);
  console.log(JSON.stringify({ date: new Date().toISOString(), environment: version, ...result }, null, 2));
} catch (error) {
  // Assertions may contain source rows but connection errors can contain credentials: never print arbitrary errors.
  console.error('Disposable PostgreSQL acceptance FAILED or NOT RUN. Stage:', error.code || error.name, ';',
    error.message?.startsWith('Acceptance command failed:') ? error.message : 'check prerequisites and temporary cluster log');
  process.exitCode = 1;
} finally {
  if (db) await db.destroy();
  if (started) {
    try { run('pg_ctl', ['-D', join(directory, 'data'), '-m', 'fast', '-w', 'stop'], true); console.log('Disposable cluster stopped.'); }
    catch { console.error('Temporary cluster stop failed; stop it using pg_ctl and the data directory below.'); process.exitCode = 1; }
  }
  if (directory) console.log(`Temporary cluster files retained for diagnosis: ${resolve(directory)}`);
}
