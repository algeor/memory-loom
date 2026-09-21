# Memory Model

## Status

Design decision for the initial experiment. Field names may change during implementation.

## Records

### Evidence Event

An immutable reference to the interaction in which the user stated a preference or correction.

```yaml
id: uuid
scenario_id: string
kind: explicit_preference|direct_correction
text: string
user_scope: string
project_scope: string|null
task_scope: string|null
recorded_at: timestamp
consent: approved|declined
```

### Memory Record

The user-approved statement available for retrieval.

```yaml
id: uuid
statement: string
kind: preference|correction
user_scope: string
project_scope: string|null
task_scope: string|null
status: active|superseded|deleted
evidence_ids: [uuid]
created_at: timestamp
valid_from: timestamp
valid_until: timestamp|null
version: integer
```

### Revision Event

Every change appends an immutable transition.

```yaml
id: uuid
memory_id: uuid
operation: approve|correct|supersede|delete
from_version: integer|null
to_version: integer|null
evidence_ids: [uuid]
actor: user|research_fixture
rationale: string
created_at: timestamp
```

### Retrieval Decision

The trace needed to evaluate retrieval independently from generation.

```yaml
query_id: uuid
memory_id: uuid
eligible: boolean
decision: selected|scope_filtered|state_filtered|budget_filtered
lexical_score: number|null
reason: string
position: integer|null
```

## State Rules

- New evidence is not durable until explicitly approved.
- Correction creates a new version; it does not mutate history in place.
- A newer explicit preference may supersede an older one in the same scope.
- A narrower exception coexists with a broader preference and wins only in its scope.
- Deletion makes the record immediately ineligible and removes it from indexes.
- Experiment fixtures may simulate approval but must record that actor explicitly.

## Scope Resolution

Apply the most specific eligible record:

1. user + project + task;
2. user + project;
3. user only.

If equally specific active records conflict, return neither and flag the case for review. The initial system does not invent a resolution.

## Deferred Admission Research

Later studies may evaluate inferred preferences, facts, procedures, or agent lessons. Those candidates need different evidence thresholds rather than one universal score:

- explicit statements may require one attributable event;
- inferred preferences require repeated independent observations;
- sensitive attributes must not be inferred automatically;
- agent lessons must remain separate from claims about the user;
- task-only instructions remain task state unless the user marks them durable.

Deterministic consent, secret, sensitivity, evidence, and scope gates must precede any model judgment. A failed hard gate cannot be overridden by frequency or an LLM score.

## Deferred Revision Research

Later consolidation may support reinforce, refine, split, merge, weaken, dispute, and expire operations. Apparent contradictions should first be classified as temporal change, scope difference, exception, source disagreement, extraction error, or unresolved conflict.

That extension requires a separate labeled evaluation of transition accuracy, scope preservation, provenance completeness, and deletion propagation. It is not part of the first experiment.
