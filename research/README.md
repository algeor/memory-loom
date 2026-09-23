# Research Overview

## Object Of Study

Memory Loom studies an **external, inspectable memory layer for coding assistants**. The memory layer is separate from model weights and supplies selected records as context for a later interaction.

The first study is intentionally limited to explicit preferences and direct corrections. Broader claims about inferred facts, autonomous learning, or general intelligence are outside scope.

## Primary Research Question

Does structured, user-approved memory improve preference adherence on later coding-assistant tasks compared with no memory, recent conversation history, or a rolling summary under the same context budget?

## Secondary Questions

1. Does memory reduce recurrence of a corrected assistant behavior?
2. Does structured retrieval use fewer irrelevant context tokens than history-based baselines?
3. Can scope, correction, and deletion rules prevent stale or forbidden memories from influencing output?
4. Which failures originate in capture, storage, retrieval, context assembly, or generation?

## Hypotheses

| ID | Hypothesis | Status |
|---|---|---|
| H1 | Structured memory increases preference adherence on memory-dependent tasks. | Untested |
| H2 | Structured memory reduces repeated corrected behavior. | Untested |
| H3 | Structured memory supplies less irrelevant context than recent-history and summary baselines under the same maximum budget. | Untested |
| H4 | Deterministic scope and lifecycle filters prevent retrieval of out-of-scope, superseded, or deleted records in the test corpus. | Untested |

H4 is a safety invariant and should be reported as a failure count, not averaged into a utility score.

## Unit Of Analysis

The primary unit is a **memory-dependent query within a longitudinal scenario**. A scenario contains earlier evidence, later queries, and optional corrections, exceptions, or deletion events.

## System Boundary

```text
prior interaction
  -> explicit candidate
  -> user approval
  -> scoped memory record
  -> deterministic retrieval
  -> bounded context
  -> assistant response
  -> outcome record
```

Only the memory layer varies between experimental conditions. The model, system prompt, task, context budget, and decoding settings remain fixed where the provider permits.

## Study Boundary

The initial study does not test:

- inferred or sensitive personal attributes;
- autonomous promotion or consolidation;
- semantic vector retrieval;
- fine-tuning;
- production-scale latency or reliability;
- legal compliance;
- transfer from simulated users to real long-term use.

## Research Artifacts

- [`claims.md`](claims.md) — every material claim and its evidence state.
- [`protocol.md`](protocol.md) — baselines, dataset, metrics, analysis, and reproducibility requirements.
- [`../design/README.md`](../design/README.md) — the minimal system proposed for the experiment.

## Interpretation Rule

A successful prototype proves only that the system can be built. A positive controlled experiment is required before claiming behavioral benefit. Real-user benefit requires a later study with consented participants.
