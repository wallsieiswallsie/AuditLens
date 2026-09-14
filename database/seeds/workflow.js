import assert from 'node:assert/strict';
import { TABLES } from '../generators/core.js';
export function assertLocal(config,env=process.env) {
  assert.equal(env.NODE_ENV||'development','development','Dataset writes are development-only');
  assert.ok(['127.0.0.1','localhost','::1'].includes(config.connection.host),'Dataset writes require loopback PostgreSQL');
  assert.equal(config.connection.database,'auditlens','Dataset writes require the dedicated auditlens development database');
  assert.ok(config.connection.password,'DATABASE_PASSWORD is required');
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
