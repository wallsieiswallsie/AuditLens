import { context, VERSION, AS_OF, COUNTS, digest, ordered } from './core.js';
import { referenceData } from './reference.js';
import { normalTransactions } from './transactions.js';
import { inject } from './anomalies.js';
import { activityLogs } from './logs.js';
export function generate(seed=20260914) {
  const c=context(seed), {tables,policy}=referenceData(c);
  normalTransactions(c,tables);
  const state=inject(c,tables);
  activityLogs(c,tables,state);
  const tableHashes=Object.fromEntries(Object.entries(tables).map(([name,rows])=>[name,digest(ordered(rows))]));
  const manifest={datasetVersion:VERSION,seed,generatedAt:AS_OF,asOf:AS_OF,policyVersion:policy.version,counts:Object.fromEntries(Object.entries(tables).map(([name,rows])=>[name,rows.length])),expectedAnomalyCounts:COUNTS,tableHashes,logicalSha256:digest(tableHashes)};
  return {tables,policy,groundTruth:state.truth,manifest};
}
