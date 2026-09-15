---
id: AH-007
title: LLM decision guardrails
status: initial
maturity: observed
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# LLM Decision Guardrails

## Use When

- An LLM participates in routing, classification, applicability, or another control decision.

## Core Pattern

Use deterministic checks first, constrain the LLM to the residual ambiguity, and fail closed.

## Observed Implementation

- Infrastructure and exact-match filters run before semantic relevance evaluation.
- The LLM receives compact excerpts, not full logs.
- Error-like lines and a bounded tail are selected as the failure signal.
- Untrusted stage names and logs are explicitly labeled as data, not instructions.
- The response is validated against a Pydantic schema.
- Batched candidates receive stable pair IDs.
- Missing verdicts default to `false`.
- Refusal, timeout, malformed response, and upstream errors become a domain error and no-match policy.
- The system prompt says to be conservative and return true only for a clear relation.

## Decision Pipeline

```text
cheap deterministic gates
  -> deterministic content matching
  -> compact ambiguous candidates
  -> structured LLM verdict
  -> completeness validation
  -> conservative fallback
```

## Why It Matters

- Reduces cost and latency.
- Shrinks prompt-injection surface.
- Makes failures observable and testable.
- Keeps probabilistic behavior from silently widening execution scope.
- Preserves a human-readable reason for audit and debugging.

## Generalized Primitive

An **LLM policy step** should declare:

- input reduction strategy;
- untrusted-data boundaries;
- response schema;
- completeness rule;
- error and refusal policy;
- default decision;
- batch size and token budget;
- audit fields.

## Plugin Implication

- Provide a reusable structured-classification adapter.
- Require explicit fallback policy before activation.
- Generate tests for missing IDs, duplicates, malformed payloads, refusal, timeout, and partial responses.
- Capture prompt version and model metadata alongside the verdict when available.

## Evidence

- `pipeline-fl-control-plane@df513fa4:fl_control_plane/handler_orchestrator/relevance_evaluator.py` — batching, prompt boundaries, schema, and fail-closed behavior.
- `pipeline-fl-control-plane@df513fa4:tests/handler_orchestrator/test_relevance_evaluator.py` — positive, negative, missing, batched, and failure cases.
- `pipeline-fl-control-plane@df513fa4:docs/design/applicability-model.md` — deterministic-before-LLM orchestration policy.

## Open Questions

- Which decision classes are too consequential for a no-match fallback and instead require human review?
