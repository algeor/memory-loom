# Project Status

## Goal

Test whether explicit, user-approved external memory improves coding-assistant behavior across sessions without unacceptable relevance, privacy, or control failures.

## Current State

- Documentation only; no executable prototype exists.
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

## Next Milestone

Implement the experiment contracts and a lexical-retrieval vertical slice for explicit preferences.

Exit conditions:

- the dataset and run manifests validate against versioned schemas;
- every retrieved preference has scope and provenance;
- deleted or out-of-scope records are never returned;
- all four baseline conditions run from the same fixture;
- results report paired effects and uncertainty rather than a single aggregate score.

## Blockers

- No benchmark dataset has been created.
- No prototype has been implemented.
- Most literature pointers in the original brief still require primary-source verification.

## History

- 2026-09-14: Extracted coding-agent harness patterns and drafted a personalized-memory concept.
- 2026-09-21: Added local-first architecture, privacy, de-identification, and RAG evaluation material.
- 2026-09-21: Reorganized the repository around an explicit scientific claim and removed duplicate speculative architecture.
