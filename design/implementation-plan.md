# Implementation Plan

## Principle

Build only what the next experiment needs. Add complexity as a new controlled condition, not as an unmeasured default.

## Phase 0: Experiment Contracts

Deliver:

- scenario schema;
- evidence, memory, revision, and retrieval schemas;
- run manifest;
- labeling guide;
- metric definitions;
- deterministic safety fixtures.

Exit gate:

- one scenario can be validated and replayed without calling a model;
- all artifact versions are recorded;
- forbidden and expected memory IDs are explicit.

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
- deletion removes eligibility and lexical index entries.

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

- development dataset;
- blinded human review workflow;
- paired analysis with uncertainty intervals;
- failure report by pipeline stage;
- protocol revisions made before held-out evaluation.

Exit gate:

- labels are usable and disagreements are measured;
- metrics distinguish retrieval from generation failures;
- no post-hoc success threshold is introduced.

## Phase 4: Held-Out Study

Freeze the protocol, dataset split, prompts, conditions, and analysis before running the held-out set. Publish all required reproducibility artifacts and limitations.

## Deferred

- autonomous extraction or promotion;
- inferred facts and sensitive attributes;
- confidence-weighted consolidation;
- vector and hybrid retrieval;
- daemon and MCP packaging;
- real-user data;
- fine-tuning;
- production deployment.
