import '../apps/api/src/config/env.js';
import { generate } from '../database/generators/index.js';
import { validate } from '../database/validation/validate.js';
import { writeArtifacts } from '../database/generators/artifacts.js';
const dataset=generate(Number(process.env.AUDITLENS_DATA_SEED||20260914));
console.log(JSON.stringify(validate(dataset),null,2));
await writeArtifacts(dataset);
