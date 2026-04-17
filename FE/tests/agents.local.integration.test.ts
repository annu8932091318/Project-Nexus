import assert from 'node:assert/strict';

import { runAgentTask } from '../src/services/gemini';

async function testManagerAgent(): Promise<void> {
  const result = await runAgentTask('manager', 'Build a local project runtime', 'prior notes');
  assert.ok(result.includes('Product Requirements Document'));
  assert.ok(result.includes('local-first runtime'));
}

async function testDesignerAgent(): Promise<void> {
  const result = await runAgentTask('designer', 'Design the dashboard UI', 'manager context');
  assert.ok(result.includes('UI/UX Design Schema'));
  assert.ok(result.includes('Component List'));
}

async function testDeveloperAgent(): Promise<void> {
  const result = await runAgentTask('developer', 'Implement backend and frontend stubs', 'design context');
  assert.ok(result.includes('Implementation Draft'));
  assert.ok(result.includes('```python'));
  assert.ok(result.includes('```ts'));
}

async function testQaAgent(): Promise<void> {
  const result = await runAgentTask('qa', 'Validate local runtime outputs', 'developer context');
  assert.ok(result.includes('QA Validation Report'));
  assert.ok(result.includes('PASS'));
}

async function run(): Promise<void> {
  await testManagerAgent();
  await testDesignerAgent();
  await testDeveloperAgent();
  await testQaAgent();
  console.log('local agent integration tests passed');
}

void run().catch((error) => {
  console.error(error);
  process.exit(1);
});
