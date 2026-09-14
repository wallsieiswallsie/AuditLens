import { base, at, money } from './core.js';
export function normalTransactions(c, t) {
  for (let i=0;i<2000;i++) {
    // Twenty August weekdays; fixed UTC+7 business calendar, independent of host clock.
    const day = 3 + Math.floor((i%20)/5)*7 + (i%5);
    const time = `2026-08-${String(day).padStart(2,'0')}T02:00:00.000Z`;
    const amount = (10000 + Math.floor(c.random()*90000))*100;
    const invoice = { ...base(c,'invoice',i,time), vendor_id:t.vendors[i%100].id, reference:`INV-${String(i+1).padStart(6,'0')}`, amount:money(amount), currency:'IDR', status:i<1600?'paid':i<1800?'approved':i<1900?'submitted':i<1950?'draft':'void', created_by:t.users[i%50].id, supporting_reference:`sample://invoice/${i+1}` };
    t.invoices.push(invoice);
    if(i<1800) t.invoice_approvals.push({ id:c.id('approval',i), invoice_id:invoice.id, decided_by:t.users[50+i%50].id, decision:'approved', decided_at:at(time,60), created_at:at(time,60) });
    if(i>=1950) t.invoice_approvals.push({ id:c.id('approval',i), invoice_id:invoice.id, decided_by:t.users[50+i%50].id, decision:'rejected', decided_at:at(time,60), created_at:at(time,60) });
    if(i<1600) {
      const parts=i<800?2:1;
      for(let part=0;part<parts;part++) {
        const index=t.payments.length;
        t.payments.push({ ...base(c,'payment',index,at(time,120+part*60)), invoice_id:invoice.id, reference:`PAY-${index+1}`, amount:money(amount/parts), currency:'IDR', status:'confirmed', created_by:t.users[100+i%50].id, confirmed_by:t.users[150+i%50].id, confirmed_at:at(time,150+part*60), updated_at:at(time,150+part*60) });
      }
    }
    invoice.updated_at = at(time, i<1600 ? (i<800?210:150) : i<1800||i>=1950?60:i<1900?30:0);
  }
}
