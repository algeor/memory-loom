# Delivery Plan

## Decision Status

- **Proposed:** Build an explicit-preference vertical slice before autonomous learning.
- **Confidence:** High that this proves the architecture with the lowest privacy risk.

## Phase 0: Contracts

Deliver:

- versioned JSON Schemas or Pydantic models;
- storage migrations;
- policy configuration schema;
- purpose-specific de-identification contract and redaction-manifest schema;
- MCP tool schemas;
- deterministic privacy fixtures for identifiers, secrets, third-party data, and encoded variants.
- a versioned development dataset and held-out RAG evaluation contract.

Exit gate:

- malformed, unauthorized, or over-budget inputs fail closed;
- schemas cover events, candidates, memories, revisions, retrieval, feedback, and egress.
- storage, embedding, export, telemetry, and egress paths cannot bypass de-identification.
- no-memory, lexical, vector, hybrid, and oracle baselines run from the same fixture set.

## Phase 1: Explicit Preferences

Deliver:

- local daemon and admin CLI;
- SQLite, FTS5, and local embeddings;
- deterministic identifier and secret detection with purpose-specific transformations;
- `memory_remember`, `memory_context`, `memory_explain`, and `memory_forget`;
- manual approval before candidate promotion;
- Claude Code and Codex CLI MCP setup guides.

Exit gate:

- a user can save, retrieve, inspect, correct, and delete one communication preference;
- no Memory Loom process opens an outbound connection in `local_only` mode;
- every retrieved item has provenance and a selection reason.
- raw identifiers do not appear in memory text, indexes, embeddings, logs, default exports, or egress payloads.
- retrieval, no-answer, privacy, and context-budget release gates pass.
- grounding, prompt-injection, and unauthorized-tool tests pass with zero critical failures.

## Phase 2: Scoped Project Memory

Deliver:

- project and task-kind scopes;
- hybrid reranking and diversity controls;
- contradiction and supersession flows;
- retrieval feedback;
- encrypted backup and export.

Exit gate:

- project memories never cross scope in adversarial tests;
- stale and contradicted records are excluded or clearly qualified;
- retrieval improves a fixed evaluation set over no-memory and lexical-only baselines.
- paired regression results show no degradation on critical slices versus the last accepted release.

## Phase 3: Assisted Consolidation

Deliver:

- scheduled candidate consolidation;
- dry-run revisions with human-readable diffs;
- optional local model adapter;
- optional remote provider adapter behind egress approval.

Exit gate:

- consolidation never mutates memory without a versioned proposal;
- local and remote modes produce auditable egress and revision traces;
- deletion invalidates derived memories and queued work.

## Deferred

- Automatic transcript ingestion.
- Autonomous promotion of inferred personal facts.
- Multi-user or hosted service operation.
- Continuous model fine-tuning.
- Remote embeddings or reranking as defaults.
- Vendor-specific features required for core correctness.

## Initial Repository Shape

```text
src/memory_loom/
  domain/        typed records and transitions
  policy/        capture, retrieval, egress, deletion
  privacy/       detection, pseudonymisation, anonymisation, manifests
  storage/       SQLite repositories and migrations
  retrieval/     FTS, vectors, reranking, manifests
  embeddings/    local model adapter
  mcp/           portable MCP tools
  cli/           local administration
  daemon/        socket server and background jobs
adapters/
  claude-code/   setup, optional plugin, optional hooks
  codex/         setup, optional plugin and skills
tests/
  contract/
  integration/
  privacy/
  evaluation/     gold datasets, timeline fixtures, rubrics, and regression tests
```

## First Implementation Decision

Start with one Python package and one SQLite database. Keep interfaces between policy, storage, retrieval, embeddings, and MCP explicit, but do not split them into network services.

## Evidence Basis

- [Spec-driven change lifecycle](../notes/03-spec-driven-change-lifecycle.md)
- [Review, validation, and failure attribution](../notes/08-review-and-validation.md)
- [Personalized-memory prototype](../notes/16-personalized-memory-prototype.md)
- [Anonymisation and pseudonymisation](07-de-identification.md)
- [RAG evaluation and testing](08-rag-evaluation-and-testing.md)
