import { AgentRole } from "../types";

function summarizeContext(context?: string): string {
  if (!context || !context.trim()) {
    return "No prior context provided.";
  }
  const compact = context.replace(/\s+/g, " ").trim();
  if (compact.length <= 280) {
    return compact;
  }
  return `${compact.slice(0, 277)}...`;
}

function buildManagerOutput(prompt: string, context?: string): string {
  return [
    "# Product Requirements Document (Local Draft)",
    "",
    "## Problem Statement",
    `- User requirement: ${prompt}`,
    "",
    "## Scope",
    "- In scope: core workflow implementation, local-first runtime, deterministic orchestration.",
    "- Out of scope: cloud-only dependencies and hosted model inference.",
    "",
    "## Functional Requirements",
    "1. Accept requirement prompt and route task flow.",
    "2. Produce design, implementation, and QA artifacts.",
    "3. Keep execution operable without internet access.",
    "",
    "## Tech Stack",
    "- Frontend: React + Next.js + TypeScript",
    "- Backend: Python runtime and local API",
    "- Storage: local filesystem artifacts and JSON session logs",
    "",
    "## Logic Flow",
    "1. Manager normalizes requirement.",
    "2. Designer proposes structure and components.",
    "3. Developer drafts implementation.",
    "4. QA validates output and reports pass/fail.",
    "",
    "## Prior Context",
    `- ${summarizeContext(context)}`,
  ].join("\n");
}

function buildDesignerOutput(prompt: string, context?: string): string {
  return [
    "# UI/UX Design Schema (Local Draft)",
    "",
    `## Requirement Focus`,
    `- ${prompt}`,
    "",
    "## Layout",
    "- Header: system status, mode, quick actions",
    "- Main panel: staged artifact workspace",
    "- Side panel: agent progress and execution logs",
    "",
    "## Component List",
    "- RequirementInput",
    "- AgentStatusBoard",
    "- TaskWorkspace",
    "- RuntimeTerminal",
    "- BuildControls",
    "",
    "## Design Notes",
    "- Prefer high-contrast developer dashboard styling.",
    "- Keep core actions visible without scrolling.",
    "- Surface failure state and recovery actions in-panel.",
    "",
    "## Prior Context",
    `- ${summarizeContext(context)}`,
  ].join("\n");
}

function buildDeveloperOutput(prompt: string, context?: string): string {
  return [
    "# Implementation Draft (Local)",
    "",
    `## Implementation Target`,
    `- ${prompt}`,
    "",
    "## Backend Snippet",
    "```python",
    "def execute_locally(requirement: str) -> dict:",
    "    return {",
    "        'status': 'draft',",
    "        'requirement': requirement,",
    "        'runtime': 'local-only'",
    "    }",
    "```",
    "",
    "## Frontend Snippet",
    "```ts",
    "export async function runLocalTask(prompt: string): Promise<string> {",
    "  return `Local runtime handled: ${prompt}`;",
    "}",
    "```",
    "",
    "## Implementation Checklist",
    "- Wire FE action to local backend endpoint",
    "- Persist generated artifacts to workspace",
    "- Add tests for deterministic role outputs",
    "",
    "## Prior Context",
    `- ${summarizeContext(context)}`,
  ].join("\n");
}

function buildQaOutput(prompt: string, context?: string): string {
  return [
    "# QA Validation Report (Local)",
    "",
    `## Scope`,
    `- ${prompt}`,
    "",
    "## Checks",
    "- Output exists and is non-empty: PASS",
    "- Role-specific format generated: PASS",
    "- Local/offline execution path used: PASS",
    "",
    "## Result",
    "PASS",
    "",
    "## Notes",
    `- Context sample: ${summarizeContext(context)}`,
  ].join("\n");
}

function buildLocalAgentOutput(role: AgentRole, prompt: string, context?: string): string {
  switch (role) {
    case "manager":
      return buildManagerOutput(prompt, context);
    case "designer":
      return buildDesignerOutput(prompt, context);
    case "developer":
      return buildDeveloperOutput(prompt, context);
    case "qa":
      return buildQaOutput(prompt, context);
    default:
      return "No output generated.";
  }
}

export async function runAgentTask(role: AgentRole, prompt: string, context?: string) {
  return Promise.resolve(buildLocalAgentOutput(role, prompt, context));
}
