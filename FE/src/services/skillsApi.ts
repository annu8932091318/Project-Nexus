export interface SkillApiResponse {
  matched_skill: string | null;
  confidence: number;
  mode: string;
  output: string;
  assumptions: string[];
  issues: string[];
  artifacts: Record<string, string>;
}

export async function runSkillRuntime(prompt: string): Promise<SkillApiResponse | null> {
  const baseUrl = process.env.NEXT_PUBLIC_NEXUS_SKILL_API;
  if (!baseUrl) {
    return null;
  }

  const response = await fetch(`${baseUrl.replace(/\/$/, '')}/run-skill`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    throw new Error(`Skill API request failed with status ${response.status}`);
  }

  const payload = (await response.json()) as SkillApiResponse;
  if (!payload.matched_skill) {
    return null;
  }

  return payload;
}
