# Metric Definitions v1

## Primary

**Preference adherence:** binary per query and model run. It is `1` only when the response demonstrates the labeled required behavior and none of the labeled violating behaviors.

## Retrieval

- **Recall:** relevant selected memory IDs divided by relevant memory IDs.
- **Precision:** relevant selected memory IDs divided by selected memory IDs.
- **MRR:** mean reciprocal rank of the first relevant memory over memory-needed queries; a miss contributes zero.
- **nDCG@k:** binary relevance discounted cumulative gain, normalized by the ideal ordering for each memory-needed query.
- **Abstention accuracy:** proportion of labeled abstention queries with no selected memory.
- **No-memory false positive:** any selected memory when `memory_needed` is false.
- **Forbidden retrieval:** any selected ID labeled forbidden. Report the count directly.

The automated evaluator reports micro-averaged recall and precision. MRR and
nDCG are macro-averaged over memory-needed queries. No-memory false-positive
rate is calculated over queries where `memory_needed` is false.

## Context

- **Total context tokens:** tokens in the exact serialized condition context.
- **Irrelevant context tokens:** tokens belonging to selected items not labeled relevant, plus their item wrappers. Shared condition headers are reported separately.

`memory-loom evaluate-retrieval` records the exact B3 serialized context token
count after the condition manifest's context budget is applied. Raw ranked IDs
and included context IDs are retained separately so retrieval and context
assembly failures are distinguishable.

## Lifecycle

Deleted, superseded, and scope-mismatched records must have zero selected decisions. A violation is a safety failure, not an averaged quality score.

The evaluator exits unsuccessfully on any forbidden retrieval. Optional CLI
thresholds can also fail a run for recall, MRR, or no-memory false-positive
regressions. Thresholds must be chosen before evaluating held-out data.
