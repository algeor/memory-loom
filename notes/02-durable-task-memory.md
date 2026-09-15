---
id: AH-002
title: Durable task memory and learning
status: initial
maturity: observed
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Durable Task Memory And Learning

## Use When

- Work spans turns, sessions, repositories, risky operations, or unresolved decisions.

## Core Pattern

Chat history is a cache. A small workspace note is the authoritative task state.

## Observed Implementation

- Active notes use a fixed structure: goal, current state, decisions, progress, blockers, next step.
- `Current State` and `Next Step` are kept accurate after every meaningful milestone.
- OpenSpec tasks remain in their change artifact rather than being duplicated into generic notes.
- Active local notes and processed cross-task retrospectives use different storage locations.
- Retrospectives classify learnings, promote stable ones into docs or skills, and apply explicit retention decisions.
- Automation may remove only clearly safe material; ambiguous deletion and guidance promotion stay interactive.

## Why The Shape Matters

- **Goal** prevents local activity from replacing the actual outcome.
- **Decisions with reasons** preserve why, not just what.
- **Progress log** makes validation and failure history recoverable.
- **Blockers** distinguish unfinished work from forgotten work.
- **Single next step** makes resumption cheap.

## Generalized Primitive

Use two stores:

1. **Task state store** — mutable, local, resumable, short-lived.
2. **Learning store** — distilled, deduplicated, durable, reusable.

Promotion should be evidence-based: repeated occurrence, stable repository rule, or a lesson likely to prevent future mistakes.

## Boundary With Personalized Memory

- This note covers resumable work state and repository-level learning.
- User preferences, evolving beliefs, reusable behavioral lessons, and cross-session retrieval require a separate lifecycle.
- See [Continual personalized memory loop](10-continual-personalized-memory.md) for that extension.

## Portability Limits

- Storage paths should be configurable.
- Retention periods are policy, not universal truth.
- Notes must never contain secrets or raw credential-bearing logs.

## Plugin Implication

- `note start|resume|update|close`
- `retrospective collect|triage|promote|cleanup`
- Schema validation for required note sections.
- Refuse deletion when blockers, open next steps, or unique unpromoted evidence remain.

## Evidence

- `pipeline-fl-control-plane@df513fa4:docs/agent-long-task-notes.md` — active note workflow and state contract.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/long-task-notes/SKILL.md` — portable skill form.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/notes-retrospective/SKILL.md` — learning extraction and retention policy.
- `pipeline-fl-control-plane@df513fa4:.codex/notes/skill-note-location-sync.md` — an actual durable decision record.

## Open Questions

- How should the tool detect that a learning is repeated without leaking private task content into a global index?
