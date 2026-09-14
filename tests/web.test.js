import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { staticServer } from '../apps/web/server.js';
import viteConfig from '../apps/web/vite.config.js';

test('static production server serves SPA navigation, HEAD and assets, but rejects missing assets and unsafe paths', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'auditlens-web-'));
  await writeFile(join(dir, 'index.html'), '<html>AuditLens test shell</html>');
  await writeFile(join(dir, 'app.js'), 'globalThis.test=true;');
  await writeFile(join(dir, '.secret'), 'SECRET');
  const server = await staticServer(dir);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    assert.equal((await fetch(base + '/')).status, 200);
    for (const route of ['/', '/audit-tests', '/findings', '/nested/route']) {
      const response = await fetch(base + route, { headers: { Accept: 'text/html' } });
      assert.equal(response.status, 200); assert.match(await response.text(), /AuditLens test shell/);
      assert.equal(response.headers.get('cache-control'), 'no-cache');
    }
    assert.match((await fetch(base + '/app.js')).headers.get('content-type'), /javascript/);
    assert.equal(await (await fetch(base + '/', { method: 'HEAD', headers: { Accept: 'text/html' } })).text(), '');
    for (const route of ['/missing.js', '/.secret', '/%2e%2e%2fpackage.json', '/%5csecret']) assert.equal((await fetch(base + route)).status, 404);
    assert.equal((await fetch(base + '/%zz')).status, 400);
    assert.equal((await fetch(base + '/', { method: 'POST' })).status, 405);
  } finally { await new Promise(resolve => server.close(resolve)); await rm(dir, { recursive: true }); }
});

test('WEB_ALLOWED_HOST is optional and rejects URL-shaped values', () => {
  const previous = { API_URL: process.env.API_URL, WEB_ALLOWED_HOST: process.env.WEB_ALLOWED_HOST };
  process.env.API_URL = 'https://api.example.test';
  try {
    process.env.WEB_ALLOWED_HOST = '';
    assert.deepEqual(viteConfig({ mode: 'test' }).preview.allowedHosts, []);
    process.env.WEB_ALLOWED_HOST = 'preview.example.test';
    assert.deepEqual(viteConfig({ mode: 'test' }).preview.allowedHosts, ['preview.example.test']);
    process.env.WEB_ALLOWED_HOST = 'https://secret@example.test:4173';
    assert.throws(() => viteConfig({ mode: 'test' }), /Invalid WEB_ALLOWED_HOST/);
  } finally { for (const [key, value] of Object.entries(previous)) { if (value === undefined) delete process.env[key]; else process.env[key] = value; } }
});
