import { readFile,writeFile } from 'node:fs/promises';
import { migrationSql } from './migration-sql.js';
import { generate } from '../database/generators/index.js';
import { FOREIGN_KEYS } from '../database/validation/validate.js';
const statements=await migrationSql(), fixture=generate();
const descriptions={id:'Immutable synthetic source UUID',created_at:'Source insertion instant',updated_at:'Last source modification instant',employee_number:'Unique fictional HR reference',full_name:'Fictional employee display name',department:'Fictional job department',hired_at:'Employment start instant',ended_at:'Employment end; required for inactive employees',employee_id:'Employee owner; human accounts require an owner',email:'Lowercase synthetic account identifier',account_type:'Human or service identity',last_login_at:'Last successful login; null means never used',code:'Stable unique master reference',name:'Fictional display name',is_privileged:'Project policy sensitive administrative capability flag',user_id:'Assigned source account',role_id:'Assigned or granting source role',permission_id:'Granted capability',vendor_id:'Fictional supplier issuing invoice',reference:'External business reference; duplicates represent control failures',amount:'Positive gross amount; serialized as exact decimal string',currency:'Fixture currency; IDR only',created_by:'Source creator account',supporting_reference:'Synthetic reference only; never fetch arbitrary URLs',invoice_id:'Parent invoice',decided_by:'Account making the approval decision',decision:'Approved or rejected decision',decided_at:'Decision instant; authoritative approval time',confirmed_by:'Confirmer; required only when confirmed',confirmed_at:'Confirmation instant; required only when confirmed',actor_id:'Source event actor; null for system events',action:'Allowlisted source event action',entity_type:'Source entity kind',entity_id:'Source snapshot identifier; deliberately no FK',before_data:'Redacted values before change',after_data:'Redacted values after change',occurred_at:'Source event instant'};
function parts(sql) {const out=[];let depth=0,start=0,quote=false;for(let i=0;i<sql.length;i++){if(sql[i]==="'")quote=!quote;if(!quote){if(sql[i]==='(')depth++;if(sql[i]===')')depth--;if(sql[i]===','&&depth===0){out.push(sql.slice(start,i).trim());start=i+1;}}}out.push(sql.slice(start).trim());return out;}
let dictionary='## IMPLEMENTED IN PHASE 1 — business source tables\n\nGenerated from the Knex PostgreSQL DDL by `npm run docs:schema`. Column inventory, types, keys, checks and indexes below match the migration. PostgreSQL execution remains pending; see [verification](VERIFICATION.md). All data is fictional; sensitivity describes the analogous real-world field. No SQL defaults or automatic timestamp triggers exist: writers supply UUIDs and UTC timestamps. Foreign keys use ON DELETE RESTRICT. Primary keys imply NOT NULL. Approvals/logs are append-only by convention; runtime enforcement is deferred.\n\n';
let erd='### A. Demo Business System — IMPLEMENTED IN PHASE 1\n\nMigration implemented; runtime verification pending. Names use `business_` to represent the business schema.\n\n```mermaid\nerDiagram\n';
for(const stmt of statements.filter(s=>s.startsWith('create table'))) {
 const [,table,body]=stmt.match(/^create table "business"\."(\w+)" \((.*)\)$/);
 const fields=parts(body), pk=fields.find(p=>p.includes('primary key')), related=statements.filter(s=>s.includes(`"business"."${table}"`));
 dictionary+=`### business.${table}\n\n| Column | Database type | Nullable | PK/FK | Constraint | Description | Example | Sensitivity |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n`;
 erd+=`  business_${table} {\n`;
 for(const field of fields) {
  const col=field.match(/^"(\w+)" (uuid|text|timestamptz|boolean|jsonb|decimal\(18, 2\)|char\(3\))( not null)?$/);if(!col)continue;
  const [,name,type,required]=col,isPk=pk.includes(`"${name}"`),fk=FOREIGN_KEYS[table]?.[name];
  const unique=related.some(s=>s.includes(`unique ("${name}")`));
  const checks=fields.filter(p=>p.startsWith('check')&&new RegExp(`\\b${name}\\b`).test(p));
  const constraint=[unique?'UNIQUE':null,...checks].filter(Boolean).join('; ')||'—';
  let example=fixture.tables[table][0][name];if(example===null)example='null';else if(typeof example==='object')example=JSON.stringify(example);else example=String(example);
  const sensitivity=['email','full_name','employee_id','hired_at','ended_at','last_login_at','created_by','decided_by','confirmed_by','actor_id'].includes(name)?'personal (synthetic)':name.endsWith('_data')?'sensitive (synthetic)':['amount','currency','reference'].includes(name)?'financial (synthetic)':'internal';
  dictionary+=`| ${name} | ${type.replace('decimal','numeric')} | ${required||isPk?'no':'yes'} | ${[isPk?'PK':null,fk?`FK business.${fk}.id`:null].filter(Boolean).join(', ')||'—'} | ${constraint} | ${descriptions[name]||'Employment/account/workflow state; allowed values in constraint'} | ${example} | ${sensitivity} |\n`;
  erd+=`    ${type.startsWith('decimal')?'numeric':type.startsWith('char')?'char':type} ${name}${isPk?' PK':fk?' FK':''}\n`;
 }
 erd+='  }\n';
 for(const [col,parent] of Object.entries(FOREIGN_KEYS[table]||{})) {const field=fields.find(f=>f.startsWith(`"${col}"`));erd+=`  business_${parent} ${field.includes('not null')?'||':'|o'}--o{ business_${table} : ${col}\n`;}
 dictionary+='\nIndexes: '+(related.filter(s=>s.startsWith('create index')).map(s=>'`'+s.match(/\((.*)\)$/)[1].replaceAll('"','')+'`').join('; ')||'none beyond keys')+'. Primary and unique constraints also create indexes.\n\n';
}
erd+='```\n\n';
const dictFile=new URL('../docs/05-DATA-DICTIONARY.md',import.meta.url), erdFile=new URL('../docs/04-ERD.md',import.meta.url);
const oldDict=await readFile(dictFile,'utf8'), oldErd=await readFile(erdFile,'utf8');
const updatedDict='# Data dictionary\n\n'+dictionary+'## PLANNED — audit schema\n\nThe following audit tables are proposed only. Common planned columns: id uuid primary key; created_at timestamptz not null; mutable entities also have updated_at timestamptz not null. Junctions use composite primary keys. No audit domain migrations exist.\n\n'+oldDict.slice(oldDict.indexOf('## audit.users'));
const updatedErd=oldErd.slice(0,oldErd.indexOf('### A.'))+erd+oldErd.slice(oldErd.indexOf('### B.'));
for(const [file,next,old] of [[dictFile,updatedDict,oldDict],[erdFile,updatedErd,oldErd]]) {
 if(process.argv.includes('--check')) {if(next!==old) throw new Error(`${file.pathname} is stale; run docs:schema`);}
 else await writeFile(file,next);
}
console.log('ERD and dictionary column/constraint inventories match compiled PostgreSQL migration.');
