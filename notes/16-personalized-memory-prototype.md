---
id: AH-016
title: Personalized-memory prototype
status: proposed
maturity: proposed
source_artifact: synthesis of depot patterns and user-provided brief
source_date: 2026-09-14
---

# Personalized-Memory Prototype

## Use When

- The concepts need to become a small, testable research system without premature distributed architecture or fine-tuning.

## Core Pattern

Build one inspectable external-memory service that persists typed contracts, runs consolidation asynchronously, and exposes retrieval traces for experiments.

## Problem It Solves

- A broad research architecture is difficult to validate without one end-to-end vertical slice.
- Premature infrastructure and autonomous promotion can hide lifecycle defects.

## Source Implementation Status

- The brief suggests a Python, FastAPI, PostgreSQL, pgvector, LLM API, and scheduler prototype.
- This note converts that suggestion into bounded entities, phases, and acceptance criteria; no implementation exists yet.

## Minimal Architecture

```text
client
  -> interaction API
  -> response model
  -> event + outcome store
  -> candidate extractor
  -> admission evaluator
  -> consolidation worker
  -> typed memory store + vector index
  -> retrieval API
  -> context manifest
  -> response model
  -> feedback event
```

## Suggested Stack

- Python and FastAPI for the service boundary.
- PostgreSQL for events, candidates, memory versions, and audit data.
- `pgvector` for semantic candidate search, combined with structured filters.
- One LLM API behind extraction, consolidation, and generation adapters.
- Cron or a simple worker for scheduled and event-triggered consolidation.
- JSON Schema or Pydantic models for every boundary.

The stack is replaceable. The contracts and traces are the research asset.

## Minimal Data Model

| Entity | Purpose |
|---|---|
| InteractionEvent | User input, agent output, outcome, and consent state |
| MemoryCandidate | Temporary extracted claim plus scores and evidence |
| MemoryRecord | Current typed, scoped, versioned belief or procedure |
| MemoryRevision | Immutable transition and rationale |
| RetrievalDecision | Selected or filtered memory with score components |
| FeedbackEvent | Observed usefulness, correction, success, or harm |
| ExperimentRun | Configuration, dataset, seed, metrics, and artifacts |

## MVP Sequence

1. Define and validate the six data contracts.
2. Capture interactions and extract candidates without promotion.
3. Add deterministic policy gates and manual candidate review.
4. Add scheduled consolidation with versioned dry-run output.
5. Add hybrid retrieval and bounded context manifests.
6. Add stage-level feedback and longitudinal evaluation.
7. Enable autonomous promotion only after baseline results and safety tests.

## First Vertical Slice

Support one memory class: explicit communication preferences. Require direct evidence, user scope, manual promotion, and explainable retrieval. This proves the full loop before adding inferred facts, agent lessons, or autonomous consolidation.

## Non-Goals

- Continuous model-weight updates.
- Multi-tenant cloud infrastructure.
- Unreviewed inference of sensitive traits.
- Storing every conversation turn indefinitely.
- Treating vector similarity as the complete memory policy.

## Portability Limits

- The suggested stack is convenient, not mandatory.
- A research prototype does not establish production privacy, scale, reliability, or compliance.
- Autonomous promotion should remain disabled until evaluation and governance gates pass.

## Acceptance Criteria

- Every response can show which memories influenced it.
- Every durable memory links to evidence and revision history.
- Contradictions revise or dispute memory instead of silently overwriting it.
- User deletion prevents future retrieval and invalidates dependent derivations.
- The experiment harness can compare no-memory and structured-memory baselines.

## Generalized Primitive

A **reference memory service** proves the lifecycle and instrumentation before optimization, automation, or fine-tuning.

## Plugin Implication

- Add the memory service behind the existing capability and runtime adapters.
- Keep extraction, consolidation, retrieval, and model providers replaceable through typed interfaces.

## Evidence And Confidence

- **Observed:** Existing depot notes provide routing, typed runtime, bounded context, guarded LLM decisions, validation, and durable learning patterns.
- **Proposed:** The service shape and stack synthesize those patterns with the user-provided brief.
- **Confidence:** High that this is sufficient for a research prototype; production scale and compliance remain out of scope.

## Open Questions

- Should the first implementation be a standalone service or a library embedded in the existing pluggable harness CLI?
