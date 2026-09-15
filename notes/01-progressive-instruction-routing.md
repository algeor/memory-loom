---
id: AH-001
title: Progressive instruction routing
status: initial
maturity: observed
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Progressive Instruction Routing

## Use When

- A repository has enough guidance that loading everything would dilute relevant context.

## Core Pattern

Keep the root instruction file small. Make it a router to task-specific authorities.

## Problem It Solves

- Context windows fill with irrelevant rules.
- Broad docs conflict with focused, current behavior.
- Agents invent workflows because they cannot find the owning document.
- Stale commands remain discoverable without being clearly superseded.

## Observed Implementation

- Root `AGENTS.md` identifies task classes and links the smallest matching document.
- Architecture work starts at an index, not the full architecture narrative.
- Skills use short names and descriptions for discovery, then load full instructions only when selected.
- Stale commands remain present but carry an explicit superseded notice and successor path.
- Repo routing names ownership boundaries before implementation begins.

## Generalized Primitive

An **instruction route** can be represented as:

```yaml
id: architecture
match:
  intents: [design, architecture, ownership]
load:
  - docs/design/architecture-index.md
avoid:
  - docs/design/legacy-overview.md
authority: focused-docs-and-source
```

The router should select routes by task intent, touched paths, and requested action. It should also expose why each document was loaded.

## Portability Limits

- File names such as `CLAUDE.md` and `AGENTS.md` are host-specific conventions.
- Instruction precedence differs by agent platform.
- Routing does not replace conflict resolution; authority still needs to be declared.

## Plugin Implication

- Provide a route registry.
- Build a minimal context pack for the chosen route.
- Warn when a source is marked stale or superseded.
- Record loaded and intentionally skipped sources for auditability.

## Evidence

- `pipeline-fl-control-plane@df513fa4:AGENTS.md` — thin router and smallest-document rule.
- `pipeline-fl-control-plane@df513fa4:docs/agent-task-routing.md` — repo and subsystem ownership routing.
- `pipeline-fl-control-plane@df513fa4:docs/design/architecture-index.md` — task-shaped architecture routes.
- `pipeline-fl-control-plane@df513fa4:.claude/commands/cicd-deployment.md` — explicit stale-command marker.

## Open Questions

- Should route selection be purely declarative, or may a classifier propose routes that must then pass deterministic checks?
