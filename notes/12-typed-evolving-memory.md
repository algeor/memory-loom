---
id: AH-012
title: Typed evolving memory
status: proposed
maturity: proposed
source_artifact: user-provided continual-personalization brief
source_date: 2026-09-14
---

# Typed Evolving Memory

## Use When

- Long-term memory must distinguish events, beliefs, procedures, and higher-level lessons while remaining revisable.

## Core Pattern

Model memory as versioned, confidence-weighted claims supported by evidence—not immutable facts or free-form summaries.

## Problem It Solves

- Untyped summaries blur events, user beliefs, reusable procedures, and agent self-corrections.
- Immutable records cannot represent changing preferences, exceptions, or conflicting evidence.

## Source Implementation Status

- The brief proposes the memory hierarchy, confidence fields, and contradiction behavior.
- No implemented consolidator or calibrated confidence model is supplied.

## Memory Types

| Type | Meaning | Example |
|---|---|---|
| Episodic | What happened in a specific interaction | User corrected answer X on date Y |
| Semantic | A generalized belief or preference | User generally prefers concise responses |
| Procedural | A reusable behavior | For this task type, verify X first |
| Metacognitive | A recurring reasoning lesson | Assumption Y repeatedly causes overestimation |

## Memory Record

```yaml
id: string
type: episodic|semantic|procedural|metacognitive
statement: string
scope: {user: string, domain: string|null, task_kind: string|null}
confidence: 0..1
importance: 0..1
evidence_refs: []
contradiction_refs: []
status: active|disputed|superseded|expired|deleted
created_at: timestamp
last_confirmed_at: timestamp|null
valid_from: timestamp|null
valid_until: timestamp|null
supersedes: []
version: integer
```

## Consolidation

Run periodically, after enough candidates, after a significant failure, or when contradiction is detected.

Allowed operations:

- **Create** a new memory from sufficient evidence.
- **Reinforce** an existing memory and update confidence.
- **Refine** its scope or add an exception.
- **Split** an overgeneralized belief into contextual variants.
- **Merge** duplicates while retaining provenance.
- **Weaken** confidence after contradictory evidence.
- **Supersede** an outdated belief without erasing history.
- **Expire or delete** according to retention and user policy.

## Contradiction Rule

Contradiction is evidence, not an automatic overwrite. Prefer a scoped refinement such as “concise by default; detailed for ML when requested” over oscillating between two global beliefs.

## Generalized Primitive

A **memory consolidator** compares new candidates with active and historical records, proposes explicit state transitions, and preserves the evidence graph behind each revision.

## Portability Limits

- Confidence values are operational estimates, not calibrated probabilities unless tested as such.
- Semantic and metacognitive memories are model-generated abstractions and need stronger evidence than episodic records.
- Consolidation quality depends on access to contradictory and superseded evidence.

## Plugin Implication

- `memory show --history`, `memory dispute`, `memory supersede`, and `memory consolidate --dry-run`.
- Version every mutation and expose a human-readable diff plus rationale.
- Keep episodic evidence available long enough to audit derived memories.

## Evidence And Confidence

- **Observed:** `AH-002` separates temporary task state from promoted durable learning.
- **Proposed:** The four-type hierarchy, mutable record, and consolidation operations formalize the user-provided brief.
- **Confidence:** High for typed/versioned storage; medium for autonomous consolidation accuracy.

## Open Questions

- How much source evidence must remain after a derived memory is superseded or deleted?
