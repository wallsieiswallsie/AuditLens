import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../apps/api/src/server.js';
import { readConfig } from '../apps/api/src/config/env.js';

test('health contract and error boundaries', async () => {
  const server = await createServer();
  server.route({ method: 'GET', path: '/test-failure', handler: () => { throw new Error('sensitive internal detail'); } });
  await server.initialize();
  try {
    const response = await server.inject('/health');
    assert.equal(response.statusCode, 200);
    assert.deepEqual(response.result, { status: 'ok', service: 'auditlens-api' });
    assert.equal((await server.inject('/missing')).statusCode, 404);
    const failure = await server.inject('/test-failure');
    assert.equal(failure.statusCode, 500);
    assert.ok(!failure.payload.includes('sensitive'));
  } finally { await server.stop(); }
});
test('invalid environment ports fail early', () => {
  for (const value of ['0', '-1', '65536', '3001oops']) {
    assert.throws(() => readConfig({ API_PORT: value }), /Invalid API_PORT/);
  }
});

