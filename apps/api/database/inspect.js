import { readdir } from 'node:fs/promises';
import { TABLES } from './generators/core.js';

// No Knex migrator calls: even an empty database remains empty.
export async function inspectDatabase(db) {
  const expected = (await readdir(new URL('./migrations/', import.meta.url))).filter(name => name.endsWith('.js')).sort();
  return db.transaction(async trx => {
    await trx.raw('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');
    const identity = (await trx.raw('SELECT current_database() AS database, current_setting(\'server_version\') AS version')).rows[0];
    const schemas = (await trx.raw("SELECT nspname FROM pg_catalog.pg_namespace WHERE nspname IN ('business','audit')")).rows.map(row => row.nspname);
    const tables = (await trx.raw("SELECT n.nspname AS schema, c.relname AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p') AND n.nspname IN ('business','audit','public')")).rows;
    const exists = (schema, name) => tables.some(row => row.schema === schema && row.name === name);
    const metadata = { migrations: exists('public', 'knex_migrations'), lock: exists('public', 'knex_migrations_lock') };
    const applied = metadata.migrations ? (await trx.withSchema('public').table('knex_migrations').select('name').orderBy('id')).map(row => row.name) : [];
    const pending = expected.filter(name => !applied.includes(name));
    const unknown = applied.filter(name => !expected.includes(name));
    const missingTables = TABLES.filter(name => !exists('business', name));
    return { connected: true, ...identity, schemas, businessTables: TABLES.filter(name => exists('business', name)), missingTables, metadata, expected, applied, pending, unknown,
      ready: schemas.length === 2 && missingTables.length === 0 && metadata.migrations && metadata.lock && pending.length === 0 && unknown.length === 0 };
  });
}
