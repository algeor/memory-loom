---
id: AH-015
title: Personalized-memory evaluation
status: proposed
maturity: proposed
source_artifact: user-provided continual-personalization brief
source_date: 2026-09-14
---

# Personalized-Memory Evaluation

## Use When

- A memory system must demonstrate improved adaptation and repeated-error correction rather than merely show that it stores text.

## Core Pattern

Evaluate the full memory lifecycle longitudinally against simpler baselines, while attributing failures to the stage that caused them.

## Problem It Solves

- A storage demo does not prove personalization, learning, or reduced repeated errors.
- End-to-end scores hide whether extraction, consolidation, retrieval, or generation failed.

## Source Implementation Status

- The brief proposes the hypothesis, baselines, longitudinal sessions, preference changes, and fine-tuning comparison.
- It provides no benchmark implementation or experimental results.

## Research Question

Can an agent autonomously decide which experiences become durable knowledge, revise those memories under contradictory evidence, and retrieve information that measurably improves future interactions with the same user?

## Hypothesis

Confidence-weighted, typed, periodically revised memory improves long-term personalization and repeated-error correction while injecting less irrelevant context than static conversation retrieval.

## Baselines

1. LLM without memory.
2. Raw conversation retrieval.
3. Rolling or periodic summaries.
4. Structured memories without consolidation.
5. Full candidate admission, consolidation, contradiction handling, and adaptive retrieval.

Keep the model, prompts, tasks, and token budgets controlled where possible so the memory mechanism is the primary independent variable.

## Evaluation Scenario

- Run simulated users for 50–100 sessions.
- Reveal preferences gradually and test them later without reminders.
- Include contextual exceptions, deliberate preference changes, and direct corrections.
- Repeat task families to measure whether an error recurs after correction.
- Evaluate after fixed horizons such as 10, 50, and 100 interactions.

## Metrics

| Layer | Measures |
|---|---|
| Admission | precision, recall, unsupported-memory rate, promotion latency |
| Consolidation | contradiction resolution, calibration, stale-memory rate, oscillation |
| Retrieval | recall@k, precision@k, useful-context rate, irrelevant tokens |
| Behavior | personalization accuracy, repeated-error rate, task success, user preference adherence |
| Efficiency | memory growth, retrieval latency, context tokens, model cost |
| Safety | cross-user leakage, sensitive-memory rate, deletion completeness |

Report results by memory type and task scope. A single aggregate score can hide harmful failures.

## Attribution

Separate failures into extraction, admission, consolidation, retrieval, generation, or evaluation. A correct memory that was not retrieved is a different defect from a retrieved memory the model ignored.

## Fine-Tuning Study

Treat weight updates as phase two. Compare external memory only, fine-tuning only, and memory plus fine-tuning. Export training data only from consented, stable, well-supported memories, and preserve a reversible external-memory baseline.

## Portability Limits

- Simulated preferences may be cleaner and more explicit than real user behavior.
- Judge-model scores need calibration against human assessment.
- Results depend on the base model, task distribution, retrieval budget, and interaction horizon.

## Related Research Pointers

- Generative Agents, Reflexion, MemGPT, MemoryBank, LoCoMo, LongMemEval, and LOCCO.
- Reflective Memory Management, PREMem, PRIME, *Hello Again!*, Persona-Plug, and *Learning to Remember User Conversations*.
- These are discovery pointers from the brief, not yet independently verified evidence in this depot.

## Generalized Primitive

A **memory evaluation harness** replays controlled longitudinal interactions, captures stage-level traces, and compares memory strategies using behavioral, efficiency, and safety metrics.

## Plugin Implication

- `experiment run|compare|report` with fixed models, prompts, datasets, seeds, and token budgets.
- Persist stage traces so every behavioral failure can be attributed and replayed.

## Evidence And Confidence

- **Observed:** `AH-008` provides risk-shaped validation and failure attribution patterns.
- **Proposed:** Research question, baselines, longitudinal simulation, and fine-tuning comparison come from the user-provided brief.
- **Confidence:** High that comparative longitudinal evaluation is necessary; effect size is unknown until tested.

## Open Questions

- Which simulated-user results reliably transfer to real long-term user relationships?
