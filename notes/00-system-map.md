---
id: AH-000
title: Harnessing system map
status: initial
maturity: inferred
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Harnessing System Map

## Core Pattern

An effective agent harness is not one prompt. It is a layered control system with explicit boundaries, durable state, capability injection, and feedback.

## The Five Planes

| Plane | Responsibility | Source expression |
|---|---|---|
| Instruction | Tell an agent how to work and where to look | Thin `AGENTS.md`, focused skills, command wrappers |
| Knowledge | Supply the smallest authoritative context | Architecture index, focused docs, source/test links |
| Workflow | Move work through explicit states | Explore → propose → apply → archive |
| Execution | Bind prompts to tools, data, identity, and isolation | Declarative handlers, jobs, skills, MCPs, typed requests |
| Learning | Preserve state and improve future behavior | Task notes, retrospectives, promotion into docs/skills |

## Control Loop

```text
task intent
  -> route context
  -> refine requirement
  -> select workflow state
  -> assemble capabilities
  -> execute in a boundary
  -> collect typed evidence
  -> validate by risk
  -> store task state
  -> promote durable learning
  -> improve routes, skills, and checks
```

## Important Separations

- **Instructions vs evidence:** A source repo's `AGENTS.md` explains that repo's harness. It does not automatically govern this depot.
- **Control plane vs data plane:** Orchestration state stays small and structured; large evidence and artifacts live behind bounded readers.
- **Deterministic vs probabilistic decisions:** Mechanical filters run before LLM judgment.
- **Active memory vs durable learning:** Current task notes are not the same artifact as promoted guidance.
- **Configuration vs implementation:** Capability declarations can evolve separately from runtime code.
- **Tool behavior vs identity privilege:** A read-only tool surface does not prove the enclosing process has read-only credentials.

## Generalized Primitive

The future tool should orchestrate these planes through composable interfaces rather than embed one monolithic agent loop.

## Continual Personalization Extension

The learning plane can extend beyond repository guidance into user-scoped, evolving memory:

```text
interaction -> candidate -> consolidation -> typed memory
            -> retrieval -> behavior -> feedback -> interaction
```

This extension is specified in `AH-010` through `AH-016`. It remains separate from active task state so temporary work, user beliefs, and reusable agent lessons do not collapse into one store.

## Evidence

- `pipeline-fl-control-plane@df513fa4:AGENTS.md` — thin instruction router.
- `pipeline-fl-control-plane@df513fa4:docs/design/architecture-index.md` — knowledge routing.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/openspec-explore/SKILL.md` — workflow states.
- `pipeline-fl-control-plane@df513fa4:docs/design/handler-model.md` — declarative execution model.
- `pipeline-fl-control-plane@df513fa4:docs/agent-long-task-notes.md` — durable task state.

## Open Questions

- Which plane should own policy conflicts when a plugin contributes instructions, tools, and validators together?
