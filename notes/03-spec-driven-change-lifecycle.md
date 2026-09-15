---
id: AH-003
title: Spec-driven change lifecycle
status: initial
maturity: observed
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Spec-Driven Change Lifecycle

## Use When

- Behavior is non-trivial, cross-cutting, ambiguous, or likely to outlive one coding session.

## Core Pattern

Represent change work as explicit actions over durable artifacts rather than one undifferentiated “implement” prompt.

## Observed Actions

| Action | Purpose | Allowed output |
|---|---|---|
| Explore | Understand the problem and code reality | Findings, options, diagrams, artifact updates; no implementation |
| Propose | Create the change definition | Proposal, design, specs, tasks |
| Apply | Execute tasks against declared context | Narrow code/docs changes and checked task items |
| Archive | Verify completion and preserve history | Synced specs and archived change |

## Supporting Pattern: Requirement Refinement

Before proposing work, map the request through four lenses:

- Existing code and ownership.
- Product/operator flow.
- API and data contracts.
- Simplicity and smallest viable change.

The result separates current implementation, architecture-only intent, cross-repo dependencies, acceptance criteria, exclusions, and real blockers.

## Guardrails

- Do not implement while in exploration mode.
- Do not guess a change when selection is ambiguous.
- Read the workflow-provided context files rather than assuming artifact names.
- Update task state immediately after completion.
- If implementation invalidates the design, repair the artifact instead of silently diverging.
- Archive warnings require an explicit decision; they should not disappear in automation.

## Generalized Primitive

A **change controller** should expose actions over an artifact graph:

```text
idea -> proposal -> design/specs -> tasks -> implementation -> verification -> archive
```

Actions can be entered fluidly, but each action has permissions, preconditions, and output contracts.

## Plugin Implication

- Workflow adapters for different spec systems.
- Action-level capability restrictions.
- Machine-readable artifact status and dependency graph.
- Checkpoints when ambiguity, blockers, or spec drift appear.

## Evidence

- `pipeline-fl-control-plane@df513fa4:.agents/skills/openspec-explore/SKILL.md` — non-implementation exploration stance.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/openspec-propose/SKILL.md` — artifact generation action.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/openspec-apply-change/SKILL.md` — task execution protocol.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/openspec-archive-change/SKILL.md` — completion and sync checks.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/requirement-refinement/SKILL.md` — code-grounded requirement alignment.

## Open Questions

- What is the smallest workflow interface that can support OpenSpec without coupling the tool to OpenSpec?
