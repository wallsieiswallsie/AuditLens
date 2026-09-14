import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { generate } from '../database/generators/index.js';
import { validate } from '../database/validation/validate.js';
import { COUNTS,TABLES } from '../database/generators/core.js';
import { assertLocal } from '../database/seeds/workflow.js';
import { migrationSql } from '../scripts/migration-sql.js';
const fixture=generate();
test('same seed yields identical complete records and metadata; another seed varies records',()=>{
  assert.deepEqual(generate(),fixture);
  const other=generate(42); assert.notEqual(other.manifest.logicalSha256,fixture.manifest.logicalSha256);validate(other);
  for(const seed of [-1,NaN,1.5,4294967296]) assert.throws(()=>generate(seed));
});
test('full fixture QA: counts, all anomaly sets, normal negatives and no orphans',()=>{
  const result=validate(fixture);assert.equal(result.orphans,0);
  assert.deepEqual(result.counts,{employees:250,users:250,roles:8,permissions:17,user_roles:250,role_permissions:27,vendors:100,invoices:2000,invoice_approvals:1840,payments:2400,audit_logs:12512});
  assert.deepEqual(result.anomalies,COUNTS);
});
test('checked-in benchmark files match the default generator',async()=>{
  for(const [file,key] of [['ground-truth','groundTruth'],['dataset-manifest','manifest'],['fixture-policy','policy']]) assert.deepEqual(JSON.parse(await readFile(new URL(`../database/sample-data/${file}.json`,import.meta.url),'utf8')),fixture[key]);
});
test('QA rejects unexpected duplicate, wrong SoD IDs, orphan, and accidental dormant account without relying on hashes',()=>{
  for(const change of [
    d=>{d.tables.invoices[400].vendor_id=d.tables.invoices[401].vendor_id;d.tables.invoices[400].reference=d.tables.invoices[401].reference;d.tables.invoices[400].amount=d.tables.invoices[401].amount;},
    d=>{d.groundTruth.anomalies['SOD-001'].recordIds[0]=d.tables.invoices[30].id;},
    d=>{d.tables.payments[0].invoice_id='00000000-0000-4000-a000-000000000000';},
    d=>{d.tables.users[40].last_login_at='2026-01-06T02:00:00.000Z';},
    d=>{d.tables.payments[1000].confirmed_by=d.tables.payments[1000].created_by;},
  ]) {const d=structuredClone(fixture);change(d);assert.throws(()=>validate(d,{verifyHashes:false}));}
});
test('local write guard refuses production, remote host, wrong database and absent credential',()=>{
  const config={connection:'postgresql://dev:test-only@127.0.0.1:5432/auditlens'};
  assert.doesNotThrow(()=>assertLocal(config,{}));
  assert.throws(()=>assertLocal(config,{NODE_ENV:'production'}));
  for(const connection of ['postgresql://dev:test-only@remote.example.test/auditlens','postgresql://dev:test-only@localhost/production','postgresql://dev@localhost/auditlens','postgresql://dev:test-only@localhost/auditlens?host=remote.example.test']) assert.throws(()=>assertLocal({connection},{}));
});
test('domain migration compiles PostgreSQL DDL with 11 tables, constraints and reverse rollback',async()=>{
  const up=(await migrationSql()).join('\n'), down=await migrationSql('down');
  assert.equal((up.match(/create table/g)||[]).length,11);
  for(const table of TABLES) assert.ok(up.includes(`create table "business"."${table}"`));
  assert.ok(up.includes('numeric')||up.includes('decimal'));assert.ok(up.includes('jsonb'));
  assert.ok(up.includes('foreign key'));assert.ok(up.includes('check'));assert.ok(up.includes('on delete RESTRICT'));
  assert.equal(down.length,11);assert.ok(down[0].includes('audit_logs'));assert.ok(down.at(-1).includes('employees'));
});
