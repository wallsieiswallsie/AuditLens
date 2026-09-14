import knex from 'knex';
import config from '../apps/api/database/knexfile.js';
import { inspectDatabase } from '../apps/api/database/inspect.js';
const db = knex(config);
try { console.log(JSON.stringify(await inspectDatabase(db), null, 2)); }
catch { console.error('Database inspection failed. Check configuration, connectivity and catalog/metadata read permissions.'); process.exitCode = 1; }
finally { await db.destroy(); }
