import { base, MASTER_TIME, AS_OF } from './core.js';
export const ROLE_PERMISSIONS = {
  administrator: ['user.read','user.manage','role.read','role.manage','audit_log.read'],
  invoice_creator: ['invoice.create','invoice.read','invoice.update','invoice.submit'],
  invoice_approver: ['invoice.read','invoice.approve','invoice.reject'],
  payment_creator: ['payment.create','payment.read','payment.update'],
  payment_confirmer: ['payment.read','payment.confirm'],
  operations_staff: ['invoice.read','vendor.read'],
  operations_manager: ['invoice.read','vendor.read','vendor.manage'],
  auditor_viewer: ['invoice.read','payment.read','user.read','role.read','audit_log.read'],
};
export function referenceData(c) {
  const roles = Object.keys(ROLE_PERMISSIONS).map((code,i) => ({ ...base(c,'role',i), code, name: code.replaceAll('_',' ') }));
  const permissions = [...new Set(Object.values(ROLE_PERMISSIONS).flat())].sort().map((code,i) => ({ ...base(c,'permission',i), code, is_privileged: ['user.manage','role.manage'].includes(code) }));
  const employees = Array.from({length:250}, (_,i) => ({ ...base(c,'employee',i), employee_number:`EMP-${String(i+1).padStart(4,'0')}`, full_name:`Fictional Employee ${i+1}`, department: i < 200 ? 'Finance' : 'Operations', status: i >= 220 ? 'inactive':'active', hired_at:MASTER_TIME, ended_at:i >= 220 ? '2026-07-01T02:00:00.000Z':null, updated_at:i >= 220 ? '2026-07-01T02:00:00.000Z':MASTER_TIME }));
  const users = employees.map((e,i) => ({ ...base(c,'user',i), employee_id:e.id, email:`employee${i+1}@example.test`, account_type:'human', status:i >= 220 ? 'disabled':'active', last_login_at:i>=220?'2026-06-30T03:00:00.000Z':'2026-09-11T03:00:00.000Z', updated_at:i>=220?'2026-07-01T02:00:00.000Z':'2026-09-11T03:00:00.000Z' }));
  const roleIndex = i => i < 50 ? 1 : i < 100 ? 2 : i < 150 ? 3 : i < 200 ? 4 : i < 202 ? 0 : i < 205 ? 6 : i < 210 ? 7 : 5;
  const user_roles = users.map((u,i) => ({user_id:u.id, role_id:roles[roleIndex(i)].id, created_at:MASTER_TIME}));
  const policy = { version:'fixture-policy-1', asOf:AS_OF, timezone:'Asia/Jakarta', businessHours:'Monday-Friday 09:00 inclusive to 17:00 exclusive; no holidays in fixture calendar', dormancyDays:90, allowedRoles:Object.fromEntries(users.map((u,i) => [u.id,[roles[roleIndex(i)].code]])) };
  const role_permissions = roles.flatMap(r => ROLE_PERMISSIONS[r.code].map(code => ({ role_id:r.id, permission_id:permissions.find(p => p.code === code).id, created_at:MASTER_TIME })));
  const vendors = Array.from({length:100},(_,i) => ({ ...base(c,'vendor',i), code:`VEN-${i+1}`, name:`Fictional Supplier ${i+1}` }));
  return { tables:{employees,users,roles,permissions,user_roles,role_permissions,vendors,invoices:[],invoice_approvals:[],payments:[],audit_logs:[]}, policy };
}
