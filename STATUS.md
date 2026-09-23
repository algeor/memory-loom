# Project Status

## Goal

Test whether explicit, user-approved external memory improves coding-assistant behavior across sessions without unacceptable relevance, privacy, or control failures.

## Current State

- Phase 0 experiment contracts and deterministic replay tooling are implemented.
- Pydantic v2 models validate scenarios, manifests, memory records, revisions, and retrieval traces and generate seven versioned JSON Schemas.
- One synthetic development scenario reconstructs B0-B3 contexts without calling a model.
- The SQLite memory core and live lexical retrieval are not implemented.
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

## Next Milestone

Implement the SQLite memory core and replace frozen retrieval decisions with live deterministic lexical retrieval.

Exit conditions:

- migrations create the record, revision, trace, and FTS tables;
- approval, correction, supersession, and deletion survive restart;
- scope, lifecycle, specificity, and conflict filters run before lexical ranking;
- deleted or out-of-scope records never reach FTS ranking or context output;
- the existing fixture's retrieval decisions can be regenerated from stored records and its query.

## Blockers

- Only one development fixture exists; no benchmark dataset has been created.
- No persistent memory core exists.
- Most literature pointers in the original brief still require primary-source verification.

## History

- 2026-09-14: Extracted coding-agent harness patterns and drafted a personalized-memory concept.
- 2026-09-21: Added local-first architecture, privacy, de-identification, and RAG evaluation material.
- 2026-09-21: Reorganized the repository around an explicit scientific claim and removed duplicate speculative architecture.
- 2026-09-21: Resolved review gaps in baseline reproducibility, scope precedence, deletion semantics, and clustered analysis.
- 2026-09-23: Implemented Phase 0 schemas, validation, deterministic B0-B3 replay, one safety fixture, and focused tests.
