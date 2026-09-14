import assert from 'node:assert/strict';
import { AS_OF, COUNTS, cents, digest, ordered } from '../generators/core.js';
export const FOREIGN_KEYS={ users:{employee_id:'employees'}, user_roles:{user_id:'users',role_id:'roles'}, role_permissions:{role_id:'roles',permission_id:'permissions'}, invoices:{vendor_id:'vendors',created_by:'users'}, invoice_approvals:{invoice_id:'invoices',decided_by:'users'}, payments:{invoice_id:'invoices',created_by:'users',confirmed_by:'users'}, audit_logs:{actor_id:'users'} };
const setEqual=(a,b,label)=>assert.deepEqual([...a].sort(),[...b].sort(),label);
const groups=(rows,key)=>{const m=new Map(); for(const r of rows){const k=key(r);m.set(k,[...(m.get(k)||[]),r.id]);}return [...m.values()].filter(g=>g.length>1);};
const norm=s=>s.trim().toUpperCase();
// Fixture-only assertions. Not exported to the API or Python analysis runtime.
export function validate(dataset,{verifyHashes=true}={}) {
  const {tables:t,groundTruth:g,manifest:m,policy}=dataset;
  const maps=Object.fromEntries(Object.entries(t).map(([name,rows])=>[name,new Map(rows.map(r=>[r.id,r]))]));
  for(const [name,rows] of Object.entries(t)) {
    assert.equal(rows.length,m.counts[name],`${name} count`);
    const keys=rows.map(r=>r.id||`${r.user_id||r.role_id}:${r.role_id&&r.user_id?r.role_id:r.permission_id}`);
    assert.equal(new Set(keys).size,keys.length,`${name} primary keys`);
    if(verifyHashes) assert.equal(digest(ordered(rows)),m.tableHashes[name],`${name} differs from deterministic fixture`);
    for(const r of rows) {
      assert.ok(Date.parse(r.created_at)<=Date.parse(AS_OF),`${name} future creation`);
      if(r.updated_at) assert.ok(r.updated_at>=r.created_at,`${name} update chronology`);
      for(const [col,parent] of Object.entries(FOREIGN_KEYS[name]||{})) if(r[col]!=null) assert.ok(maps[parent].has(r[col]),`${name}.${col} orphan`);
    }
  }
  for(const [name,col] of [['employees','employee_number'],['users','email'],['roles','code'],['permissions','code'],['vendors','code']]) assert.equal(new Set(t[name].map(r=>r[col])).size,t[name].length,`${name} unique ${col}`);
  for(const u of t.users) {assert.ok(['active','disabled'].includes(u.status));assert.ok(u.account_type!=='human'||maps.employees.has(u.employee_id));assert.ok(u.email===u.email.trim().toLowerCase());}
  for(const e of t.employees) assert.ok(e.status==='active'?e.ended_at===null:e.ended_at>=e.hired_at);
  for(const i of t.invoices) {assert.ok(cents(i.amount)>0n);assert.equal(i.currency,'IDR');assert.ok(i.supporting_reference.startsWith('sample://invoice/'));assert.ok(maps.users.get(i.created_by).created_at<=i.created_at);}
  for(const a of t.invoice_approvals) assert.ok(a.decided_at>=maps.invoices.get(a.invoice_id).created_at);
  for(const p of t.payments) {assert.ok(cents(p.amount)>0n);assert.equal(p.currency,maps.invoices.get(p.invoice_id).currency);assert.ok(p.confirmed_by&&p.confirmed_at>=p.created_at);assert.ok(p.created_at>=maps.invoices.get(p.invoice_id).created_at);}
  for(const l of t.audit_logs) {const parent={user:'users',invoice:'invoices',payment:'payments'}[l.entity_type];assert.ok(maps[parent]?.has(l.entity_id),'log source reference');assert.ok(l.created_at>=l.occurred_at);}
  const exact=(code,ids,actualGroups)=>{
    const fixture=g.anomalies[code]; assert.equal(fixture.expectedCount,COUNTS[code]);
    setEqual(ids,fixture.recordIds,`${code} exact IDs (including clean negative population)`);
    assert.equal(actualGroups?actualGroups.length:ids.length,COUNTS[code],`${code} count`);
    if(actualGroups) setEqual(actualGroups.map(x=>x.sort().join(':')),fixture.groups.map(x=>[...x].sort().join(':')),`${code} members`);
  };
  exact('AC-001',t.users.filter(u=>u.status==='active'&&maps.employees.get(u.employee_id).status==='inactive').map(u=>u.id));
  exact('AC-002',t.users.filter(u=>u.status==='active'&&Date.parse(u.last_login_at||u.created_at)<Date.parse(AS_OF)-90*86400000).map(u=>u.id));
  exact('AC-003',t.users.filter(u=>t.user_roles.some(r=>r.user_id===u.id&&!policy.allowedRoles[u.id].includes(maps.roles.get(r.role_id).code))).map(u=>u.id));
  exact('SOD-001',t.invoices.filter(i=>t.invoice_approvals.some(a=>a.invoice_id===i.id&&a.decision==='approved'&&a.decided_by===i.created_by)).map(i=>i.id));
  exact('SOD-002',t.payments.filter(p=>p.created_by===p.confirmed_by).map(p=>p.id));
  const ig=groups(t.invoices.filter(i=>i.status!=='void'),i=>[i.vendor_id,norm(i.reference),i.currency,i.amount].join(':'));
  exact('TX-001',ig.flat(),ig);
  const pg=groups(t.payments.filter(p=>p.status==='confirmed'),p=>[p.invoice_id,norm(p.reference),p.currency,p.amount].join(':'));
  exact('TX-002',pg.flat(),pg);
  const totals=new Map(); for(const p of t.payments) if(p.status==='confirmed') totals.set(p.invoice_id,(totals.get(p.invoice_id)||0n)+cents(p.amount));
  exact('TX-003',t.invoices.filter(i=>(totals.get(i.id)||0n)>cents(i.amount)).map(i=>i.id));
  exact('TX-004',t.invoices.filter(i=>['paid','approved'].includes(i.status)&&!t.invoice_approvals.some(a=>a.invoice_id===i.id&&a.decision==='approved'&&t.payments.filter(p=>p.invoice_id===i.id).every(p=>a.decided_at<=p.created_at))).map(i=>i.id));
  const events=t.audit_logs.filter(l=>['invoice.created','payment.created'].includes(l.action));
  exact('TX-005',events.filter(l=>{const e=maps.employees.get(maps.users.get(l.actor_id).employee_id);return e.ended_at&&l.occurred_at>=e.ended_at;}).map(l=>l.id));
  exact('TX-006',events.filter(l=>{const local=new Date(Date.parse(l.occurred_at)+7*3600000);return [0,6].includes(local.getUTCDay())||local.getUTCHours()<9||local.getUTCHours()>=17;}).map(l=>l.id));
  exact('LOG-001',t.audit_logs.filter(l=>l.action==='invoice.updated'&&['amount','currency','vendor_id'].some(k=>l.before_data?.[k]!==l.after_data?.[k])&&t.invoice_approvals.some(a=>a.invoice_id===l.entity_id&&a.decision==='approved'&&a.decided_at<l.occurred_at)).map(l=>l.id));
  exact('LOG-002',t.audit_logs.filter(l=>l.action==='payment.status_overridden').map(l=>l.id));
  exact('LOG-003',t.audit_logs.filter(l=>['user.role_assigned','user.role_removed'].includes(l.action)&&!l.after_data?.change_reference).map(l=>l.id));
  assert.deepEqual(Object.keys(g.anomalies).sort(),Object.keys(COUNTS).sort());
  return {counts:m.counts,anomalies:COUNTS,orphans:0,logicalSha256:m.logicalSha256};
}
