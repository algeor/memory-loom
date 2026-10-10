# Reference Design

## Status

This is a **design decision** with a partial reference implementation. The experiment contracts, SQLite lifecycle core, hybrid retrieval path, synchronous baseline runner, and all five v1 MCP tools exist. Automated Codex and Claude Code onboarding is implemented; the JSON CLI fallback remains incomplete. The system has not produced experimental results.

Its purpose is to create the smallest system capable of running the initial experiment in [`../research/protocol.md`](../research/protocol.md).

## Design Goal

Store an explicit preference or direct correction, retrieve it in the correct scope, show why it was retrieved, and remove it completely enough for the experimental deletion checks.

## Minimal System

```text
coding CLI -> local MCP boundary -> memory API
experiment runner -------------> memory API
                                  -> policy checks
                                  -> SQLite records and revisions
                                  -> hybrid retrieval
                                  -> bounded context manifest
```

The core remains one process or library. Local stdio MCP is the chosen client-neutral boundary. A network daemon, remote model calls inside Memory Loom, and background consolidation remain unnecessary.

## Components

| Component | Responsibility |
|---|---|
| Memory API | Approve, retrieve, correct, supersede, and delete records |
| Policy module | Enforce consent, scope, state, and operation rules |
| Store | Persist evidence, records, revisions, and retrieval traces |
| Hybrid retriever | Return eligible records using deterministic lexical and local-vector search |
| Context builder | Produce a bounded, labeled context manifest |
| MCP boundary | Expose retrieval and user-controlled lifecycle operations to compatible hosts |
| Experiment adapter | Run identical scenarios across experimental conditions |
| Host integration | Invoke MCP tools or equivalent JSON CLI operations without changing the memory core |

## Invariants

- Only explicit preferences and direct corrections are durable in the first study.
- A user approves each durable record.
- Every record links to source evidence and revision history; provenance metadata is append-only while user-authored content remains erasable.
- Scope, lifecycle, specificity, and conflict filters run before ranking.
- Deleted, superseded, and out-of-scope records are ineligible.
- Memory is labeled as fallible context, never as system instruction.
- The current request overrides conflicting memory.
- Every experiment run records its complete configuration.
- The local memory-profile scope is supplied by the host and must not be broadened by model-generated arguments.

## Documents

- [`memory-model.md`](memory-model.md) — records, states, and revisions.
- [`import-architecture.md`](import-architecture.md) — approval-gated memory admission diagrams.
- [`retrieval.md`](retrieval.md) — hybrid retrieval and context construction.
- [`retrieval-architecture.md`](retrieval-architecture.md) — scoped retrieval, reranking, and provenance diagrams.
- [`safety.md`](safety.md) — consent, scope, deletion, and threat boundaries.
- [`implementation-plan.md`](implementation-plan.md) — build order and exit gates.
- [`codex-mcp.md`](codex-mcp.md) — Codex installation, registration, and verification.
- [`claude-code-mcp.md`](claude-code-mcp.md) — Claude Code installation, registration, and verification.
- [`database-upgrades.md`](database-upgrades.md) — SQLite backup, migration, and early-user upgrade rules.
- [`project-guidance.md`](project-guidance.md) — project-scoped conventions using the existing approval lifecycle.
- [`provider-runner.md`](provider-runner.md) — provider invocation, isolation, usage, and failure recording.
- [`../contracts/v1/mcp-tools.md`](../contracts/v1/mcp-tools.md) — proposed client-neutral tool boundary.
- [`../contracts/v1/json-stdio.md`](../contracts/v1/json-stdio.md) — persistent JSON-lines fallback for non-MCP hosts.

## Deferred Decisions

These require evidence from the first study or a separate experiment:

- provider-backed embeddings or model-backed reranking;
- inferred preferences or personal facts;
- confidence scoring;
- autonomous admission and consolidation;
- network daemon and remote service hosting;
- host-specific enforcement and non-MCP wrappers;
- Gemini CLI onboarding and verification;
- anonymisation of research exports;
- encryption and long-term backup retention policy;
- fine-tuning.
