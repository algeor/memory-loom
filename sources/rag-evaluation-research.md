# Source Ledger: RAG Evaluation Research

## Snapshot

- Reviewed: 2026-09-21.
- Subject: Retrieval, RAG, and long-term memory evaluation methods.
- Evidence class: Primary research papers plus proposed product-specific test gates.

## Verified Sources

| Source | Verified contribution | Used in |
|---|---|---|
| `RAGAS` (`arXiv:2309.15217v2`) | Separates retrieval relevance, response faithfulness, and response quality; proposes reference-free automated metrics | RAG stage separation and optional model-assisted diagnostics |
| `BEIR` (`arXiv:2104.08663v4`) | Evaluates lexical, sparse, dense, late-interaction, and reranking approaches across heterogeneous retrieval datasets | Retrieval baselines and standard ranking metrics |
| `LongMemEval` (`arXiv:2410.10813v2`) | Evaluates extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention over long interaction histories | Memory-specific gold-set slices and longitudinal replay |

## Interpretation Limits

- RAGAS is an evaluation framework, not proof that a system is correct or safe.
- BEIR evaluates general information retrieval, not personalized memory policy or deletion semantics.
- LongMemEval supplies a useful benchmark taxonomy, but product-specific preferences, privacy boundaries, and tool behavior still require local cases.
- Numeric release thresholds in the implementation architecture are proposed starting points, not values established by these papers.

## Resulting Architecture Decisions

- Maintain a human-reviewed, product-specific gold set.
- Evaluate retrieval and generation separately.
- Include lexical, vector, hybrid, no-memory, and oracle baselines.
- Add temporal update, abstention, scope isolation, deletion, and prompt-injection cases.
- Use model-based judges only after calibration against human labels.
- Gate releases on grounded claims, prompt-injection resistance, independent tool authorization, and paired regression results.

## Next Evidence Step

Implement the first 100-case development set, measure inter-reviewer disagreement, and calibrate release thresholds from observed baseline distributions.
