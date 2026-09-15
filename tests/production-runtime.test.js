import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readConfig } from '../apps/api/src/config/env.js';

test('production requires DATABASE_URL; development health keeps its default', () => {
  assert.throws(() => readConfig({ NODE_ENV: 'production' }), /DATABASE_URL/);
  assert.equal(readConfig({}).api.port, 3001);
});

test('production migration and server startup never print raw configuration errors', () => {
  for (const script of ['apps/api/src/migrate.js', 'apps/api/src/index.js']) {
    for (const DATABASE_URL of ['', 'postgresql://secret-sentinel@',
      'postgresql://test:secret-sentinel@127.0.0.1:1/auditlens']) {
      const result = spawnSync(process.execPath, [script], { encoding: 'utf8', timeout: 15000,
        env: { ...process.env, NODE_ENV: 'production', DATABASE_URL, PORT: 'secret-sentinel' } });
      assert.equal(result.status, 1);
      assert.ok(!`${result.stdout}${result.stderr}`.includes('secret-sentinel'));
      assert.match(result.stderr, /failed: check/);
    }
  }
});
