export async function up(knex) {
  await knex.schema.createSchema('business');
  await knex.schema.createSchema('audit');
}

export async function down(knex) {
  // RESTRICT deliberately refuses rollback once either schema contains domain tables.
  await knex.raw('DROP SCHEMA audit RESTRICT');
  await knex.raw('DROP SCHEMA business RESTRICT');
}