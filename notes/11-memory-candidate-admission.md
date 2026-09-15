---
id: AH-011
title: Memory candidate admission
status: proposed
maturity: proposed
source_artifact: user-provided continual-personalization brief
source_date: 2026-09-14
---

# Memory Candidate Admission

## Use When

- An interaction may contain information worth remembering, but immediate promotion would overfit noise or one-off requests.

## Core Pattern

Treat extracted memories as temporary proposals. Admit them only after policy checks and evidence-based evaluation.

## Problem It Solves

- One instruction can be situational rather than a lasting preference.
- Model-generated summaries can invent or overgeneralize claims.
- Raw retrieval accumulates irrelevant, contradictory, or sensitive material.

## Source Implementation Status

- The brief defines candidate examples and evaluation factors, not production admission code or calibrated thresholds.
- `AH-007` provides the closest observed implementation pattern: deterministic gates before a constrained LLM decision.

## Candidate Contract

```yaml
id: string
subject: user|agent|task|domain
type: preference|fact|lesson|skill
statement: string
scope: {user: string, domain: string|null, task_kind: string|null}
evidence_refs: []
scores:
  novelty: 0..1
  importance: 0..1
  confidence: 0..1
  stability: 0..1
  future_utility: 0..1
signals:
  frequency: integer
  contradiction_refs: []
decision: pending|reject|defer|promote|review
rationale: string
created_at: timestamp
```

## Admission Pipeline

```text
interaction
  -> deterministic policy gates
  -> structured extraction
  -> evidence verification
  -> novelty and contradiction lookup
  -> scored decision
  -> reject | defer | human review | consolidation queue
```

## Decision Rules

- Run consent, secret, sensitive-trait, retention, and scope checks before LLM judgment.
- Keep **confidence** separate from **future utility**; a true fact may still be useless.
- Prefer repeated behavior or explicit user statements over agent inference.
- Allow a severe correction to enter quickly, but retain its exact task scope.
- Defer borderline candidates so later evidence can strengthen or weaken them.
- Store the extraction prompt/model version with the decision for auditability.

## Generalized Primitive

A **memory admission policy** combines deterministic safety gates with a structured LLM evaluator. It emits a decision, rationale, and evidence links—not just a score.

## Portability Limits

- Weights and thresholds require calibration against the target domain.
- Frequency alone can reinforce repeated model errors.
- Sensitive personal attributes should not be inferred merely because they improve ranking.

## Plugin Implication

- Policy-defined candidate types and prohibited classes.
- Pluggable scoring features without a mandatory universal formula.
- Queue views for deferred, contradicted, and human-review candidates.
- Tests for malformed extraction, missing evidence, duplication, and unsafe content.

## Evidence And Confidence

- **Observed:** `AH-007` supports deterministic checks before constrained LLM classification and conservative fallback.
- **Proposed:** Candidate factors and schema come from the user-provided brief.
- **Confidence:** High for the admission pattern; medium for any uncalibrated scoring formula.

## Open Questions

- Which candidate classes can be promoted from one explicit statement, and which require repetition?
