// Source structure only: control failures remain representable without broken keys.
export async function up(knex) {
  const schema = () => knex.schema.withSchema('business');
  const base = (t, mutable = true) => {
    t.uuid('id').primary();
    t.timestamp('created_at', { useTz: true }).notNullable();
    if (mutable) {
      t.timestamp('updated_at', { useTz: true }).notNullable();
      t.check('updated_at >= created_at');
    }
  };
  const ref = (t, col, table, nullable = false) => {
    const c = t.uuid(col).references('id').inTable(`business.${table}`).onDelete('RESTRICT');
    if (!nullable) c.notNullable();
    t.index(col);
  };
  const txt = (t, col) => { t.text(col).notNullable(); t.check('length(trim(??)) > 0', [col]); };
  await schema().createTable('employees', t => {
    base(t); txt(t, 'employee_number'); t.unique('employee_number');
    txt(t, 'full_name'); txt(t, 'department');
    t.text('status').notNullable(); t.check("status IN ('active','inactive')");
    t.timestamp('hired_at', { useTz: true }).notNullable();
    t.timestamp('ended_at', { useTz: true });
    t.check("(status = 'active' AND ended_at IS NULL) OR (status = 'inactive' AND ended_at >= hired_at)");
    t.check("status <> 'inactive' OR ended_at IS NOT NULL");
  });
  await schema().createTable('users', t => {
    base(t); ref(t, 'employee_id', 'employees', true); txt(t, 'email'); t.unique('email');
    t.check('email = lower(trim(email))');
    t.text('account_type').notNullable(); t.check("account_type IN ('human','service')");
    t.check("account_type <> 'human' OR employee_id IS NOT NULL");
    t.text('status').notNullable(); t.check("status IN ('active','disabled')");
    t.timestamp('last_login_at', { useTz: true });
    t.check('last_login_at IS NULL OR last_login_at >= created_at');
    t.index(['status', 'last_login_at']);
  });
  await schema().createTable('roles', t => { base(t); txt(t, 'code'); t.unique('code'); txt(t, 'name'); });
  await schema().createTable('permissions', t => { base(t); txt(t, 'code'); t.unique('code'); t.boolean('is_privileged').notNullable(); });
  for (const [table, a, b] of [['user_roles', 'user', 'role'], ['role_permissions', 'role', 'permission']]) {
    await schema().createTable(table, t => {
      ref(t, `${a}_id`, `${a}s`); ref(t, `${b}_id`, `${b}s`);
      t.primary([`${a}_id`, `${b}_id`]); t.timestamp('created_at', { useTz: true }).notNullable();
    });
  }
  await schema().createTable('vendors', t => { base(t); txt(t, 'code'); t.unique('code'); txt(t, 'name'); });
  const money = t => { t.decimal('amount', 18, 2).notNullable(); t.check('amount > 0'); t.specificType('currency', 'char(3)').notNullable(); t.check("currency IN ('IDR')"); };
  await schema().createTable('invoices', t => {
    base(t); ref(t, 'vendor_id', 'vendors'); txt(t, 'reference'); money(t);
    t.text('status').notNullable(); t.check("status IN ('draft','submitted','approved','paid','void')");
    ref(t, 'created_by', 'users'); t.text('supporting_reference');
    t.index(['vendor_id', 'reference', 'currency', 'amount']); t.index(['status', 'created_at']);
  });
  await schema().createTable('invoice_approvals', t => {
    base(t, false); ref(t, 'invoice_id', 'invoices'); ref(t, 'decided_by', 'users');
    t.text('decision').notNullable(); t.check("decision IN ('approved','rejected')");
    t.timestamp('decided_at', { useTz: true }).notNullable(); t.check('created_at >= decided_at');
    t.index(['invoice_id', 'decided_at']);
  });
  await schema().createTable('payments', t => {
    base(t); ref(t, 'invoice_id', 'invoices'); txt(t, 'reference'); money(t);
    t.text('status').notNullable(); t.check("status IN ('pending','confirmed','void')");
    ref(t, 'created_by', 'users'); ref(t, 'confirmed_by', 'users', true);
    t.timestamp('confirmed_at', { useTz: true });
    t.check("(status = 'confirmed' AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL) OR (status <> 'confirmed' AND confirmed_by IS NULL AND confirmed_at IS NULL)");
    t.check('confirmed_at IS NULL OR (confirmed_at >= created_at AND updated_at >= confirmed_at)');
    t.index(['invoice_id', 'reference', 'currency', 'amount']);
  });
  await schema().createTable('audit_logs', t => {
    base(t, false); ref(t, 'actor_id', 'users', true); txt(t, 'action');
    t.check("action IN ('user.role_assigned','user.role_removed','invoice.created','invoice.submitted','invoice.updated','invoice.approved','invoice.rejected','invoice.paid','invoice.voided','payment.created','payment.confirmed','payment.status_overridden')");
    t.text('entity_type').notNullable(); t.check("entity_type IN ('user','invoice','payment')");
    t.uuid('entity_id').notNullable(); t.jsonb('before_data'); t.jsonb('after_data');
    t.timestamp('occurred_at', { useTz: true }).notNullable(); t.check('created_at >= occurred_at');
    t.index(['entity_type', 'entity_id', 'occurred_at']); t.index(['action', 'occurred_at']);
  });
}

export async function down(knex) {
  for (const table of ['audit_logs', 'payments', 'invoice_approvals', 'invoices', 'vendors', 'role_permissions', 'user_roles', 'permissions', 'roles', 'users', 'employees']) {
    await knex.schema.withSchema('business').dropTable(table);
  }
}