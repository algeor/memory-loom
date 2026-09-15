---
id: AH-013
title: Adaptive memory retrieval
status: proposed
maturity: proposed
source_artifact: user-provided continual-personalization brief
source_date: 2026-09-14
---

# Adaptive Memory Retrieval

## Use When

- A large memory store must improve the current interaction without flooding context or applying irrelevant preferences.

## Core Pattern

Retrieve broadly, filter by policy and scope, rerank by expected utility, and inject a small context manifest with reasons.

## Problem It Solves

- Dumping all memories into context increases cost, distraction, and cross-scope mistakes.
- Similarity-only retrieval ignores confidence, validity, contradictions, and prior usefulness.

## Source Implementation Status

- The brief proposes ranking signals and a retrieve-filter-rerank-select flow.
- Existing depot notes provide observed bounded-context and guarded-decision patterns, but no memory retriever.

## Retrieval Pipeline

```text
current request
  -> candidate search
  -> access and status filters
  -> scope and contradiction filters
  -> utility reranking
  -> diversity and token-budget selection
  -> context manifest
  -> model behavior
  -> usefulness feedback
```

## Ranking Signals

- Semantic and lexical relevance.
- Confidence and evidence strength.
- Recency and last confirmation.
- Importance and predicted future utility.
- User, domain, and task similarity.
- Prior retrieval usefulness or harmfulness.
- Contradiction, dispute, and supersession penalties.

No single signal should dominate by default. Relevance without confidence retrieves noise; confidence without scope applies true information in the wrong context.

## Retrieval Decision Contract

```yaml
request_id: string
memory_id: string
eligible: boolean
score_components: {}
decision: selected|filtered|budget_cut
reason: string
position: integer|null
token_cost: integer
```

## Context Contract

- Label memories as historical evidence, preferences, or procedures—not system instructions.
- Include scope, confidence, and exceptions when they affect interpretation.
- Deduplicate overlapping memories and preserve type diversity.
- Set hard item and token limits.
- Record selected and high-scoring rejected items for diagnosis.

## Feedback Loop

After the response, capture whether each selected memory was relevant, followed, contradicted, ignored, or harmful. Feed that result into retrieval calibration and future consolidation; do not treat model self-assessment as sufficient evidence.

## Generalized Primitive

A **memory retriever** returns an explainable, budgeted context manifest plus a retrieval trace. It is specialized RAG over mutable beliefs and learned procedures.

## Portability Limits

- Embeddings alone are weak at permissions, temporal validity, and logical contradiction.
- Clicks or acceptance may not prove memory correctness.
- Retrieval quality and generation quality must be evaluated separately.

## Plugin Implication

- Hybrid retrieval adapter with configurable filters and rerankers.
- `memory retrieve --explain` for selected and rejected records.
- Feedback events tied to both response outcome and memory IDs.

## Evidence And Confidence

- **Observed:** `AH-001`, `AH-006`, and `AH-007` support minimum-context routing, bounded context, and guarded LLM decisions.
- **Proposed:** Memory-specific ranking and feedback signals come from the user-provided brief.
- **Confidence:** High for bounded explainable retrieval; medium for the optimal ranking function.

## Open Questions

- How should retrieval estimate usefulness before generation without reproducing the full generation cost?
