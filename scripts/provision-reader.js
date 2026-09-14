import knex from 'knex';
import config from '../apps/api/database/knexfile.js';
import { assertLocal } from '../apps/api/database/seeds/workflow.js';
import { provisionReader } from '../apps/api/database/security/source-reader.js';
let db;
try {
  assertLocal(config);
  if (process.env.AUDITLENS_ALLOW_READER_PROVISION !== 'YES') throw new Error();
  db = knex(config); await provisionReader(db);
  console.log('Source reader provisioned. Run disposable acceptance for actual permission evidence.');
} catch { console.error('Reader provisioning refused or failed. Requires explicit AUDITLENS_ALLOW_READER_PROVISION=YES, dedicated local development database and role/schema administration privileges.'); process.exitCode = 1; }
finally { if (db) await db.destroy(); }
