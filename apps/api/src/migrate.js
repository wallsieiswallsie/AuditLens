// Resolve migrations relative to this module, independent of Railway's working directory.
import knex from 'knex';

let db;
try {
  const { default: config } = await import('../database/knexfile.js');
  db = knex({ ...config, log: { warn: () => {}, error: () => {}, debug: () => {}, deprecate: () => {} } });
  const [, applied] = await db.migrate.latest();
  console.log(`API migrations ready: ${applied.length} applied`);
} catch {
  console.error('API migration failed: check DATABASE_URL, connectivity, privileges and migration state');
  process.exitCode = 1;
} finally {
  if (db) await db.destroy();
}
