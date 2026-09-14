import '../apps/api/src/config/env.js';
import { generate } from '../apps/api/database/generators/index.js';
import { validate } from '../apps/api/database/validation/validate.js';
import { writeArtifacts } from '../apps/api/database/generators/artifacts.js';
const dataset=generate(Number(process.env.AUDITLENS_DATA_SEED||20260914));
console.log(JSON.stringify(validate(dataset),null,2));
await writeArtifacts(dataset);
