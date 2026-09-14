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
  for (const value of ['0', '-1', '65536', 'abc', '3001.5', '3001oops']) {
    assert.throws(() => readConfig({ PORT: value }), /Invalid PORT/);
  }
  for (const value of ['3001', '8080']) assert.equal(readConfig({ PORT: value }).api.port, Number(value));
  assert.equal(readConfig({}).api.port, 3001);
});

test('live health, absent CORS, payload cap and graceful server stop', async () => {
  const server = await createServer({ api: { host: '127.0.0.1', port: 0 } });
  server.route({ method: 'POST', path: '/test-payload', handler: () => ({ ok: true }) });
  await server.start();
  try {
    const response = await fetch(server.info.uri + '/health', { headers: { Origin: 'https://foreign.example.test' } });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('access-control-allow-origin'), null);
    assert.equal((await server.inject({ method: 'POST', url: '/test-payload', payload: 'x'.repeat(1048577), headers: { 'content-type': 'text/plain' } })).statusCode, 413);
  } finally { await server.stop({ timeout: 1000 }); }
  assert.equal(server.info.started, 0);
});
