---
id: AH-010
title: Continual personalized memory loop
status: proposed
maturity: proposed
source_artifact: user-provided continual-personalization brief
source_date: 2026-09-14
---

# Continual Personalized Memory Loop

## Use When

- An agent should improve across interactions with the same user without changing model weights after every turn.

## Core Pattern

Transform selected interaction evidence into evolving beliefs, skills, and lessons; retrieve only the useful subset; then use outcomes as new evidence.

```text
experience
  -> candidate
  -> evidence
  -> consolidation
  -> belief | skill | lesson
  -> retrieval
  -> behavior
  -> feedback
  -> next experience
```

## Problem It Solves

- Chat history is too large, noisy, and transient to serve as durable learning.
- Saving every turn to a vector database preserves data, not judgment.
- Immediate fine-tuning is expensive, difficult to reverse, and unsafe for unstable preferences.

## Source Implementation Status

- The brief proposes the lifecycle and research framing but does not provide an implemented system.
- Existing depot patterns supply analogous task-memory, routing, guardrail, and validation primitives.

## Two Learning Goals

1. **User adaptation** — learn preferences, stable facts, recurring goals, and context-dependent exceptions.
2. **Agent improvement** — remember corrections, failed reasoning patterns, and procedures that reduce repeated mistakes.

Keep these goals distinguishable. A user preference is not the same claim as an agent lesson.

## System Boundary

| Stage | Responsibility | Durable output |
|---|---|---|
| Interaction capture | Record the minimum useful event and outcome | Evidence reference |
| Candidate extraction | Propose possible memories | Candidate record |
| Admission | Score, reject, defer, or queue | Admission decision |
| Consolidation | Compare candidates with existing memory | Revised memory graph |
| Retrieval | Select scoped, useful memories | Context manifest |
| Behavior | Apply memories as evidence, not commands | Response or action |
| Feedback | Measure usefulness and correctness | New evidence |

## Generalized Primitive

A **memory loop** owns five typed contracts: interaction event, memory candidate, memory record, retrieval decision, and feedback event. Each transition must preserve provenance and explain why state changed.

## Separation From Existing Memory

- `AH-002` task notes preserve current work and repository lessons.
- This pattern models a user and the agent's learned behavior across tasks.
- Raw conversations remain evidence; they are not automatically long-term memory.

## Portability Limits

- Personalization policies depend on user consent, product domain, and data sensitivity.
- A memory useful in one task scope can be harmful when generalized globally.
- External memory changes behavior through context; it does not update model parameters.

## Plugin Implication

- `memory capture|extract|evaluate|consolidate|retrieve|feedback`
- Require a user scope, provenance chain, policy decision, and audit reason at every stage.
- Expose external-memory behavior before supporting training-data export or fine-tuning.

## Evidence And Confidence

- **Observed:** `AH-002` demonstrates temporary state, durable learning, and evidence-based promotion in a repository harness.
- **Proposed:** The user-provided brief extends that loop to confidence-weighted, personalized memory.
- **Confidence:** High for architectural feasibility; unvalidated for measured personalization gains.

## Open Questions

- Which outcomes prove that a retrieved memory improved behavior rather than merely changing it?
