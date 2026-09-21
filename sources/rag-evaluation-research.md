# Source Ledger: RAG Evaluation Research

## Snapshot

- Reviewed: 2026-09-21.
- Subject: Retrieval, RAG, and long-term memory evaluation methods.
- Evidence class: Primary research papers.

## Verified Sources

| Source | Verified contribution | Used in |
|---|---|---|
| [RAGAS](https://arxiv.org/abs/2309.15217) (`arXiv:2309.15217v2`) | Separates retrieval relevance, response faithfulness, and response quality; proposes reference-free automated metrics | Stage separation and limits on model-assisted diagnostics |
| [BEIR](https://arxiv.org/abs/2104.08663) (`arXiv:2104.08663v4`) | Compares retrieval approaches across heterogeneous datasets using standard ranking metrics | Retrieval metrics and later retriever comparisons |
| [LongMemEval](https://arxiv.org/abs/2410.10813) (`arXiv:2410.10813v2`) | Includes multi-session reasoning, temporal reasoning, knowledge updates, and abstention | Longitudinal scenario design |

## Interpretation Limits

- RAGAS is an evaluation framework, not proof that a system is correct or safe.
- BEIR evaluates general information retrieval, not personalized memory policy or deletion semantics.
- LongMemEval supplies a useful benchmark taxonomy, but product-specific preferences, privacy boundaries, and tool behavior still require local cases.
- None of these papers establishes a universal success threshold for Memory Loom.

## Use In This Repository

- [`../research/protocol.md`](../research/protocol.md) separates retrieval from generation outcomes.
- The dataset includes temporal updates, abstention, and hard negatives.
- Human labels remain primary; model judges require calibration.
- Vector and hybrid retrieval are deferred comparisons, not assumed improvements.

## Next Evidence Step

Verify additional personalized-memory benchmarks from primary papers, then justify each added dataset slice or metric explicitly.
