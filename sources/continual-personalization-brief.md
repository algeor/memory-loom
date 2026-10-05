# Source Ledger: Continual Personalization Brief

## Source

- Artifact: user-provided design and research brief
- Received: 2026-09-14
- Subject: external memory for user adaptation and repeated-error correction
- Evidence status: design input, not empirical evidence

The brief is not a published implementation, dataset, benchmark, or result. It can motivate hypotheses but cannot validate them.

## Retained For The Initial Study

| Input idea | Current location |
|---|---|
| External memory instead of continuous weight updates | [`research/README.md`](../research/README.md) |
| Explicit user preferences and direct corrections | [`design/memory-model.md`](../design/memory-model.md) |
| Longitudinal comparison with simpler baselines | [`research/protocol.md`](../research/protocol.md) |
| Stage-level failure attribution | [`research/protocol.md`](../research/protocol.md) |
| Inspectable provenance and revision history | [`design/memory-model.md`](../design/memory-model.md) |

## Deferred

The following ideas are plausible research directions but add unmeasured variables to the first study:

- inferred preferences and personal facts;
- episodic, semantic, procedural, and metacognitive hierarchies;
- confidence-weighted admission;
- periodic or event-triggered consolidation;
- autonomous contradiction resolution;
- vector or hybrid retrieval;
- memory-derived fine-tuning.

Admission hard gates, candidate-specific evidence thresholds, typed revision operations, contradiction classes, and their proposed evaluation metrics are preserved as deferred work in [`design/memory-model.md`](../design/memory-model.md).

## Rejected As Premature Defaults

- Python/FastAPI as a required service boundary;
- PostgreSQL and `pgvector` before a lexical baseline exists;
- a local daemon and MCP bridge before the experiment runner needs them;
- arbitrary confidence weights, retrieval limits, latency targets, or quality thresholds;
- production privacy or compliance claims from a documentation-only design.

These may become justified engineering choices later, but the brief itself does not supply that evidence.

## Literature Resolution

The brief named Generative Agents, Reflexion, MemGPT, MemoryBank, LoCoMo, LongMemEval, LOCCO, Reflective Memory Management, PREMem, PRIME, *Hello Again!*, Persona-Plug, and *Learning to Remember User Conversations*.

The retrieval-evaluation sources are recorded in
[`rag-evaluation-research.md`](rag-evaluation-research.md). The remaining named
works are verified and bounded in
[`personalized-memory-research.md`](personalized-memory-research.md).

## Next Evidence Step

Use these sources only for clearly attributed design comparisons. Add empirical
claims to the claim register only when they affect a specific protocol decision.
