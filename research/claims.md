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

There are currently **no confirmatory result claims**. The bounded development
result below must not be generalized beyond its frozen synthetic run.

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
| H1 | Structured memory improves later preference adherence. | Predeclared paired contrasts against all baselines with clustered uncertainty and multiplicity control |
| H2 | Structured memory reduces recurrence after a direct correction. | Longitudinal correction scenarios with adjudicated outcomes |
| H3 | Structured memory reduces irrelevant context at a fixed budget. | Context relevance labels and token counts |
| H4 | Lifecycle filters prevent forbidden retrieval in the evaluated test corpus. | Zero out-of-scope, superseded, and deleted hits in adversarial fixtures |

All four remain unconfirmed. H1 and H4 were exercised in the synthetic
development pilot, but that model-reviewed run was not confirmatory.

## Exploratory Result

| ID | Claim | Status | Evidence |
|---|---|---|---|
| R1 | In the frozen 24-scenario, 192-output Claude development pilot, the B3-B0 preference-adherence estimate was 0.2188 with simultaneous 95% interval [-0.0625, 0.5000]; the B3-B1 and B3-B2 intervals also included zero. The pilot therefore did not distinguish structured memory from any baseline. | Result | [`development-pilot-claude-001`](../evaluation-runs/development-pilot-claude-001/REPORT.md) |
| R2 | The same frozen run recorded zero forbidden context inclusions and zero no-memory false-positive retrievals, but its synthetic coverage does not establish safety outside that corpus. | Result | [`development-pilot-claude-001`](../evaluation-runs/development-pilot-claude-001/analysis.json) |

## Design Decisions

| ID | Decision | Why it is not a result |
|---|---|---|
| D1 | Begin with explicit, user-approved preferences only. | Scope choice intended to reduce ambiguity and risk |
| D2 | Use an external local store rather than model-weight updates. | Makes inspection, correction, and deletion testable |
| D3 | Start with deterministic lexical retrieval. | Provides an interpretable baseline before adding vectors |
| D4 | Keep append-only provenance metadata and revision events while storing user-authored content in erasable fields. | Supports replay and testable deletion; effectiveness remains to be measured |
| D5 | Integrate through replaceable adapters. | Prevents one client implementation from defining the research claim |

## Prohibited Claims

Until supported by confirmatory results, do not claim that Memory Loom:

- learns a user autonomously;
- improves coding quality generally;
- prevents hallucinations;
- is private, secure, anonymous, or compliant in production;
- outperforms vector databases, fine-tuning, or commercial memory products;
- transfers from synthetic evaluation to real users.

## Update Rule

A hypothesis becomes a result only when the repository contains the versioned dataset, configuration, raw run artifacts, analysis, and limitations needed to reproduce it.
