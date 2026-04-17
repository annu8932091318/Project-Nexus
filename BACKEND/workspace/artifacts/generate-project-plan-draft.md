# PM Skill Draft: generate-project-plan

- Phase: 2 — Planning
- Mode: new
- Template: project-plan-ru.md
- Target file: project-plan.md
- Skill key: project-management-kit/generate-project-plan

## Prompt
generate project plan from approved charter

## Intake Checklist
- Verify required upstream artifacts are present and approved.
- Detect and resolve contradictions before drafting content.
- Ask only minimum clarifying questions needed for mandatory fields.

## Drafting Workflow
1. Build a normalized input model (goals, scope, dates, owners, constraints).
2. Populate all required sections and placeholders from verified inputs.
3. Flag all assumptions explicitly and keep them auditable.
4. Run checklist validation from skill instructions before presenting.
5. Request approval, then finalize output file and log update recommendation.

## Dependency Guidance
- Suggested next skill after approval: generate-risk-register (detailed) and generate-comm-plan

## Assumptions
- Language inferred from user prompt.
- Prompt is short; runtime may request clarification for required fields.

## Detected Issues
- None

## Approval
Status: draft
Action required: Approve, revise, or reject.