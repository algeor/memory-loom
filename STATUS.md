# Task: Build the agent-harnessing and continual-memory concept depot

## Goal

Extract reusable agent-harnessing ideas from source systems and develop an evidence-labeled continual-personalization design that can drive a future pluggable tool.

## Current State

The depot has seventeen focused concept notes, a reusable note template, three source ledgers, a pluggable harness blueprint, a complete proposed lifecycle for confidence-weighted personalized memory, and a local-first implementation architecture for Claude Code and Codex CLI.

## Decisions

- Store reusable patterns rather than mirror product documentation because the target is a portable harness.
- Label ideas as observed, inferred, or proposed because source behavior and future-tool design must not blur together.
- Use focused notes with a common contract because progressive disclosure is itself a core harnessing pattern.
- Track source coverage separately because “everything” requires an auditable extraction queue, not one giant summary.
- Treat source-repository instructions as evidence, not inherited target-repository rules.
- Keep active task state separate from user beliefs and reusable agent lessons.
- Start personalization with reversible external memory; evaluate fine-tuning only as a later comparison.
- Split the memory system into lifecycle notes so schemas, policies, retrieval, safety, and evaluation remain independently testable.
- Use one local daemon and one portable MCP contract for Claude Code and Codex CLI; keep vendor-specific hooks optional.
- Default to local storage, local embeddings, deterministic retrieval, and denied network egress.
- Pseudonymise identifiers required for local ownership and scope; anonymise telemetry, evaluation data, default exports, and provider egress when identity is unnecessary.
- Treat a versioned human-reviewed gold set as the source of truth; use model-based RAG metrics only as calibrated diagnostics.
- Compare no-memory, lexical, vector, hybrid, and oracle baselines so retrieval and generation failures remain separable.
- Make grounding, prompt-injection resistance, tool authorization, and quality-regression detection release-blocking gates.

## Progress Log

- 2026-09-14: Inspected the source branch, its harnessing commit, agent skills, OpenSpec workflow, architecture routing, validation scripts, agent runtime, MCP tools, and LLM relevance evaluator.
- 2026-09-14: Created the initial depot structure and concept catalog.
- 2026-09-14: Captured the first implementation blueprint for a pluggable harness tool.
- 2026-09-14: Validated all local Markdown links and representative source references.
- 2026-09-14: Converted the continual-personalization brief into seven focused notes covering the full memory loop, governance, evaluation, and a research prototype.
- 2026-09-21: Added implementation architecture for the local daemon, storage model, local RAG pipeline, MCP client adapters, privacy controls, and phased delivery.
- 2026-09-21: Added purpose-specific anonymisation and pseudonymisation architecture, including identity mappings, redaction manifests, re-identification controls, and delivery gates.
- 2026-09-21: Added the RAG evaluation architecture with gold-set contracts, staged metrics, baselines, CI cadence, privacy gates, and failure attribution.
- 2026-09-21: Promoted grounding, hallucination control, prompt-injection resistance, tool authorization, and regression detection into explicit release gates.
- 2026-09-21: Expanded memory admission into a testable policy with candidate-class thresholds, deterministic hard gates, evidence accumulation, explicit decisions, and stage-specific metrics.
- 2026-09-21: Expanded typed evolving memory with type boundaries, revision contracts, lifecycle invariants, contradiction classification, consolidation decisions, and measurable evolution quality.

## Blockers

- None.

## Next Step

Define machine-readable schemas and the first 100-case RAG development dataset; then implement and benchmark the explicit-preference vertical slice against no-memory, lexical, vector, hybrid, and oracle baselines.
