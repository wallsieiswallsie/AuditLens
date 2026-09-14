import test from 'node:test';
import assert from 'node:assert/strict';
import { assertReset } from '../apps/api/database/seeds/workflow.js';
test('destructive opt-in never permits production', () => {
  assert.throws(() => assertReset({}));
  assert.throws(() => assertReset({ NODE_ENV: 'production', AUDITLENS_ALLOW_LOCAL_RESET: 'YES' }));
  assert.doesNotThrow(() => assertReset({ NODE_ENV: 'development', AUDITLENS_ALLOW_LOCAL_RESET: 'YES' }));
});
