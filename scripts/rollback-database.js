import knex from 'knex';
import config from '../apps/api/database/knexfile.js';
import { assertLocal, assertReset } from '../apps/api/database/seeds/workflow.js';
let db;
try {
  assertLocal(config); assertReset();
  db = knex(config);
  await db.migrate.rollback();
  console.log('Disposable local migration batch rolled back.');
} catch { console.error('Rollback refused or failed. Requires development, dedicated loopback auditlens database and AUDITLENS_ALLOW_LOCAL_RESET=YES.'); process.exitCode = 1; }
finally { if (db) await db.destroy(); }
