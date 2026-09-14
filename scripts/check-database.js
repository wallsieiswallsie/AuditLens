import knex from 'knex';
import config from '../database/knexfile.js';

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
