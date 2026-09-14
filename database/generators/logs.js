import { at, cents, money } from './core.js';
export function activityLogs(c,t,state) {
  const add=(action,type,row,actor,time,before=null,after=null)=>{
    const event={id:c.id('log',t.audit_logs.length),actor_id:actor,action,entity_type:type,entity_id:row.id,before_data:before,after_data:after,occurred_at:time,created_at:time}; t.audit_logs.push(event); return event;
  };
  const inactive=[],late=[],changes=[],overrides=[],privileges=[];
  for(const [index,u] of t.users.entries()) {
    const current=t.user_roles.find(r=>r.user_id===u.id);
    const originalRole=index>=210&&index<216?t.roles[5].id:current.role_id;
    add('user.role_assigned','user',u,t.users[200].id,current.created_at,null,{role_id:originalRole,change_reference:`sample://access/${index+1}`});
  }
  for(let n=210;n<216;n++) {
    const u=t.users[n];
    privileges.push(add('user.role_removed','user',u,t.users[200].id,'2026-09-10T02:00:00.000Z',{role_id:t.roles[5].id},{change_reference:null}));
    privileges.push(add('user.role_assigned','user',u,t.users[200].id,'2026-09-10T02:01:00.000Z',null,{role_id:t.roles[0].id,change_reference:null}));
    t.user_roles.find(r=>r.user_id===u.id).created_at='2026-09-10T02:01:00.000Z';
  }
  t.invoices.forEach((i,index)=>{
    const normalTime=index>=180&&index<200?at(i.created_at,180):i.created_at;
    const originalAmount=state.modified.includes(i)?money(Number(cents(i.amount))-10000):i.amount;
    const ev=add('invoice.created','invoice',i,i.created_by,i.created_at,null,{reference:i.reference,vendor_id:i.vendor_id,amount:originalAmount,currency:i.currency,status:'draft'});
    if(index>=60&&index<68) inactive.push(ev);
    if(index>=180&&index<200) late.push(ev);
    if(i.status==='draft') return;
    add('invoice.submitted','invoice',i,t.users[index%50].id,at(normalTime,30),{status:'draft'},{status:'submitted'});
    const approval=t.invoice_approvals.find(a=>a.invoice_id===i.id);
    if(approval) add(approval.decision==='approved'?'invoice.approved':'invoice.rejected','invoice',i,approval.decided_by,approval.decided_at,{status:'submitted'},{status:approval.decision,approval_id:approval.id});
    if(i.status==='void') add('invoice.voided','invoice',i,t.users[index%50].id,i.updated_at,{status:'rejected'},{status:'void'});
    if(i.status==='paid') add('invoice.paid','invoice',i,t.users[150+index%50].id,at(normalTime,index<800?210:150),{status:approval?'approved':'submitted'},{status:'paid'});
    if(state.modified.includes(i)) changes.push(add('invoice.updated','invoice',i,t.users[index%50].id,i.updated_at,{amount:originalAmount},{amount:i.amount,change_reference:null}));
  });
  t.payments.forEach((p,index)=>{
    add('payment.created','payment',p,p.created_by,p.created_at,null,{reference:p.reference,amount:p.amount,currency:p.currency,status:'pending'});
    if(index>=1800&&index<1808) overrides.push(add('payment.status_overridden','payment',p,t.users[200].id,p.confirmed_at,{status:'pending'},{status:'confirmed',confirmed_by:p.confirmed_by,change_reference:null}));
    else add('payment.confirmed','payment',p,p.confirmed_by,p.confirmed_at,{status:'pending'},{status:'confirmed'});
  });
  state.mark('TX-005','audit_logs',inactive,'creation event after employee ended_at');
  state.mark('TX-006','audit_logs',late,'out-of-hours creation event');
  state.mark('LOG-001','audit_logs',changes,'material change event');
  state.mark('LOG-002','audit_logs',overrides,'override event');
  state.mark('LOG-003','audit_logs',privileges,'unapproved role change event');
}
