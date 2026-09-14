import { mkdir, writeFile } from 'node:fs/promises';
export async function writeArtifacts(dataset) {
  const root=new URL('../sample-data/',import.meta.url);
  await mkdir(new URL('examples/',root),{recursive:true});
  for(const [file,value] of [['ground-truth',dataset.groundTruth],['dataset-manifest',dataset.manifest],['fixture-policy',dataset.policy]]) await writeFile(new URL(`${file}.json`,root),JSON.stringify(value,null,2)+'\n');
  for(const table of ['users','invoices','payments','audit_logs']) await writeFile(new URL(`examples/${table.replaceAll('_','-')}.sample.json`,root),JSON.stringify(dataset.tables[table].slice(0,3),null,2)+'\n');
}
