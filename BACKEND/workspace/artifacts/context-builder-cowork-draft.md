# Skill Execution Draft: context-builder-cowork

- Version: 1.0
- Source: C:\Users\Anup\Documents\projects\Project-Nexus\claude-skills-kit-main\skills\context-builder-cowork\SKILL.md
- Mode: new

## Prompt
generate closure report for project completion

## Execution Plan
1. Validate required inputs from the user against skill instructions.
2. Ask clarification questions only for missing mandatory fields.
3. Generate structured output using the skill's contract.
4. Present draft and wait for explicit approval before finalization.
5. Persist approved artifact and execution log.

## Assumptions
- Language inferred from user prompt.
- Prompt is short; runtime may request clarification for required fields.
- Skill has no explicit trigger list in frontmatter; description-based routing was used.

## Detected Issues
- None

## Approval
Status: draft
Action required: Approve, revise, or reject.