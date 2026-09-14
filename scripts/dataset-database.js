import knex from 'knex';
import config from '../database/knexfile.js';
import { generate } from '../database/generators/index.js';
import { validate } from '../database/validation/validate.js';
import { assertLocal,seedEmpty,resetData } from '../database/seeds/workflow.js';
import { writeArtifacts } from '../database/generators/artifacts.js';
import { TABLES } from '../database/generators/core.js';
const mode=process.argv[2];
const db=knex(config);
try {
  if(!['seed','reset','validate','status'].includes(mode)) throw new Error('Unknown database action');
  if(['seed','reset'].includes(mode)) assertLocal(config);
  if(mode==='status') {
    const [done,pending]=await db.migrate.list();
    for(const schema of ['business','audit']) if(!(await db.raw('SELECT 1 FROM information_schema.schemata WHERE schema_name=?',[schema])).rows.length) throw new Error(`Missing ${schema} schema`);
    if(pending.length) throw new Error(`${pending.length} pending migrations`);
    console.log(`Schemas business/audit and public.knex_migrations verified; ${done.length} migrations applied, none pending.`);
  } else if(mode==='reset') {await resetData(db); console.log('Local business rows deleted. Run db:seed next.');}
  else {
    const dataset=generate(Number(process.env.AUDITLENS_DATA_SEED||20260914));
    validate(dataset);
    if(mode==='seed') {await seedEmpty(db,dataset);await writeArtifacts(dataset);console.log('Synthetic dataset committed.');}
    const tables=await db.transaction(async trx=>{
      await trx.raw('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');
      const result={};
      for(const name of TABLES) result[name]=JSON.parse(JSON.stringify(await trx.withSchema('business').table(name).select('*')));
      return result;
    });
    console.log(JSON.stringify(validate({...dataset,tables}),null,2));
  }
} catch(error) {console.error(`Database ${mode} failed. Check connection availability, local-write safeguards, migrations and dataset validity.`);process.exitCode=1;}
finally {await db.destroy();}
