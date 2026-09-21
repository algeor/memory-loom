# Claim Register

This file is the authority for what the repository may claim.

## Status Vocabulary

| Status | Meaning |
|---|---|
| Observed | Directly present in a cited source |
| Inferred | A reasoned abstraction from observations |
| Hypothesis | A falsifiable prediction with no result yet |
| Design decision | A replaceable engineering choice |
| Result | Supported by a completed, reproducible experiment |

There are currently **no result claims**.

## Source Observations

| ID | Claim | Status | Evidence |
|---|---|---|---|
| O1 | A repository can route agents from a small root instruction file to focused guidance. | Observed | [`AH-001`](../notes/01-progressive-instruction-routing.md) |
| O2 | Task notes can separate resumable state from promoted reusable guidance. | Observed | [`AH-002`](../notes/02-durable-task-memory.md) |
| O3 | Deterministic checks can precede constrained LLM classification with conservative fallback. | Observed | [`AH-007`](../notes/07-llm-decision-guardrails.md) |
| O4 | Validation can be selected by risk and failures attributed to distinct stages. | Inferred | [`AH-008`](../notes/08-review-and-validation.md) |
| O5 | Retrieval evaluation commonly separates ranking quality from answer quality. | Observed in literature | [`rag-evaluation-research`](../sources/rag-evaluation-research.md) |
| O6 | Long-term memory evaluation requires temporal updates and abstention cases. | Observed in literature | [`rag-evaluation-research`](../sources/rag-evaluation-research.md) |

## Research Hypotheses

| ID | Claim | Required evidence |
|---|---|---|
| H1 | Structured memory improves later preference adherence. | Paired comparison against all preregistered baselines |
| H2 | Structured memory reduces recurrence after a direct correction. | Longitudinal correction scenarios with adjudicated outcomes |
| H3 | Structured memory reduces irrelevant context at a fixed budget. | Context relevance labels and token counts |
| H4 | Lifecycle filters prevent forbidden retrieval. | Zero out-of-scope, superseded, and deleted hits in adversarial fixtures |

All four remain untested.

## Design Decisions

| ID | Decision | Why it is not a result |
|---|---|---|
| D1 | Begin with explicit, user-approved preferences only. | Scope choice intended to reduce ambiguity and risk |
| D2 | Use an external local store rather than model-weight updates. | Makes inspection, correction, and deletion testable |
| D3 | Start with deterministic lexical retrieval. | Provides an interpretable baseline before adding vectors |
| D4 | Store immutable evidence and revision events. | Supports replay and audit; effectiveness remains to be measured |
| D5 | Integrate through replaceable adapters. | Prevents one client implementation from defining the research claim |

## Prohibited Claims

Until supported by results, do not claim that Memory Loom:

- learns a user autonomously;
- improves coding quality generally;
- prevents hallucinations;
- is private, secure, anonymous, or compliant in production;
- outperforms vector databases, fine-tuning, or commercial memory products;
- transfers from synthetic evaluation to real users.

## Update Rule

A hypothesis becomes a result only when the repository contains the versioned dataset, configuration, raw run artifacts, analysis, and limitations needed to reproduce it.
