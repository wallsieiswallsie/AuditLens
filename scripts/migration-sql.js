import knex from 'knex';
import { up,down } from '../apps/api/database/migrations/20260914035028_create_business_domain.js';
export async function migrationSql(direction='up') {
  const db=knex({client:'pg'}), statements=[];
  db.client.runner=builder=>({run:async()=>{statements.push(...[builder.toSQL()].flat().map(q=>q.sql));return [];}});
  try {await (direction==='up'?up:down)(db);return statements;} finally {await db.destroy();}
}
