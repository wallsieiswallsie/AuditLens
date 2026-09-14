import { createServer } from 'node:http';
import { readFile, realpath, stat } from 'node:fs/promises';
import { resolve, relative, extname, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';

const dist = fileURLToPath(new URL('./dist/', import.meta.url));
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.json': 'application/json' };
const contained = (root, file) => { const rel = relative(root, file); return !rel.startsWith('..') && !isAbsolute(rel); };

export async function staticServer(directory = dist) {
  const root = await realpath(directory);
  const index = await readFile(resolve(root, 'index.html'));
  return createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    if (!['GET', 'HEAD'].includes(req.method)) {
      res.writeHead(405, { Allow: 'GET, HEAD' }); res.end(); return;
    }
    try {
      const path = decodeURIComponent(req.url.split('?')[0]);
      if (path.includes('\0') || path.includes('\\') || path.split('/').some(part => part.startsWith('.'))) {
        res.writeHead(404); res.end(); return;
      }
      const candidate = resolve(root, '.' + path);
      if (!contained(root, candidate)) { res.writeHead(404); res.end(); return; }
      let file;
      try {
        file = await realpath(candidate);
        if (!contained(root, file) || !(await stat(file)).isFile()) file = undefined;
      } catch (error) { if (!['ENOENT', 'ENOTDIR'].includes(error.code)) throw error; }
      // Only browser navigation gets SPA fallback; missing assets stay 404.
      const fallback = !file && (path === '/' || (!extname(path) && (req.headers.accept || '').includes('text/html')));
      if (!file && !fallback) { res.writeHead(404); res.end(); return; }
      const body = file ? await readFile(file) : index;
      const type = file ? mime[extname(file)] || 'application/octet-stream' : mime['.html'];
      res.writeHead(200, { 'Content-Type': type, 'Content-Length': body.length, 'Cache-Control': type.startsWith('text/html') ? 'no-cache' : 'public, max-age=3600' });
      res.end(req.method === 'HEAD' ? undefined : body);
    } catch (error) { res.writeHead(error instanceof URIError ? 400 : 500); res.end(); }
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const port = process.env.PORT || '4173';
    if (!/^\d+$/.test(port) || Number(port) < 1 || Number(port) > 65535) throw new Error('Invalid PORT');
    const server = await staticServer();
    server.listen(Number(port), '0.0.0.0', () => console.log(`AuditLens Web listening on port ${port}`));
    server.on('error', () => { console.error('Web listener failed'); process.exitCode = 1; });
    for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => {
      server.close(() => process.exit(0));
      setTimeout(() => process.exit(1), 5000).unref();
    });
  } catch { console.error('Web startup failed: build dist first and supply a valid PORT'); process.exitCode = 1; }
}
