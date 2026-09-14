import { AS_OF, VERSION, COUNTS, at, cents, money } from './core.js';
export function inject(c,t) {
  const truth={ datasetVersion:VERSION, seed:c.seed, generatedAt:AS_OF, policyVersion:'fixture-policy-1', anomalies:{} };
  const mark=(code,table,records,unit='record',groups=[]) => { truth.anomalies[code]={ expectedCount:COUNTS[code], unit, table:`business.${table}`, recordIds:records.map(r=>r.id), ...(groups.length?{groups}: {}) }; };
  const selected=(start,count)=>t.invoices.slice(start,start+count);
  t.users.slice(220,228).forEach(u=>{u.status='active';u.last_login_at='2026-09-11T03:00:00.000Z';u.updated_at=u.last_login_at;});
  mark('AC-001','users',t.users.slice(220,228),'account');
  // Dormant fixtures have no transaction activity, including the never-used account.
  const dormant=[...t.users.slice(201,210),...t.users.slice(216,219)];
  dormant.forEach((u,i)=>{u.last_login_at=i===0?null:'2026-06-01T03:00:00.000Z';});
  // Exactly-at-threshold and recently created never-used clean controls.
  t.users[32].last_login_at='2026-06-16T10:00:00.000Z';
  Object.assign(t.users[219], {created_at:'2026-09-01T02:00:00.000Z',updated_at:'2026-09-01T02:00:00.000Z',last_login_at:null});
  t.user_roles.find(r=>r.user_id===t.users[219].id).created_at=t.users[219].created_at;
  mark('AC-002','users',dormant,'account');
  t.users.slice(210,216).forEach(u=>{t.user_roles.find(r=>r.user_id===u.id).role_id=t.roles[0].id;});
  mark('AC-003','users',t.users.slice(210,216),'account');
  const self=selected(0,10); self.forEach(i=>{t.invoice_approvals.find(a=>a.invoice_id===i.id).decided_by=i.created_by;});
  mark('SOD-001','invoices',self,'observed self-approval invoice');
  const selfPay=t.payments.slice(40,48); selfPay.forEach(p=>{p.confirmed_by=p.created_by;});
  mark('SOD-002','payments',selfPay,'observed self-confirmation payment');
  const invoiceGroups=[];
  for(let i=100;i<120;i+=2) { const a=t.invoices[i],b=t.invoices[i+1]; Object.assign(b,{vendor_id:a.vendor_id,reference:` ${a.reference.toLowerCase()} `,amount:a.amount}); t.payments.filter(p=>p.invoice_id===b.id).forEach(p=>{p.amount=money(Number(cents(b.amount))/2);}); invoiceGroups.push([a.id,b.id]); }
  mark('TX-001','invoices',selected(100,20),'duplicate group',invoiceGroups);
  const paymentGroups=[];
  for(let i=140;i<152;i++) { const pair=t.payments.filter(p=>p.invoice_id===t.invoices[i].id); pair[1].reference=` ${pair[0].reference.toLowerCase()} `; paymentGroups.push(pair.map(p=>p.id)); }
  mark('TX-002','payments',t.payments.filter(p=>paymentGroups.flat().includes(p.id)),'duplicate group',paymentGroups);
  const over=selected(820,8); over.forEach(i=>{t.payments.find(p=>p.invoice_id===i.id).amount=money(Number(cents(i.amount))+100);});
  mark('TX-003','invoices',over,'invoice with cumulative overpayment');
  const missing=selected(160,10); t.invoice_approvals=t.invoice_approvals.filter(a=>!missing.some(i=>i.id===a.invoice_id));
  mark('TX-004','invoices',missing,'invoice');
  selected(60,8).forEach((i,n)=>{i.created_by=t.users[228+n].id;});
  // Event IDs for TX-005/006 and LOG categories are filled by log generation.
  selected(180,20).forEach(i=>{i.created_at=at(i.created_at,-180);});
  const modified=selected(850,10); modified.forEach(i=>{i.amount=money(Number(cents(i.amount))+10000); i.updated_at=at(i.created_at,240);});
  return {truth,mark,modified,missing};
}
