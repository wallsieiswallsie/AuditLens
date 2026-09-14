import assert from 'node:assert/strict';
import { TABLES } from '../generators/core.js';
export function assertLocal(config,env=process.env) {
  assert.equal(env.NODE_ENV||'development','development','Dataset writes are development-only');
  let connection;
  try { connection = new URL(config.connection); } catch { throw new Error('Invalid DATABASE_URL'); }
  // Inspect only for the destructive-write guard; Knex still receives the original URL.
  assert.ok(['postgres:', 'postgresql:'].includes(connection.protocol), 'Expected PostgreSQL URL');
  assert.equal(connection.search, '', 'Dataset writes do not allow connection query overrides');
  assert.equal(connection.hash, '', 'Dataset writes do not allow URL fragments');
  assert.ok(['127.0.0.1','localhost','[::1]'].includes(connection.hostname),'Dataset writes require loopback PostgreSQL');
  assert.equal(decodeURIComponent(connection.pathname.slice(1)),'auditlens','Dataset writes require the dedicated auditlens development database');
  assert.ok(connection.password,'DATABASE_URL must contain a password for dataset writes');
}
export async function seedEmpty(db,dataset) {
  await db.transaction(async trx=>{
    await trx.raw("SELECT pg_advisory_xact_lock(20260914)");
    for(const name of TABLES) assert.equal(Number((await trx.withSchema('business').table(name).count('* as n').first()).n),0,`business.${name} is not empty; use explicit local reset`);
    for(const name of TABLES) for(let i=0;i<dataset.tables[name].length;i+=250) await trx.withSchema('business').table(name).insert(dataset.tables[name].slice(i,i+250));
  });
}
export async function resetData(db,env=process.env) {
  assert.equal(env.AUDITLENS_ALLOW_LOCAL_RESET,'YES','Set AUDITLENS_ALLOW_LOCAL_RESET=YES to delete local business data');
  await db.transaction(async trx=>{
    await trx.raw('SELECT pg_advisory_xact_lock(20260914)');
    // No CASCADE, no schema/database drop, no writes to audit or migration metadata.
    for(const name of [...TABLES].reverse()) await trx.withSchema('business').table(name).delete();
  });
}
