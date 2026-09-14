import knex from 'knex';
import config from '../database/knexfile.js';

if (!config.connection.password) {
  console.error('DATABASE_PASSWORD is required for database verification. Set it in your local .env.');
  process.exit(1);
}
const db = knex(config);
try {
  await db.raw('SELECT 1 AS connected');
  console.log('PostgreSQL connection verified.');
} catch (error) {
  console.error(`PostgreSQL connection failed (${error.code || 'connection error'}). Check .env and database availability.`);
  process.exitCode = 1;
} finally {
  await db.destroy();
}
