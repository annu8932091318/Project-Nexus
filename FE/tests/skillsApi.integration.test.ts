import assert from 'node:assert/strict';

import { runSkillRuntime } from '../src/services/skillsApi';

interface MockResponse {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
}

type FetchMock = (input: string, init?: RequestInit) => Promise<MockResponse>;

const originalFetch = globalThis.fetch;

function setFetchMock(mock: FetchMock): void {
  (globalThis as { fetch: FetchMock }).fetch = mock;
}

async function testReturnsNullWhenApiNotConfigured(): Promise<void> {
  delete process.env.NEXT_PUBLIC_NEXUS_SKILL_API;

  const result = await runSkillRuntime('generate project plan');
  assert.equal(result, null);
}

async function testReturnsPayloadWhenSkillMatched(): Promise<void> {
  process.env.NEXT_PUBLIC_NEXUS_SKILL_API = 'http://localhost:8765';

  setFetchMock(async (_input, init) => {
    assert.equal(init?.method, 'POST');
    const payload = JSON.parse(String(init?.body));
    assert.equal(payload.prompt, 'weekly digest from notes');

    return {
      ok: true,
      status: 200,
      json: async () => ({
        matched_skill: 'weekly-digest-synthesizer',
        confidence: 0.88,
        mode: 'new',
        output: 'digest draft',
        assumptions: [],
        issues: [],
        artifacts: { draft: 'weekly-digest.md' },
      }),
    };
  });

  const result = await runSkillRuntime('weekly digest from notes');
  assert.ok(result);
  assert.equal(result?.matched_skill, 'weekly-digest-synthesizer');
  assert.equal(result?.artifacts.draft, 'weekly-digest.md');
}

async function testReturnsNullWhenNoSkillMatched(): Promise<void> {
  process.env.NEXT_PUBLIC_NEXUS_SKILL_API = 'http://localhost:8765';

  setFetchMock(async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      matched_skill: null,
      confidence: 0.2,
      mode: 'none',
      output: 'No matching skill found',
      assumptions: [],
      issues: [],
      artifacts: {},
    }),
  }));

  const result = await runSkillRuntime('random prompt');
  assert.equal(result, null);
}

async function testThrowsOnHttpError(): Promise<void> {
  process.env.NEXT_PUBLIC_NEXUS_SKILL_API = 'http://localhost:8765';

  setFetchMock(async () => ({
    ok: false,
    status: 503,
    json: async () => ({}),
  }));

  await assert.rejects(async () => runSkillRuntime('generate charter'), /status 503/);
}

async function run(): Promise<void> {
  try {
    await testReturnsNullWhenApiNotConfigured();
    await testReturnsPayloadWhenSkillMatched();
    await testReturnsNullWhenNoSkillMatched();
    await testThrowsOnHttpError();
    console.log('skillsApi integration tests passed');
  } finally {
    if (originalFetch) {
      (globalThis as { fetch: typeof originalFetch }).fetch = originalFetch;
    }
  }
}

void run();
