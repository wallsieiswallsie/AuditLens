import { fileURLToPath } from 'node:url';
import { requireDatabaseUrl } from '../src/config/env.js';

export default {
  client: 'pg',
  connection: requireDatabaseUrl(),
  pool: { min: 0, max: 5 },
  acquireConnectionTimeout: 5000,
  migrations: {
    directory: fileURLToPath(new URL('./migrations', import.meta.url)),
    tableName: 'knex_migrations',
    schemaName: 'public',
  },
};
