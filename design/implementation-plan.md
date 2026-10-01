# Implementation Plan

## Principle

Build only what the next experiment needs. Add complexity as a new controlled condition, not as an unmeasured default.

## Progress

- Phase 0 completed on 2026-09-23.
- Phase 1 completed on 2026-09-23.
- Phase 2 completed on 2026-09-24.
- Phase 3 is active; the development dataset is complete.
- The model-neutral MCP contract was drafted on 2026-09-30; retrieval, proposal, commit, and discard tools are implemented.

## Phase 0: Experiment Contracts

Deliver:

- scenario schema;
- evidence, memory, revision, and retrieval schemas;
- run manifest;
- baseline construction manifests;
- labeling guide;
- metric definitions;
- clustered analysis and multiplicity rules;
- deterministic safety fixtures.

Exit gate:

- one scenario can be validated and replayed without calling a model;
- all artifact versions are recorded;
- forbidden and expected memory IDs are explicit.
- every condition can reconstruct its exact context without future queries or labels.

## Phase 1: Memory Core

Deliver:

- SQLite schema and migrations;
- approval, correction, supersession, and deletion operations;
- scope and lifecycle policy;
- retrieval traces;
- unit and contract tests.

Exit gate:

- explicit preferences survive restart;
- revision history is complete;
- forbidden records never reach ranking;
- narrower rules displace broader rules before ranking;
- equal-scope conflicts return no record;
- deletion erases user-authored content, eligibility, and lexical index entries while retaining only tombstone metadata.

## Phase 2: Baseline Runner

Deliver:

- no-memory condition;
- recent-history condition;
- rolling-summary condition;
- structured lexical-memory condition;
- fixed-budget context assembly;
- raw output and configuration capture.

Exit gate:

- all conditions run from the same scenario;
- only the memory strategy differs;
- failed runs remain visible and attributable.

## Phase 3: Pilot

Deliver:

- development dataset — complete: 24 synthetic scenarios across six template families;
- blinded human review workflow;
- paired analysis with uncertainty intervals;
- failure report by pipeline stage;
- protocol revisions made before held-out evaluation.

Exit gate:

- labels are usable and disagreements are measured;
- metrics distinguish retrieval from generation failures;
- no post-hoc success threshold is introduced.

## Client Integration Track: MCP

This track exposes the existing memory lifecycle to coding assistants. It is an
integration surface, not a new experimental condition or a model adapter.

Deliver:

- local stdio MCP server;
- retrieve, propose, commit, discard, and inspect tools;
- ephemeral proposal storage with expiry;
- local memory-profile scope supplied outside model-controlled content;
- equivalent JSON CLI operations;
- contract and integration tests that do not call a model.

Exit gate:

- multiple MCP-capable hosts can use the same memory database and tool contract;
- no proposal becomes durable before an explicit approval event;
- rejected and expired proposals leave no durable evidence or index entries;
- tool output never exposes out-of-scope records or raw internal errors;
- the existing lifecycle and retrieval tests still pass.

## Phase 4: Held-Out Study

Freeze the protocol, dataset split, prompts, conditions, and analysis before running the held-out set. Publish all required reproducibility artifacts and limitations.

## Deferred

- autonomous extraction or promotion;
- inferred facts and sensitive attributes;
- confidence-weighted consolidation;
- vector and hybrid retrieval;
- network daemon and remote service hosting;
- host-specific enforcement wrappers;
- real-user data;
- fine-tuning;
- production deployment.
