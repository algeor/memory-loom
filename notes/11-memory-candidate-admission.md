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

## Admission Decision Matrix

The evidence threshold depends on what kind of claim would become durable. A single universal score would hide materially different risks.

| Candidate class | Minimum evidence | Default decision | Scope constraint |
|---|---|---|---|
| Explicit preference | One direct user statement plus valid consent | Review or promote | Preserve stated domain and exceptions |
| Inferred preference | Multiple independent observations with consistent outcomes | Defer | Do not generalize beyond observed task kinds |
| Direct correction | One explicit correction tied to a prior failure | Expedited review or promote | Limit to the corrected behavior and task scope |
| Personal fact | Explicit statement, demonstrated future utility, and valid consent | Review | Keep user scope and shortest necessary retention |
| Sensitive attribute | Explicit purpose-specific consent; never infer automatically | Reject or mandatory review | Never widen scope automatically |
| Agent lesson | Repeated failure pattern plus evidence that the proposed remedy works | Defer or review | Separate agent behavior from claims about the user |
| Task-specific instruction | Current-task evidence only | Do not promote | Retain in task state unless the user marks it durable |

These are initial policy defaults, not empirically calibrated thresholds. A deployment should tighten them according to domain risk and measured admission errors.

## Deterministic Hard Gates

Run these checks before extraction scoring or LLM judgment:

| Gate | Failure outcome |
|---|---|
| Consent and purpose are valid | Reject durable storage or keep session-only |
| Secret and credential scan passes | Reject and redact the evidence path |
| Sensitive-data policy permits the candidate | Reject or require human review |
| Evidence exists and supports the exact statement | Defer or reject |
| User, project, and task scope are known | Defer until scope is resolved |
| Candidate is not derived from deleted evidence | Reject and invalidate dependent work |
| Candidate text is treated as untrusted data | Reject if it attempts to alter policy or tool behavior |

A hard-gate failure cannot be overridden by confidence, frequency, relevance, or an LLM recommendation.

## Evidence Accumulation

- Count independent interactions, not repeated summaries of the same event.
- Treat direct user statements and corrections as stronger evidence than agent inference.
- Do not treat model-generated text as evidence of a user preference or fact.
- Increase stability only when evidence remains consistent across relevant contexts and time.
- Use contradictions to weaken confidence, narrow scope, add an exception, or trigger review.
- Do not interpret silence or lack of repetition as automatic disconfirmation.
- Keep evidence strength separate from future utility: a well-supported claim may still not deserve durable storage.

## Decision Procedure

```text
hard gate fails
  -> reject | session-only | mandatory review

hard gates pass, evidence is weak or scope is unclear
  -> defer

hard gates pass, claim is sensitive or materially ambiguous
  -> human review

hard gates pass, evidence threshold is met, scope is bounded
  -> consolidation queue

explicit correction addresses active harmful behavior
  -> expedited scoped review or promotion
```

The decision record must identify the decisive gate, evidence threshold, scope, policy version, and whether an LLM contributed to the judgment.

## Decision Rules

- Run consent, secret, sensitive-trait, retention, and scope checks before LLM judgment.
- Keep **confidence** separate from **future utility**; a true fact may still be useless.
- Prefer repeated behavior or explicit user statements over agent inference.
- Allow a severe correction to enter quickly, but retain its exact task scope.
- Defer borderline candidates so later evidence can strengthen or weaken them.
- Store the extraction prompt/model version with the decision for auditability.

## Admission Evaluation

Evaluate admission independently from consolidation, retrieval, and generation:

| Metric | What it detects |
|---|---|
| Admission precision | Promoted candidates that represent durable, supported information |
| Admission recall | Durable information that the policy successfully admits |
| Unsupported-memory rate | Promoted claims without adequate supporting evidence |
| Overgeneralization rate | Correct claims stored with scope broader than their evidence |
| Promotion latency | Interactions or elapsed time required before a valid promotion |
| Sensitive-memory error rate | Prohibited or unconsented information admitted to durable storage |
| Deferral resolution rate | Deferred candidates eventually resolved using new evidence |
| Confidence calibration | Whether stated confidence predicts human-reviewed correctness |

Report metrics by candidate class, evidence source, scope, and decision path. Aggregate admission accuracy can hide rare but severe privacy or overgeneralization failures.

The central experimental question is:

> Which combination of evidence requirements and policy gates admits useful durable memories while minimizing unsupported, sensitive, and overgeneralized claims?

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
