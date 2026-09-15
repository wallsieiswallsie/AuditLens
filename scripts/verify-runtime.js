// Local production-command smoke test; API mode is called only by disposable acceptance.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:net';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

export async function verifyRuntime(service, environment = {}) {
  assert.ok(['api', 'web'].includes(service));
  assert.ok(process.env.npm_execpath, 'Run through npm to use its current local CLI');
  const root = fileURLToPath(new URL('../', import.meta.url));
  for (const workspace of [false, true]) {
    const socket = createServer();
    socket.listen(0, '127.0.0.1');
    await once(socket, 'listening');
    const port = socket.address().port;
    await new Promise(resolve => socket.close(resolve));
    const child = spawn(process.execPath, [process.env.npm_execpath, 'run', workspace ? 'start' : `start:${service}`], {
      cwd: workspace ? resolve(root, 'apps', service) : root,
      env: { ...process.env, ...environment, NODE_ENV: 'production', API_HOST: '127.0.0.1', PORT: String(port) },
      windowsHide: true, detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'],
    });
    let output = '';
    child.stdout.on('data', chunk => { output += chunk; });
    child.stderr.on('data', chunk => { output += chunk; });
    const exited = once(child, 'exit');
    try {
      let response;
      for (let i = 0; i < 120 && child.exitCode === null; i++) {
        try {
          response = await fetch(`http://127.0.0.1:${port}/${service === 'api' ? 'health' : 'index.html'}`, { signal: AbortSignal.timeout(1000) });
          if (response.ok) break;
        } catch { /* Listener may not be ready yet. */ }
        await new Promise(resolve => setTimeout(resolve, 250));
      }
      assert.equal(response?.status, 200, 'Production command did not become healthy (output suppressed)');
      if (service === 'api') {
        assert.equal((await response.json()).service, 'auditlens-api');
        assert.match(output, /API migrations ready: 0 applied/);
      } else {
        assert.match(await response.text(), /id="root"/);
      }
      if (environment.DATABASE_URL) {
        assert.ok(!output.includes(environment.DATABASE_URL));
        const password = decodeURIComponent(new URL(environment.DATABASE_URL).password);
        if (password) assert.ok(!output.includes(password));
      }
    } finally {
      // Stop only this owned npm process tree, including its service child.
      if (child.exitCode === null && child.signalCode === null) {
        if (process.platform === 'win32') {
          const stopped = spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore', timeout: 10000 });
          assert.equal(stopped.status, 0, `Owned runtime process cleanup failed: PID ${child.pid}; use permitted process permissions`);
        }
        else { try { process.kill(-child.pid, 'SIGTERM'); } catch {} }
      }
      await exited;
    }
  }
  return `PASS: ${service} npm start from repository and service roots; live HTTP; owned processes stopped`;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  // Standalone mode deliberately verifies only the database-free Web service.
  try { console.log(await verifyRuntime('web')); }
  catch { console.error('Web runtime verification failed: build dist first and run through npm'); process.exitCode = 1; }
}
