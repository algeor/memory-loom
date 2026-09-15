# Agent Harnessing

A source-backed depot of reusable patterns for **steering, equipping, running, validating, and improving coding agents**.

This repository does not copy the product architecture of `pipeline-fl-control-plane`. It extracts the harnessing ideas demonstrated by that repository and reformulates them as portable building blocks.

## Core Model

```text
request
  │
  ▼
instruction router ──► focused knowledge pack
  │                         │
  ▼                         ▼
change workflow ─────► capability/runtime adapter
  │                         │
  ▼                         ▼
validation + evidence ◄── structured result
  │
  ▼
durable notes ──► retrospective ──► improved guidance
```

The central idea is a **closed-loop harness**:

1. Route the task to the smallest relevant instructions.
2. Ground decisions in code, specs, tests, and ownership boundaries.
3. Execute through declared capabilities and typed contracts.
4. Validate with risk-shaped checks.
5. Persist task state and promote repeated lessons back into the harness.

## Catalog

- [System map](notes/00-system-map.md)
- [Progressive instruction routing](notes/01-progressive-instruction-routing.md)
- [Durable task memory and learning](notes/02-durable-task-memory.md)
- [Spec-driven change lifecycle](notes/03-spec-driven-change-lifecycle.md)
- [LLM-first architecture knowledge](notes/04-llm-first-architecture-knowledge.md)
- [Declarative agent runtime](notes/05-declarative-agent-runtime.md)
- [Bounded tools and context shaping](notes/06-bounded-tools-and-context-shaping.md)
- [LLM decision guardrails](notes/07-llm-decision-guardrails.md)
- [Review, validation, and failure attribution](notes/08-review-and-validation.md)
- [Pluggable tool blueprint](notes/09-pluggable-tool-blueprint.md)
- [Continual personalized memory loop](notes/10-continual-personalized-memory.md)
- [Memory candidate admission](notes/11-memory-candidate-admission.md)
- [Typed evolving memory](notes/12-typed-evolving-memory.md)
- [Adaptive memory retrieval](notes/13-adaptive-memory-retrieval.md)
- [Memory governance and safety](notes/14-memory-governance-and-safety.md)
- [Personalized-memory evaluation](notes/15-personalized-memory-evaluation.md)
- [Personalized-memory prototype](notes/16-personalized-memory-prototype.md)

## Evidence Model

Each note distinguishes:

- **Observed** — directly present in source code or committed guidance.
- **Inferred** — a reusable principle derived from multiple observed choices.
- **Proposed** — a design direction for the future pluggable tool.

Source references use this form:

```text
pipeline-fl-control-plane@df513fa4:path/to/file#section-or-symbol
```

See [the source ledger](sources/pipeline-fl-control-plane.md) for scope and extraction status.

## Working Method

- Add one focused concept note at a time.
- Keep routing metadata near the top.
- Link deep evidence instead of duplicating it.
- Record rejected assumptions and portability limits.
- Treat `STATUS.md` as the durable continuation point.

## Current State

The depot now covers both repository-oriented agent harnessing and a proposed continual-personalization extension. The next pass should turn the memory event, candidate, record, retrieval, and feedback contracts into machine-readable schemas and a reference prototype.
