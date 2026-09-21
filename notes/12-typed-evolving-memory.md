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

## Type Boundaries

Each record has one primary type. Records may reference one another, but combining event, belief, procedure, and reasoning lesson into one summary makes evidence and revision ambiguous.

| Type | Required basis | What it must not become automatically | Default evolution |
|---|---|---|---|
| Episodic | One attributable event with time and scope | A general user trait or global rule | Remain immutable evidence; redact, expire, or delete by policy |
| Semantic | Direct durable statement or synthesis of sufficient episodic evidence | A procedure merely because it influenced one successful answer | Reinforce, narrow, dispute, or supersede |
| Procedural | A scoped action pattern with evidence of successful outcomes | A claim that the user always wants that behavior | Refine preconditions, split by task, weaken, or supersede |
| Metacognitive | Repeated reasoning failures or successes with an evidenced causal pattern | A psychological claim about the user | Refine the trigger and remedy; review before broadening |

Examples of invalid automatic promotion:

- One request for a detailed explanation does not establish a semantic preference for detailed responses.
- One successful tool sequence does not establish a reusable procedure.
- One incorrect assumption does not establish a metacognitive failure pattern.
- An agent-generated interpretation does not convert an episodic event into a user fact.

## Memory Record

```yaml
id: string
version_id: string
type: episodic|semantic|procedural|metacognitive
statement: string
subject: user|agent|task|domain
scope: {user: string, project: string|null, domain: string|null, task_kind: string|null}
confidence: 0..1
confidence_components: {evidence_quality: 0..1, independence: 0..1, consistency: 0..1, scope_fit: 0..1, recency: 0..1}
importance: 0..1
evidence_refs: []
derived_from: []
contradiction_refs: []
status: active|disputed|superseded|expired|deleted
created_at: timestamp
recorded_at: timestamp
last_confirmed_at: timestamp|null
valid_from: timestamp|null
valid_until: timestamp|null
supersedes_version_id: string|null
version: integer
```

`id` identifies the logical memory across revisions. `version_id` identifies one immutable version. `valid_from` and `valid_until` describe when the claim applies; `recorded_at` describes when the system learned or revised it.

Confidence is an operational decision signal, not automatically a probability that the statement is true. Persist its components so the system can distinguish weak evidence from contradiction, poor scope fit, or staleness.

## Revision Contract

Every mutation creates a new version and an immutable revision event:

```yaml
memory_id: string
from_version_id: string|null
to_version_ids: []
operation: create|reinforce|refine|split|merge|weaken|dispute|supersede|expire|delete
trigger_refs: []
field_changes: {}
rationale: string
actor: user|policy|human_reviewer|model
policy_version: string
model_version: string|null
created_at: timestamp
```

For `split` and `merge`, `to_version_ids` may contain multiple resulting records or point to a new logical memory. The revision must preserve the source relationships rather than silently replacing history.

## Lifecycle Invariants

- Published versions are immutable; changes always create a new version.
- Every non-episodic memory links to the evidence and prior memories from which it was derived.
- An automatically revised scope may become narrower, but broadening requires new supporting evidence or human review.
- At most one current version of a logical memory is active in the same scope and validity interval.
- Disputed, superseded, expired, and deleted versions are excluded from normal retrieval.
- Deleting evidence triggers dependency analysis for every memory derived from it.
- Deletion removes protected content and derived indexes; an audit tombstone retains only policy-permitted metadata.
- `derived_from` and supersession relationships must remain acyclic.
- Confidence changes must identify which evidence or policy decision caused them.

## State Transitions

```text
promoted candidate
  -> active

active
  -> active new version | disputed | superseded | expired | deleted

disputed
  -> active new version | superseded | expired | deleted

superseded | expired | deleted
  -> never reactivated in place; create a new version or logical memory
```

Status and confidence represent different concerns. A high-confidence memory can be expired by retention policy, while a low-confidence memory can remain active but rank poorly or require qualification.

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

## Consolidation Decision Matrix

| New evidence relative to memory | Preferred operation |
|---|---|
| Supports the same claim in the same scope | Reinforce |
| Supports the claim only in a narrower context | Refine |
| Reveals distinct context-dependent variants | Split |
| Duplicates another record without adding meaning | Merge |
| Conflicts but neither side dominates | Dispute or weaken |
| Explicitly replaces an older preference or procedure | Supersede |
| Shows the memory is stale or outside its validity interval | Expire |
| Is removed through user deletion or policy | Recompute dependencies, then dispute, supersede, or delete |

Consolidation should produce a dry-run proposal when it changes statement meaning, broadens scope, merges provenance, or resolves a contradiction. Autonomous reinforcement of an unchanged, already-supported claim is lower risk than autonomous abstraction or scope expansion.

## Contradiction Rule

Contradiction is evidence, not an automatic overwrite. Prefer a scoped refinement such as “concise by default; detailed for ML when requested” over oscillating between two global beliefs.

Classify the apparent contradiction before choosing an operation:

- **Temporal change:** the newer statement replaces an older preference after a known time.
- **Scope difference:** both statements are valid for different projects, domains, or task kinds.
- **Exception:** a general rule remains valid but has an explicit exception.
- **Source disagreement:** evidence sources conflict and require review or qualification.
- **Extraction error:** one candidate is unsupported or misstates its source.
- **True unresolved conflict:** sufficient evidence supports incompatible claims in the same scope and validity interval.

Only temporal change normally implies supersession. Scope differences and exceptions should preserve both claims with explicit applicability. Unresolved conflicts should remain disputed rather than being hidden by averaging confidence scores.

## Memory Evolution Evaluation

Evaluate the memory model separately from downstream retrieval and generation:

| Metric | What it detects |
|---|---|
| Type classification accuracy | Confusion between event, belief, procedure, and reasoning lesson |
| Transition accuracy | Whether the chosen revision operation matches human review |
| Contradiction-resolution accuracy | Correct split, refinement, dispute, or supersession |
| Over-merge and over-split rates | Loss of distinctions or unnecessary fragmentation |
| Scope-preservation rate | Whether revisions retain valid project, domain, and task boundaries |
| Provenance completeness | Current memories with a traversable evidence and revision chain |
| Temporal-validity accuracy | Correct treatment of stale, future, and superseded claims |
| Confidence calibration | Whether confidence corresponds to human-reviewed support |
| Deletion-propagation completeness | Dependent records and indexes handled after evidence deletion |

Use replayable timelines containing repetition, exceptions, preference changes, ambiguous conflicts, and deletion events. Report results by memory type and operation because aggregate accuracy can hide unsafe semantic or metacognitive abstractions.

The central experimental question is:

> Can a typed, versioned memory model preserve provenance and context while revising beliefs more accurately than immutable summaries or overwrite-in-place storage?

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
