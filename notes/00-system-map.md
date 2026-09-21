---
id: AH-000
title: Harnessing system map
kind: evidence-note
claim_status: inferred
verification: source-checked
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

## Inference

The five-plane model is a synthesis, not a structure named by the source. It is useful because it prevents instructions, evidence, workflow state, execution privileges, and durable learning from collapsing into one prompt or store.

## Limits

- One repository demonstrates the ingredients, not the completeness or superiority of the five-plane taxonomy.
- The source concerns repository and operational harnessing, not personalized memory.

## Design Relevance

Memory Loom reuses two narrow lessons: keep memory separate from current task state, and preserve provenance through validation. This source does not show that user memory improves behavior.

## Evidence

- `pipeline-fl-control-plane@df513fa4:AGENTS.md` — thin instruction router.
- `pipeline-fl-control-plane@df513fa4:docs/design/architecture-index.md` — knowledge routing.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/openspec-explore/SKILL.md` — workflow states.
- `pipeline-fl-control-plane@df513fa4:docs/design/handler-model.md` — declarative execution model.
- `pipeline-fl-control-plane@df513fa4:docs/agent-long-task-notes.md` — durable task state.

## Open Question

- Does the five-plane taxonomy remain useful when tested against other agent systems?
