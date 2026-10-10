# Project Status

## Goal

Test whether explicit, user-approved external memory improves coding-assistant behavior across sessions without unacceptable relevance, privacy, or control failures.

## Current State

- Phase 0 experiment contracts and deterministic replay tooling are implemented.
- Pydantic v2 models validate scenarios, manifests, run artifacts, blinded-review artifacts, pilot analyses, retrieval evaluations, memory records, revisions, and retrieval traces and generate 13 versioned JSON Schemas.
- A 24-scenario synthetic development set covers six independent template families with four surface variants each.
- All 24 pilot scenarios validate, use unique UUIDs, and reproduce their labeled B3 retrieval selections without calling a model.
- The SQLite memory core implements approval, correction, supersession, deletion, restart persistence, and retrieval traces.
- Live retrieval applies scope, lifecycle, specificity, and conflict filters before candidate-only FTS5 ranking and pluggable reranking.
- The deterministic retrieval evaluator reports ranking, abstention, safety, and context-cost metrics from frozen labels without calling a model.
- The resumable parallel runner executes B0-B3 through OpenAI Responses API, isolated Claude CLI, or deterministic no-model adapters and records prompts, contexts, usage, cost, latency, raw outputs, and failures.
- A frozen Claude development pilot completed 192 runs across 24 scenarios, with condition-blind model review and paired cluster-bootstrap analysis.
- All pilot contrast intervals included zero; the run did not distinguish structured memory from any baseline and is not confirmatory evidence.
- The MCP 2.x stdio server implements host-scoped retrieval, ephemeral create/correct/delete proposals, and approval-gated durable commits.
- All five v1 MCP tools are implemented over local stdio, including read-only scoped inspection with tombstone-safe output.
- A persistent JSON-lines fallback exposes the same host-scoped lifecycle for clients without MCP.
- Codex host registration and verification are documented, and the five-tool lifecycle has passed a local stdio smoke test.
- Automated onboarding registers Codex or Claude Code, installs a managed project instruction block, and verifies host configuration.
- Claude Code local registration is documented and has passed its MCP connection check.
- SQLite upgrades now create a pre-migration backup, apply changes transactionally, and reject unsupported newer schemas.
- Local diagnostics, manual backup, and guarded restore commands are implemented without printing memory content.
- CI and tagged-release workflows test contracts, retrieval gates, built distributions, clean onboarding, MCP restart persistence, and v1 database upgrades.
- Source-backed harness patterns are cataloged in `notes/00` through `notes/08`.
- Research questions, hypotheses, claims, and protocol are now separated from implementation design.
- The first system under test is limited to explicit preferences and direct corrections.
- Earlier admission and memory-revision material is retained only as later-phase design material.
- Every literature item named in the original personalization brief is resolved to a primary paper or proceedings record with an explicit relevance boundary.

## Decisions

- Treat Memory Loom as a research project, not a generic agent-platform specification.
- Keep source observations, hypotheses, and engineering choices in separate documents.
- Use no-memory, recent-history, rolling-summary, and structured-memory baselines.
- Start with manual approval and deterministic retrieval.
- Defer inferred traits, autonomous consolidation, vector retrieval, and fine-tuning.
- Do not set numerical quality targets before a pilot establishes baseline distributions.
- Build every baseline from the same frozen scenario timeline and context-budget contract.
- Resolve scope specificity and conflicts before lexical ranking and reranking.
- Treat provenance metadata as append-only while keeping user-authored content erasable.
- Resample independent scenario-construction clusters rather than queries or repeated model runs.
- Use local stdio MCP as the primary client integration boundary, with a JSON CLI fallback for hosts without MCP.
- Keep provider adapters confined to the experiment runner; Memory Loom itself does not depend on a model provider.
- Defer Gemini CLI onboarding until a later client-integration stage.
- Distribute the first tester build as a versioned GitHub release artifact rather than claiming production readiness.
- Treat internal-language and API conventions as concise, explicit project-scoped preferences, not bulk document ingestion or model training.

## Next Scientific Milestone

Calibrate the blinded rubric with independent human review, then freeze a
held-out confirmatory study before viewing its outputs.

Exit conditions:

- obtain at least two independent condition-blind human reviews;
- measure reviewer agreement and adjudicate disagreements;
- use a dated provider model snapshot with enforceable decoding controls;
- freeze the held-out dataset, decision rules, and exact code revision;
- publish conclusions only after the preregistered analysis completes.

## Scientific Limits

- The completed pilot uses synthetic development scenarios, not held-out data or real users.
- Review is model-only and is not calibrated against blinded human judgments.
- One reviewer cannot estimate reviewer disagreement.
- Claude CLI did not expose temperature, top-p, seed, or output-token controls.
- The generation manifest records a working-tree revision rather than an exact commit.

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
- 2026-10-01: Implemented MCP retrieval, ephemeral proposals, and approval-gated create, correction, and deletion commits with host-event provenance.
- 2026-10-01: Completed the v1 MCP tool surface with proposal discard and scoped, read-only inspection.
- 2026-10-01: Verified Codex registration and the full propose, commit, retrieve, and inspect lifecycle; documented reproducible host setup.
- 2026-10-01: Added automated Codex and Claude Code onboarding; deferred Gemini CLI integration.
- 2026-10-01: Hardened early-user database upgrades with backups, transactional migrations, compatibility guards, and preservation tests.
- 2026-10-01: Added versioned lexical-retrieval evaluation with CI thresholds and forbidden-hit failure behavior.
- 2026-10-01: Added early-tester diagnostics, backup/restore, clean-wheel smoke testing, CI, release automation, and tester guidance.
- 2026-10-01: Documented project-scoped guidance for internal languages and APIs without expanding the first-study memory model.
- 2026-10-05: Added the lifecycle-equivalent persistent JSON stdio fallback for non-MCP hosts.
- 2026-10-05: Added OpenAI Responses API and isolated Claude CLI provider adapters plus resumable parallel study execution.
- 2026-10-05: Added condition-blind review packets, model and human review workflows, and paired cluster-bootstrap analysis.
- 2026-10-05: Completed the 192-output Claude development pilot; every B3 contrast interval included zero, so no baseline difference was established.
- 2026-10-05: Resolved every named personalization and memory paper in the original brief to a primary source record.
