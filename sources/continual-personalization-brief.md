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

## Literature Queue

The brief named Generative Agents, Reflexion, MemGPT, MemoryBank, LoCoMo, LongMemEval, LOCCO, Reflective Memory Management, PREMem, PRIME, *Hello Again!*, Persona-Plug, and *Learning to Remember User Conversations*.

Only sources recorded in [`rag-evaluation-research.md`](rag-evaluation-research.md) are treated as checked. All other names remain an unverified search queue.

## Next Evidence Step

Verify the most relevant memory benchmarks and personalized-dialogue studies from primary papers. Add only claims that can be tied to a precise source and to a decision in the research protocol.
