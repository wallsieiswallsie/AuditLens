import { readdir, readFile, access } from 'node:fs/promises';
import path from 'node:path';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { default: mermaid } = await import('mermaid');
mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const lists = await Promise.all(entries.filter(e => !['node_modules', '.git', '.venv', 'dist', '__pycache__'].includes(e.name)).map(e => e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]));
  return lists.flat();
}
let diagrams = 0;
let links = 0;
const files = (await walk('.')).filter(f => f.endsWith('.md'));
for (const file of files) {
  const source = await readFile(file, 'utf8');
  for (const match of source.matchAll(/\x60\x60\x60mermaid\r?\n([\s\S]*?)\x60\x60\x60/g)) {
    try { await mermaid.parse(match[1]); diagrams++; }
    catch (error) { throw new Error(`${file}: invalid Mermaid: ${error.message}`); }
  }
  for (const match of source.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
    const target = match[1].split('#')[0];
    if (!target || /^[a-z]+:/i.test(target)) continue;
    await access(path.resolve(path.dirname(file), decodeURIComponent(target)));
    links++;
  }
}
console.log(`Validated ${files.length} Markdown files, ${links} relative links and ${diagrams} Mermaid diagrams.`);

