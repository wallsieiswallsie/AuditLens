import { fileURLToPath } from 'node:url';
import { readConfig } from '../apps/api/src/config/env.js';

export default {
  client: 'pg',
  connection: { ...readConfig().database, connectionTimeoutMillis: 5000 },
  pool: { min: 0, max: 5 },
  acquireConnectionTimeout: 5000,
  migrations: {
    directory: fileURLToPath(new URL('./migrations', import.meta.url)),
    tableName: 'knex_migrations',
    schemaName: 'public',
  },
};
