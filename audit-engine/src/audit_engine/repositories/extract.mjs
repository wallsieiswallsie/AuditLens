// Private transport only. No CLI SQL, table, role or connection arguments.
import pg from 'pg';
import dotenv from 'dotenv';
import { readFileSync } from 'node:fs';
dotenv.config({ path: new URL('../../../../.env', import.meta.url), quiet: true });
const columns = JSON.parse(readFileSync(new URL('./source-schema.json', import.meta.url), 'utf8'));
const connectionString = process.env.AUDIT_SOURCE_DATABASE_URL?.trim() || process.env.DATABASE_URL?.trim();
let client;
try {
  const url = new URL(connectionString);
  if (!['postgres:', 'postgresql:'].includes(url.protocol) || !url.hostname || url.search || url.hash) throw new Error();
  client = new pg.Client({ connectionString, connectionTimeoutMillis: 10000, statement_timeout: 60000 });
  await client.connect();
  await client.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');
  await client.query('SET LOCAL ROLE auditlens_source_reader');
  const identity = (await client.query('SELECT current_user AS role')).rows[0];
  if (identity.role !== 'auditlens_source_reader') throw new Error();
  const tables = {};
  for (const table of Object.keys(columns).sort()) {
    const fields = columns[table].map(column => {
      if (column.endsWith('_at')) return `to_char("${column}" AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS "${column}"`;
      if (['amount', 'before_data', 'after_data'].includes(column)) return `"${column}"::text AS "${column}"`;
      return `"${column}"`;
    });
    const keys = table === 'user_roles' ? 'user_id, role_id' : table === 'role_permissions' ? 'role_id, permission_id' : 'id';
    tables[table] = (await client.query(`SELECT ${fields.join(', ')} FROM business."${table}" ORDER BY ${keys}`)).rows;
  }
  await client.query('ROLLBACK');
  process.stdout.write(JSON.stringify({ source_type: 'postgresql', schema_version: '1', tables }));
} catch {
  // Driver errors may contain URLs, server names, source values or credentials.
  process.stderr.write('Source extraction failed; check local connection and reader provisioning.\n');
  process.exitCode = 1;
} finally {
  if (client) await client.end().catch(() => {});
}
