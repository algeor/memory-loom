# Reference Design

## Status

This is a **design decision**, not an implemented or validated system.

Its purpose is to create the smallest system capable of running the initial experiment in [`../research/protocol.md`](../research/protocol.md).

## Design Goal

Store an explicit preference or direct correction, retrieve it in the correct scope, show why it was retrieved, and remove it completely enough for the experimental deletion checks.

## Minimal System

```text
experiment runner or client adapter
  -> memory API
     -> policy checks
     -> SQLite records and revisions
     -> lexical retrieval
     -> bounded context manifest
  -> assistant model
  -> outcome and trace
```

The first implementation should be one process or library. A daemon, MCP server, vector index, remote model calls, and background consolidation are unnecessary for the first experiment.

## Components

| Component | Responsibility |
|---|---|
| Memory API | Approve, retrieve, correct, supersede, and delete records |
| Policy module | Enforce consent, scope, state, and operation rules |
| Store | Persist evidence, records, revisions, and retrieval traces |
| Lexical retriever | Return eligible records using deterministic text search |
| Context builder | Produce a bounded, labeled context manifest |
| Experiment adapter | Run identical scenarios across experimental conditions |
| Client adapter | Optional integration with a coding assistant |

## Invariants

- Only explicit preferences and direct corrections are durable in the first study.
- A user approves each durable record.
- Every record links to source evidence and revision history; provenance metadata is append-only while user-authored content remains erasable.
- Scope, lifecycle, specificity, and conflict filters run before ranking.
- Deleted, superseded, and out-of-scope records are ineligible.
- Memory is labeled as fallible context, never as system instruction.
- The current request overrides conflicting memory.
- Every experiment run records its complete configuration.

## Documents

- [`memory-model.md`](memory-model.md) — records, states, and revisions.
- [`retrieval.md`](retrieval.md) — lexical retrieval and context construction.
- [`safety.md`](safety.md) — consent, scope, deletion, and threat boundaries.
- [`implementation-plan.md`](implementation-plan.md) — build order and exit gates.

## Deferred Decisions

These require evidence from the first study or a separate experiment:

- vector or hybrid retrieval;
- inferred preferences or personal facts;
- confidence scoring;
- autonomous admission and consolidation;
- local daemon and MCP packaging;
- anonymisation of research exports;
- encryption and backup strategy;
- fine-tuning.
