import { createHash } from 'node:crypto';
export const VERSION = '1.0.0';
export const AS_OF = '2026-09-14T10:00:00.000Z';
export const MASTER_TIME = '2026-01-05T02:00:00.000Z';
export const COUNTS = { 'AC-001': 8, 'AC-002': 12, 'AC-003': 6, 'SOD-001': 10, 'SOD-002': 8, 'TX-001': 10, 'TX-002': 12, 'TX-003': 8, 'TX-004': 10, 'TX-005': 8, 'TX-006': 20, 'LOG-001': 10, 'LOG-002': 8, 'LOG-003': 12 };
export const TABLES = ['employees','users','roles','permissions','user_roles','role_permissions','vendors','invoices','invoice_approvals','payments','audit_logs'];
export function context(seed = 20260914) {
  if (!Number.isSafeInteger(seed) || seed < 0 || seed > 4294967295) throw new Error('Seed must be an unsigned 32-bit integer');
  let state = seed;
  return {
    seed,
    random: () => { state = (Math.imul(state, 1664525) + 1013904223) >>> 0; return state / 4294967296; },
    id: (kind, index) => { const h = createHash('sha256').update(`${VERSION}:${seed}:${kind}:${index}`).digest('hex'); return `${h.slice(0,8)}-${h.slice(8,12)}-4${h.slice(13,16)}-a${h.slice(17,20)}-${h.slice(20,32)}`; },
  };
}
export const money = cents => (cents / 100).toFixed(2);
export const cents = value => { if (!/^\d+\.\d{2}$/.test(value)) throw new Error('Invalid decimal'); return BigInt(value.replace('.', '')); };
export const at = (time, minutes) => new Date(Date.parse(time) + minutes * 60000).toISOString();
export const base = (c, kind, i, time = MASTER_TIME) => ({ id: c.id(kind, i), created_at: time, updated_at: time });
export function canonical(value) {
  if (value instanceof Date) return value.toISOString();
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  return value;
}
export const digest = value => createHash('sha256').update(JSON.stringify(canonical(value))).digest('hex');
export function ordered(rows) { return rows.map(canonical).sort((a,b) => JSON.stringify(a).localeCompare(JSON.stringify(b), 'en')); }
