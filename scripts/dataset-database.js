import knex from 'knex';
import config from '../apps/api/database/knexfile.js';
import { generate } from '../apps/api/database/generators/index.js';
import { validate } from '../apps/api/database/validation/validate.js';
import { assertLocal,seedEmpty,resetData } from '../apps/api/database/seeds/workflow.js';
import { writeArtifacts } from '../apps/api/database/generators/artifacts.js';
import { TABLES } from '../apps/api/database/generators/core.js';
import { inspectDatabase } from '../apps/api/database/inspect.js';
const mode=process.argv[2];
const db=knex(config);
try {
  if(!['seed','reset','validate','status'].includes(mode)) throw new Error('Unknown database action');
  if(['seed','reset'].includes(mode)) assertLocal(config);
  if(mode==='status') {
    const result=await inspectDatabase(db);
    console.log(JSON.stringify(result,null,2));
    if(!result.ready) process.exitCode=1;
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
