# Project Status

## Goal

Test whether explicit, user-approved external memory improves coding-assistant behavior across sessions without unacceptable relevance, privacy, or control failures.

## Current State

- Phase 0 experiment contracts and deterministic replay tooling are implemented.
- Pydantic v2 models validate scenarios, manifests, run artifacts, memory records, revisions, and retrieval traces and generate eight versioned JSON Schemas.
- A 24-scenario synthetic development set covers six independent template families with four surface variants each.
- All 24 pilot scenarios validate, use unique UUIDs, and reproduce their labeled B3 retrieval selections without calling a model.
- The SQLite memory core implements approval, correction, supersession, deletion, restart persistence, and retrieval traces.
- Live retrieval applies scope, lifecycle, specificity, and conflict filters before candidate-only FTS5 ranking.
- The synchronous baseline runner executes B0-B3 through one adapter and records exact prompts, contexts, configuration, latency, raw outputs, and failures.
- A deterministic no-model adapter exercises the complete pipeline; no provider-backed runs or experimental results exist.
- The MCP 2.x stdio server implements host-scoped retrieval and ephemeral create, correction, and deletion proposals.
- Commit, discard, and inspection MCP tools are specified but not yet implemented.
- Source-backed harness patterns are cataloged in `notes/00` through `notes/08`.
- Research questions, hypotheses, claims, and protocol are now separated from implementation design.
- The first system under test is limited to explicit preferences and direct corrections.
- Earlier admission and memory-revision material is retained only as later-phase design material.

## Decisions

- Treat Memory Loom as a research project, not a generic agent-platform specification.
- Keep source observations, hypotheses, and engineering choices in separate documents.
- Use no-memory, recent-history, rolling-summary, and structured-memory baselines.
- Start with manual approval and deterministic retrieval.
- Defer inferred traits, autonomous consolidation, vector retrieval, and fine-tuning.
- Do not set numerical quality targets before a pilot establishes baseline distributions.
- Build every baseline from the same frozen scenario timeline and context-budget contract.
- Resolve scope specificity and conflicts before lexical ranking.
- Treat provenance metadata as append-only while keeping user-authored content erasable.
- Resample independent scenario-construction clusters rather than queries or repeated model runs.
- Use local stdio MCP as the primary client integration boundary, with a JSON CLI fallback for hosts without MCP.
- Keep provider adapters confined to the experiment runner; Memory Loom itself does not depend on a model provider.

## Next Implementation Milestone

Implement the model-neutral MCP boundary without changing the tested memory lifecycle.

Exit conditions:

- expose the five frozen v1 tools over local stdio MCP;
- keep proposed changes ephemeral until explicit user approval;
- preserve scope, lifecycle, deletion, and retrieval-trace invariants;
- provide equivalent JSON CLI operations for non-MCP hosts;
- add contract and integration tests without calling a model.

The Phase 3 scientific pilot follows this integration milestone. It still needs
a provider-backed experiment adapter and an exercised blinded review workflow.

## Blockers

- The MCP lifecycle is incomplete: commit, discard, inspection, and host configuration documentation remain.
- No provider-backed experiment runner exists.
- The blinded review workflow has not been exercised.
- Most literature pointers in the original brief still require primary-source verification.

## History

- 2026-09-14: Extracted coding-agent harness patterns and drafted a personalized-memory concept.
- 2026-09-21: Added local-first architecture, privacy, de-identification, and RAG evaluation material.
- 2026-09-21: Reorganized the repository around an explicit scientific claim and removed duplicate speculative architecture.
- 2026-09-21: Resolved review gaps in baseline reproducibility, scope precedence, deletion semantics, and clustered analysis.
- 2026-09-23: Implemented Phase 0 schemas, validation, deterministic B0-B3 replay, one safety fixture, and focused tests.
- 2026-09-23: Implemented Phase 1 SQLite lifecycle operations, prefiltered FTS5 retrieval, persisted traces, and live B3 replay.
- 2026-09-24: Implemented Phase 2 synchronous B0-B3 execution, deterministic no-model replay, versioned run artifacts, and failure-preserving output capture.
- 2026-09-30: Completed 24 synthetic Phase 3 development scenarios across six independent template families and validated their contracts and live B3 selections.
- 2026-09-30: Chose a model-neutral stdio MCP boundary and drafted five lifecycle-preserving tool contracts.
